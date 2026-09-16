from fastapi import APIRouter, HTTPException

from app.core.database import database
from app.entretien_devis.models import (
    ComparateurInput,
    ComparateurResultat,
    ContratRecurrentGenere,
    ContratRecurrentInput,
    DevisEntretienGenere,
    FormuleDevis,
    FournisseurComparateur,
    GenererDevisInput,
    LigneDevisEntretien,
)
from app.entretien_devis.apprentissage import appliquer_ponderation
from app.entretien_devis.service import comparer_fournisseurs, formules_par_defaut, generer_formules

router = APIRouter(prefix="/entretien/devis", tags=["entretien-devis"])

LABELS_NIVEAU = {"eco": "Éco", "standard": "Standard", "premium": "Premium"}
DESCRIPTIONS_NIVEAU = {
    "eco": "Prestations essentielles",
    "standard": "Recommandé — essentiel + finitions",
    "premium": "Confort complet + options renforcées",
}

# "bimensuelle" est utilisee ici au sens courant des contrats d'entretien (un passage tous les
# 2 mois), pas au sens strict "deux fois par mois" - le libelle explicite le nombre de passages
# pour lever toute ambiguite cote artisan/client.
FREQUENCES = {
    "mensuelle": {"label": "Mensuelle (12 passages/an)", "interventions_an": 12},
    "bimensuelle": {"label": "Bimensuelle (6 passages/an, tous les 2 mois)", "interventions_an": 6},
    "saisonniere": {"label": "Saisonnière (4 passages/an)", "interventions_an": 4},
}

# Remise accordee sur le prix unitaire d'une intervention en echange d'un engagement contractuel
# recurrent, par rapport au meme devis facture ponctuellement a chaque passage.
TAUX_DEGRESSIVITE = 0.90


@router.post("/generer", response_model=DevisEntretienGenere)
async def generer_devis(payload: GenererDevisInput) -> DevisEntretienGenere:
    catalogue = await database.entretien_catalogue_produits.find(
        {"compte_id": payload.compte_id}, {"_id": 0}
    ).to_list()
    if not catalogue:
        raise HTTPException(status_code=404, detail="Aucun catalogue importé pour ce compte")

    estimation = payload.estimation_surface.model_dump() if payload.estimation_surface else None

    formules_brutes = await generer_formules(
        payload.categorie, payload.lieu, payload.taches_suggerees, estimation, catalogue
    )
    if formules_brutes is None:
        formules_brutes = formules_par_defaut(payload.categorie, estimation, catalogue)
    if formules_brutes is None:
        raise HTTPException(status_code=404, detail="Aucune prestation du catalogue ne correspond à ce diagnostic")

    formules_brutes, ajustements_appris = await appliquer_ponderation(payload.compte_id, payload.categorie, formules_brutes)

    formules = []
    for niveau in ("eco", "standard", "premium"):
        lignes = [
            LigneDevisEntretien(
                designation=produit["designation"],
                categorie=produit["categorie"],
                unite=produit["unite"],
                prix_unitaire=produit["prix"],
                quantite=produit["quantite"],
                sous_total=round(produit["prix"] * produit["quantite"], 2),
            )
            for produit in (formules_brutes.get(niveau) or [])
        ]
        total = round(sum(ligne.sous_total for ligne in lignes), 2)
        formules.append(
            FormuleDevis(niveau=niveau, label=LABELS_NIVEAU[niveau], description=DESCRIPTIONS_NIVEAU[niveau], lignes=lignes, total=total)
        )

    return DevisEntretienGenere(
        compte_id=payload.compte_id, categorie=payload.categorie, formules=formules, ajustements_appris=ajustements_appris
    )


@router.post("/contrat-recurrent", response_model=ContratRecurrentGenere)
async def generer_contrat_recurrent(payload: ContratRecurrentInput) -> ContratRecurrentGenere:
    if payload.frequence not in FREQUENCES:
        raise HTTPException(status_code=400, detail=f"Fréquence inconnue : {payload.frequence}")
    if not payload.lignes:
        raise HTTPException(status_code=400, detail="Le devis de référence ne contient aucune ligne")

    prix_ponctuel = round(sum(ligne.prix_unitaire * ligne.quantite for ligne in payload.lignes), 2)
    frequence_info = FREQUENCES[payload.frequence]
    prix_intervention_contrat = round(prix_ponctuel * TAUX_DEGRESSIVITE, 2)
    prix_annuel = round(prix_intervention_contrat * frequence_info["interventions_an"], 2)
    prix_mensuel = round(prix_annuel / 12, 2)

    return ContratRecurrentGenere(
        frequence=payload.frequence,
        frequence_label=frequence_info["label"],
        duree_mois=payload.duree_mois,
        interventions_an=frequence_info["interventions_an"],
        prix_intervention_ponctuel=prix_ponctuel,
        prix_intervention_contrat=prix_intervention_contrat,
        prix_annuel=prix_annuel,
        prix_mensuel=prix_mensuel,
        economie_pourcentage=round((1 - TAUX_DEGRESSIVITE) * 100, 1),
    )


@router.post("/comparateur", response_model=ComparateurResultat)
async def comparer_prix(payload: ComparateurInput) -> ComparateurResultat:
    fournisseurs = comparer_fournisseurs(payload.designation, payload.prix_actuel)
    return ComparateurResultat(
        designation=payload.designation,
        fournisseurs=[FournisseurComparateur(**f) for f in fournisseurs],
    )
