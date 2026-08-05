from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Response

from app.core.database import database
from app.diagnostic.service import selectionner_materiel
from app.diagnostic.session_store import recuperer_session
from app.devis.models import (
    AlternativeInput,
    AlternativeResultat,
    DevisGenere,
    DevisPdfInput,
    DiagnosticInput,
    GroupeCategorie,
    HistoriqueDetail,
    HistoriqueResume,
    LigneDevis,
    RepartitionProbleme,
    StatistiquesDevis,
)
from app.devis.pdf import construire_pdf_devis
from app.devis.service import trouver_alternative_moins_chere

router = APIRouter(prefix="/devis", tags=["devis"])


@router.post("/generer", response_model=DevisGenere)
async def generer_devis(diagnostic: DiagnosticInput) -> DevisGenere:
    regle = await database.regles_association.find_one({"probleme": diagnostic.probleme})
    if regle is None:
        raise HTTPException(status_code=404, detail=f"Aucune règle d'association pour '{diagnostic.probleme}'")

    # le premier produit de la regle est le "produit principal", celui que le client
    # aurait achete seul sans SnapDevis - c'est la base du calcul panier moyen avant/apres,
    # et sert de repli quand il n'y a pas de conversation IA exploitable.
    produit_principal = await database.produits.find_one(
        {"reference": regle["references_produits"][0]}, {"_id": 0}
    )

    session = recuperer_session(diagnostic.session_id) if diagnostic.session_id else None

    materiel = None
    if session is not None and produit_principal is not None:
        # on donne a l'IA tout le catalogue de la categorie concernee (pas seulement la
        # petite liste fixe de la regle) pour qu'elle choisisse elle-meme le materiel
        # reellement necessaire a partir de la conversation (mesures, dimensions...).
        catalogue_categorie = await database.produits.find(
            {"categorie": produit_principal["categorie"]}, {"_id": 0}
        ).to_list()
        materiel = await selectionner_materiel(session, catalogue_categorie)

    if materiel is None:
        # repli : liste fixe de la regle d'association, quantite 1 (comportement historique,
        # utilise sans conversation IA - acces direct, tests, ou service IA indisponible).
        produits = await database.produits.find(
            {"reference": {"$in": regle["references_produits"]}}, {"_id": 0}
        ).to_list()
        produits_par_reference = {produit["reference"]: produit for produit in produits}
        materiel = [
            {**produits_par_reference[reference], "quantite": 1}
            for reference in regle["references_produits"]
            if reference in produits_par_reference
        ]

    lignes = [
        LigneDevis(
            reference=produit["reference"],
            nom=produit["nom"],
            categorie=produit["categorie"],
            unite=produit["unite"],
            prix_unitaire=produit["prix"],
            quantite=produit["quantite"],
            sous_total=round(produit["prix"] * produit["quantite"], 2),
        )
        for produit in materiel
    ]

    groupes_par_categorie: dict[str, float] = {}
    for ligne in lignes:
        groupes_par_categorie[ligne.categorie] = groupes_par_categorie.get(ligne.categorie, 0) + ligne.sous_total

    groupes = [
        GroupeCategorie(categorie=categorie, sous_total=round(sous_total, 2))
        for categorie, sous_total in groupes_par_categorie.items()
    ]

    total = round(sum(ligne.sous_total for ligne in lignes), 2)

    if lignes and produit_principal is not None:
        await database.historique_devis.insert_one(
            {
                "probleme": diagnostic.probleme,
                "produit_principal_prix": produit_principal["prix"],
                "total_complet": total,
                "lignes": [ligne.model_dump() for ligne in lignes],
                "date": datetime.now(timezone.utc),
            }
        )

    return DevisGenere(probleme=diagnostic.probleme, lignes=lignes, groupes=groupes, total=total)


