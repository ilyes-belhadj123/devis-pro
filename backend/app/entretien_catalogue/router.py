import csv
import io

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile

from app.core.database import database
from app.entretien_catalogue.models import ProduitEntretien
from app.entretien_comptes.models import COMPTE_DEMO_ID

router = APIRouter(prefix="/entretien/catalogue", tags=["entretien-catalogue"])

COLONNES_ATTENDUES = ["designation", "unite", "prix", "categorie"]

TEMPLATE_CSV = (
    "designation,unite,prix,categorie\n"
    "Tonte pelouse standard,m2,0.35,tonte\n"
    "Taille de haie moyenne,ml,7.80,taille\n"
    "Plantation arbuste godet,unite,18.00,plantation\n"
)


@router.get("", response_model=list[ProduitEntretien])
async def lister_catalogue(compte_id: str = Query(default=COMPTE_DEMO_ID)) -> list[dict]:
    return await database.entretien_catalogue_produits.find(
        {"compte_id": compte_id}, {"_id": 0, "compte_id": 0}
    ).to_list()


@router.get("/template")
async def telecharger_template() -> Response:
    return Response(
        content=TEMPLATE_CSV,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=modele-catalogue-entretien.csv"},
    )


def _parser_csv(contenu: str) -> list[dict]:
    lecteur = csv.DictReader(io.StringIO(contenu))
    entetes = {(champ or "").strip().lower() for champ in (lecteur.fieldnames or [])}
    if not set(COLONNES_ATTENDUES).issubset(entetes):
        raise HTTPException(
            status_code=400,
            detail=f"Colonnes attendues dans le CSV : {', '.join(COLONNES_ATTENDUES)}",
        )

    produits: list[dict] = []
    erreurs: list[str] = []

    for numero, ligne_brute in enumerate(lecteur, start=2):  # la ligne 1 est l'en-tete
        ligne = {(cle or "").strip().lower(): valeur for cle, valeur in ligne_brute.items()}
        designation = (ligne.get("designation") or "").strip()
        unite = (ligne.get("unite") or "").strip()
        categorie = (ligne.get("categorie") or "").strip()
        prix_brut = (ligne.get("prix") or "").strip().replace(",", ".")

        if not designation or not unite or not categorie:
            erreurs.append(f"Ligne {numero} : désignation, unité et catégorie sont obligatoires")
            continue

        try:
            prix = float(prix_brut)
            if prix < 0:
                raise ValueError
        except ValueError:
            erreurs.append(f"Ligne {numero} : prix invalide (« {ligne.get('prix')} »)")
            continue

        produits.append({"designation": designation, "unite": unite, "prix": prix, "categorie": categorie})

    if erreurs:
        raise HTTPException(status_code=400, detail="; ".join(erreurs))

    return produits


@router.post("/import", response_model=list[ProduitEntretien])
async def importer_catalogue(
    fichier: UploadFile = File(...), compte_id: str = Query(default=COMPTE_DEMO_ID)
) -> list[dict]:
    contenu_brut = await fichier.read()
    try:
        contenu = contenu_brut.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Le fichier doit être un CSV encodé en UTF-8") from exc

    produits = _parser_csv(contenu)
    if not produits:
        raise HTTPException(status_code=400, detail="Le fichier ne contient aucune ligne de produit valide")

    await database.entretien_catalogue_produits.delete_many({"compte_id": compte_id})
    await database.entretien_catalogue_produits.insert_many(
        [{**produit, "compte_id": compte_id} for produit in produits]
    )

    return produits
