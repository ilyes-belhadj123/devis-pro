from fastapi import APIRouter, HTTPException

from app.core.database import database
from app.devis.models import DevisGenere, DiagnosticInput, GroupeCategorie, LigneDevis

router = APIRouter(prefix="/devis", tags=["devis"])


@router.post("/generer", response_model=DevisGenere)
async def generer_devis(diagnostic: DiagnosticInput) -> DevisGenere:
    regle = await database.regles_association.find_one({"probleme": diagnostic.probleme})
    if regle is None:
        raise HTTPException(status_code=404, detail=f"Aucune regle d'association pour '{diagnostic.probleme}'")

    produits = await database.produits.find(
        {"reference": {"$in": regle["references_produits"]}}, {"_id": 0}
    ).to_list()

    lignes = [
        LigneDevis(
            reference=produit["reference"],
            nom=produit["nom"],
            categorie=produit["categorie"],
            unite=produit["unite"],
            prix_unitaire=produit["prix"],
            quantite=1,
            sous_total=round(produit["prix"], 2),
        )
        for produit in produits
    ]

    groupes_par_categorie: dict[str, float] = {}
    for ligne in lignes:
        groupes_par_categorie[ligne.categorie] = groupes_par_categorie.get(ligne.categorie, 0) + ligne.sous_total

    groupes = [
        GroupeCategorie(categorie=categorie, sous_total=round(sous_total, 2))
        for categorie, sous_total in groupes_par_categorie.items()
    ]

    total = round(sum(ligne.sous_total for ligne in lignes), 2)

    return DevisGenere(probleme=diagnostic.probleme, lignes=lignes, groupes=groupes, total=total)
