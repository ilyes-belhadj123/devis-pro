import json
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query, Response

from app.core.database import database
from app.entretien_devis.apprentissage import enregistrer_correction
from app.entretien_validation.export import construire_csv_export, construire_json_export
from app.entretien_validation.models import (
    STATUT_ACCEPTE,
    STATUT_EN_ATTENTE,
    STATUT_ENVOYE,
    STATUT_VALIDE,
    AccepterInput,
    CreerDevisValidationInput,
    DevisValidation,
    DevisValidationResume,
    Formule,
    FormuleInput,
    LigneDevis,
    ModifierFormulesInput,
)
from app.entretien_validation.pdf import construire_pdf_devis

router = APIRouter(prefix="/entretien/validation", tags=["entretien-validation"])

STATUTS_EXPORTABLES = (STATUT_VALIDE, STATUT_ENVOYE, STATUT_ACCEPTE)


def _construire_formules(formules_input: list[FormuleInput]) -> list[dict]:
    formules: list[dict] = []
    for formule in formules_input:
        lignes = [
            {
                "designation": ligne.designation,
                "categorie": ligne.categorie,
                "unite": ligne.unite,
                "prix_unitaire": ligne.prix_unitaire,
                "quantite": ligne.quantite,
                "sous_total": round(ligne.prix_unitaire * ligne.quantite, 2),
            }
            for ligne in formule.lignes
        ]
        total = round(sum(ligne["sous_total"] for ligne in lignes), 2)
        formules.append(
            {"niveau": formule.niveau, "label": formule.label, "description": formule.description, "lignes": lignes, "total": total}
        )
    return formules


def _document_vers_devis(document: dict) -> DevisValidation:
    return DevisValidation(
        id=str(document["_id"]),
        compte_id=document["compte_id"],
        categorie=document["categorie"],
        statut=document["statut"],
        formules=[
            Formule(
                niveau=f["niveau"],
                label=f["label"],
                description=f["description"],
                lignes=[LigneDevis(**ligne) for ligne in f["lignes"]],
                total=f["total"],
            )
            for f in document["formules"]
        ],
        formule_choisie=document.get("formule_choisie"),
        cree_le=document["cree_le"],
        valide_le=document.get("valide_le"),
        envoye_le=document.get("envoye_le"),
        accepte_le=document.get("accepte_le"),
    )


def _identifiant(devis_id: str) -> ObjectId:
    try:
        return ObjectId(devis_id)
    except InvalidId as exc:
        raise HTTPException(status_code=400, detail="Identifiant de devis invalide") from exc


async def _recuperer_ou_404(devis_id: str) -> dict:
    document = await database.entretien_devis_valides.find_one({"_id": _identifiant(devis_id)})
    if document is None:
        raise HTTPException(status_code=404, detail="Devis introuvable")
    return document


@router.post("/devis", response_model=DevisValidation)
async def creer_devis_validation(payload: CreerDevisValidationInput) -> DevisValidation:
    formules = _construire_formules(payload.formules)
    document = {
        "compte_id": payload.compte_id,
        "categorie": payload.categorie,
        "statut": STATUT_EN_ATTENTE,
        "formules": formules,
        # instantane immuable de la suggestion initiale, pour detecter les corrections
        # de l'artisan a la validation (TICKET-601) - jamais expose tel quel via l'API.
        "formules_generees": _construire_formules(payload.formules),
        "formule_choisie": None,
        "cree_le": datetime.now(timezone.utc),
        "valide_le": None,
        "envoye_le": None,
        "accepte_le": None,
    }
    resultat = await database.entretien_devis_valides.insert_one(document)
    document["_id"] = resultat.inserted_id
    return _document_vers_devis(document)


@router.get("/devis", response_model=list[DevisValidationResume])
async def lister_devis_validation(compte_id: str = Query(default="demo")) -> list[DevisValidationResume]:
    documents = await database.entretien_devis_valides.find({"compte_id": compte_id}).sort("cree_le", -1).to_list()
    resumes = []
    for document in documents:
        formule_standard = next((f for f in document["formules"] if f["niveau"] == "standard"), None)
        total_standard = formule_standard["total"] if formule_standard else (document["formules"][0]["total"] if document["formules"] else 0.0)
        resumes.append(
            DevisValidationResume(
                id=str(document["_id"]),
                categorie=document["categorie"],
                statut=document["statut"],
                total_standard=total_standard,
                cree_le=document["cree_le"],
            )
        )
    return resumes


@router.get("/devis/{devis_id}", response_model=DevisValidation)
async def obtenir_devis_validation(devis_id: str) -> DevisValidation:
    return _document_vers_devis(await _recuperer_ou_404(devis_id))


@router.put("/devis/{devis_id}", response_model=DevisValidation)
async def modifier_devis_validation(devis_id: str, payload: ModifierFormulesInput) -> DevisValidation:
    document = await _recuperer_ou_404(devis_id)
    if document["statut"] != STATUT_EN_ATTENTE:
        raise HTTPException(status_code=409, detail="Ce devis ne peut plus être modifié (déjà validé ou envoyé)")

    formules = _construire_formules(payload.formules)
    await database.entretien_devis_valides.update_one({"_id": document["_id"]}, {"$set": {"formules": formules}})
    document["formules"] = formules
    return _document_vers_devis(document)


