"""Apprentissage des corrections artisan (TICKET-601).

Quand l'artisan corrige une quantite ou un prix lors de la validation d'un devis
(app/entretien_validation/router.py::valider_devis), la correction est enregistree ici,
associee au compte et a la categorie de besoin concernee. Une future generation de devis
pour ce meme compte et cette meme categorie ponderera la suggestion initiale avec la
moyenne des corrections passees pour la designation concernee.

Strictement local au compte : toutes les requetes sont filtrees par compte_id, jamais
d'agregation inter-comptes.
"""

from datetime import datetime, timezone

from app.core.database import database

COLLECTION = "entretien_corrections"

# Ecart minimal (10%) en dessous duquel une difference est consideree comme du bruit
# (arrondi de l'IA, ajustement mineur) plutot qu'une vraie correction a apprendre.
SEUIL_ECART_SIGNIFICATIF = 0.10


async def enregistrer_correction(
    compte_id: str, categorie: str, designation: str, champ: str, valeur_generee: float, valeur_corrigee: float
) -> None:
    if valeur_generee <= 0:
        return
    ratio = valeur_corrigee / valeur_generee
    if abs(ratio - 1.0) < SEUIL_ECART_SIGNIFICATIF:
        return

    await database[COLLECTION].insert_one(
        {
            "compte_id": compte_id,
            "categorie": categorie,
            "designation": designation,
            "champ": champ,
            "valeur_generee": valeur_generee,
            "valeur_corrigee": valeur_corrigee,
            "ratio": ratio,
            "cree_le": datetime.now(timezone.utc),
        }
    )


async def _ratio_appris(compte_id: str, categorie: str, designation: str, champ: str) -> float | None:
    corrections = await database[COLLECTION].find(
        {"compte_id": compte_id, "categorie": categorie, "designation": designation, "champ": champ}
    ).to_list()
    if not corrections:
        return None
    return sum(c["ratio"] for c in corrections) / len(corrections)


async def appliquer_ponderation(
    compte_id: str, categorie: str, formules: dict[str, list[dict]]
) -> tuple[dict[str, list[dict]], list[str]]:
    """Ajuste quantite/prix des lignes des formules selon l'historique de corrections
    de ce compte pour cette categorie. Renvoie les formules ajustees + la liste des
    designations effectivement modifiees (pour affichage cote artisan)."""
    designations_ajustees: set[str] = set()

    for lignes in formules.values():
        for produit in lignes:
            ratio_quantite = await _ratio_appris(compte_id, categorie, produit["designation"], "quantite")
            if ratio_quantite is not None and abs(ratio_quantite - 1.0) >= SEUIL_ECART_SIGNIFICATIF:
                produit["quantite"] = round(produit["quantite"] * ratio_quantite, 2)
                designations_ajustees.add(produit["designation"])

            ratio_prix = await _ratio_appris(compte_id, categorie, produit["designation"], "prix_unitaire")
            if ratio_prix is not None and abs(ratio_prix - 1.0) >= SEUIL_ECART_SIGNIFICATIF:
                produit["prix"] = round(produit["prix"] * ratio_prix, 2)
                designations_ajustees.add(produit["designation"])

    return formules, sorted(designations_ajustees)