@router.post("/pdf")
async def exporter_pdf(payload: DevisPdfInput) -> Response:
    if not payload.lignes:
        raise HTTPException(status_code=400, detail="Le devis ne contient aucune ligne")

    pdf_bytes = construire_pdf_devis(payload.lignes)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=devis-snapdevis.pdf"},
    )


@router.post("/alternative", response_model=AlternativeResultat)
async def proposer_alternative(payload: AlternativeInput) -> AlternativeResultat:
    resultat = await trouver_alternative_moins_chere(
        payload.reference_actuelle, payload.categorie, payload.prix_actuel
    )
    return AlternativeResultat(**resultat)


@router.get("/statistiques", response_model=StatistiquesDevis)
async def statistiques_devis() -> StatistiquesDevis:
    historique = await database.historique_devis.find({}, {"_id": 0}).to_list()
    nombre_sessions = len(historique)

    if nombre_sessions == 0:
        return StatistiquesDevis(
            nombre_sessions=0,
            panier_moyen_produit_principal=0.0,
            panier_moyen_devis_complet=0.0,
            delta_moyen=0.0,
            delta_pourcentage=0.0,
            repartition_par_probleme=[],
        )

    panier_moyen_principal = sum(h["produit_principal_prix"] for h in historique) / nombre_sessions
    panier_moyen_complet = sum(h["total_complet"] for h in historique) / nombre_sessions
    delta_moyen = panier_moyen_complet - panier_moyen_principal
    delta_pourcentage = (delta_moyen / panier_moyen_principal * 100) if panier_moyen_principal > 0 else 0.0

    totaux_par_probleme: dict[str, list[float]] = {}
    for h in historique:
        totaux_par_probleme.setdefault(h["probleme"], []).append(h["total_complet"])

    repartition = [
        RepartitionProbleme(probleme=probleme, nombre=len(totaux), panier_moyen=round(sum(totaux) / len(totaux), 2))
        for probleme, totaux in sorted(totaux_par_probleme.items())
    ]

    return StatistiquesDevis(
        nombre_sessions=nombre_sessions,
        panier_moyen_produit_principal=round(panier_moyen_principal, 2),
        panier_moyen_devis_complet=round(panier_moyen_complet, 2),
        delta_moyen=round(delta_moyen, 2),
        delta_pourcentage=round(delta_pourcentage, 1),
        repartition_par_probleme=repartition,
    )


@router.get("/historique", response_model=list[HistoriqueResume])
async def lister_historique() -> list[HistoriqueResume]:
    documents = await database.historique_devis.find({}).sort("date", -1).to_list()
    return [
        HistoriqueResume(
            session_id=str(document["_id"]),
            probleme=document["probleme"],
            date=document["date"],
            total=document["total_complet"],
            nombre_lignes=len(document.get("lignes", [])),
        )
        for document in documents
    ]


@router.get("/historique/{session_id}", response_model=HistoriqueDetail)
async def obtenir_historique(session_id: str) -> HistoriqueDetail:
    try:
        identifiant = ObjectId(session_id)
    except InvalidId as exc:
        raise HTTPException(status_code=400, detail="Identifiant de session invalide") from exc

    document = await database.historique_devis.find_one({"_id": identifiant})
    if document is None:
        raise HTTPException(status_code=404, detail="Session introuvable")

    lignes = [LigneDevis(**ligne) for ligne in document.get("lignes", [])]

    groupes_par_categorie: dict[str, float] = {}
    for ligne in lignes:
        groupes_par_categorie[ligne.categorie] = groupes_par_categorie.get(ligne.categorie, 0) + ligne.sous_total

    groupes = [
        GroupeCategorie(categorie=categorie, sous_total=round(sous_total, 2))
        for categorie, sous_total in groupes_par_categorie.items()
    ]

    return HistoriqueDetail(
        session_id=session_id,
        probleme=document["probleme"],
        date=document["date"],
        lignes=lignes,
        groupes=groupes,
        total=document["total_complet"],
    )