async def _enregistrer_corrections_artisan(document: dict) -> None:
    """Compare les formules validees a l'instantane genere initialement, et enregistre
    chaque ecart significatif de quantite/prix comme une correction a apprendre pour ce
    compte (TICKET-601). Une designation n'est comptee qu'une fois par champ, meme si
    elle apparait dans plusieurs formules."""
    lignes_generees_par_designation: dict[str, dict] = {}
    for formule in document.get("formules_generees", []):
        for ligne in formule["lignes"]:
            lignes_generees_par_designation.setdefault(ligne["designation"], ligne)

    deja_enregistre: set[tuple[str, str]] = set()
    for formule in document["formules"]:
        for ligne in formule["lignes"]:
            ligne_generee = lignes_generees_par_designation.get(ligne["designation"])
            if ligne_generee is None:
                continue
            for champ in ("quantite", "prix_unitaire"):
                cle = (ligne["designation"], champ)
                if cle in deja_enregistre:
                    continue
                deja_enregistre.add(cle)
                await enregistrer_correction(
                    document["compte_id"],
                    document["categorie"],
                    ligne["designation"],
                    champ,
                    ligne_generee[champ],
                    ligne[champ],
                )


@router.post("/devis/{devis_id}/valider", response_model=DevisValidation)
async def valider_devis(devis_id: str) -> DevisValidation:
    document = await _recuperer_ou_404(devis_id)
    if document["statut"] != STATUT_EN_ATTENTE:
        raise HTTPException(status_code=409, detail="Seul un devis en attente de validation peut être validé")

    await _enregistrer_corrections_artisan(document)

    valide_le = datetime.now(timezone.utc)
    await database.entretien_devis_valides.update_one(
        {"_id": document["_id"]}, {"$set": {"statut": STATUT_VALIDE, "valide_le": valide_le}}
    )
    document["statut"] = STATUT_VALIDE
    document["valide_le"] = valide_le
    return _document_vers_devis(document)


@router.post("/devis/{devis_id}/envoyer", response_model=DevisValidation)
async def envoyer_devis(devis_id: str) -> DevisValidation:
    document = await _recuperer_ou_404(devis_id)
    if document["statut"] != STATUT_VALIDE:
        raise HTTPException(
            status_code=409, detail="Le devis doit être validé par l'artisan avant de pouvoir être envoyé au client"
        )

    envoye_le = datetime.now(timezone.utc)
    await database.entretien_devis_valides.update_one(
        {"_id": document["_id"]}, {"$set": {"statut": STATUT_ENVOYE, "envoye_le": envoye_le}}
    )
    document["statut"] = STATUT_ENVOYE
    document["envoye_le"] = envoye_le
    return _document_vers_devis(document)


@router.get("/devis/{devis_id}/public", response_model=DevisValidation)
async def obtenir_devis_public(devis_id: str) -> DevisValidation:
    document = await _recuperer_ou_404(devis_id)
    if document["statut"] not in (STATUT_ENVOYE, STATUT_ACCEPTE):
        raise HTTPException(status_code=404, detail="Ce devis n'est pas (encore) disponible")
    return _document_vers_devis(document)


@router.post("/devis/{devis_id}/accepter", response_model=DevisValidation)
async def accepter_devis(devis_id: str, payload: AccepterInput) -> DevisValidation:
    document = await _recuperer_ou_404(devis_id)
    if document["statut"] != STATUT_ENVOYE:
        raise HTTPException(status_code=409, detail="Ce devis n'est plus en attente d'acceptation")
    if payload.niveau_choisi not in {f["niveau"] for f in document["formules"]}:
        raise HTTPException(status_code=400, detail="Formule choisie invalide")

    accepte_le = datetime.now(timezone.utc)
    await database.entretien_devis_valides.update_one(
        {"_id": document["_id"]},
        {"$set": {"statut": STATUT_ACCEPTE, "accepte_le": accepte_le, "formule_choisie": payload.niveau_choisi}},
    )
    document["statut"] = STATUT_ACCEPTE
    document["accepte_le"] = accepte_le
    document["formule_choisie"] = payload.niveau_choisi
    return _document_vers_devis(document)


def _formule_pour_export(document: dict, niveau: str | None) -> dict:
    if document["statut"] not in STATUTS_EXPORTABLES:
        raise HTTPException(status_code=409, detail="Seul un devis validé peut être exporté")

    niveau_cible = niveau or document.get("formule_choisie") or "standard"
    formule = next((f for f in document["formules"] if f["niveau"] == niveau_cible), None)
    if formule is None:
        formule = document["formules"][0] if document["formules"] else None
    if formule is None:
        raise HTTPException(status_code=404, detail="Aucune formule disponible pour ce devis")
    return formule


@router.get("/devis/{devis_id}/pdf")
async def exporter_pdf(devis_id: str, niveau: str | None = Query(default=None)) -> Response:
    document = await _recuperer_ou_404(devis_id)
    formule = _formule_pour_export(document, niveau)

    compte = await database.entretien_comptes.find_one({"_id": document["compte_id"]})
    compte_nom = compte["nom"] if compte else document["compte_id"]

    pdf_bytes = construire_pdf_devis(compte_nom, document["categorie"], formule)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=devis-entretien-{devis_id}.pdf"},
    )


@router.get("/devis/{devis_id}/export")
async def exporter_facturation(
    devis_id: str, niveau: str | None = Query(default=None), format: str = Query(default="csv")
) -> Response:
    document = await _recuperer_ou_404(devis_id)
    formule = _formule_pour_export(document, niveau)

    if format == "json":
        contenu = json.dumps(construire_json_export(devis_id, document["categorie"], formule), ensure_ascii=False, indent=2)
        return Response(
            content=contenu,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=devis-entretien-{devis_id}.json"},
        )

    if format == "csv":
        contenu = construire_csv_export(devis_id, document["categorie"], formule)
        return Response(
            content=contenu,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=devis-entretien-{devis_id}.csv"},
        )

    raise HTTPException(status_code=400, detail="Format d'export inconnu (csv ou json attendu)")
