"""Export du devis validé vers un format générique de facturation (CSV/JSON).

Format documenté dans docs/EXPORT_FORMAT.md - toute modification des colonnes/clés
ci-dessous doit être répercutée dans ce document.
"""

import csv
import io

# Taux de TVA générique utilisé pour l'export (prototype de démo, pas de gestion
# multi-taux) - configurable dans une vraie intégration facturation.
TAUX_TVA = 0.20

COLONNES_CSV = [
    "reference_devis",
    "categorie_devis",
    "formule",
    "designation",
    "categorie_prestation",
    "unite",
    "quantite",
    "prix_unitaire_ht",
    "montant_ht",
    "taux_tva",
    "montant_ttc",
]


def _lignes_export(devis_id: str, categorie_devis: str, formule: dict) -> list[dict]:
    lignes = []
    for ligne in formule["lignes"]:
        montant_ht = round(ligne["prix_unitaire"] * ligne["quantite"], 2)
        montant_ttc = round(montant_ht * (1 + TAUX_TVA), 2)
        lignes.append(
            {
                "reference_devis": devis_id,
                "categorie_devis": categorie_devis,
                "formule": formule["niveau"],
                "designation": ligne["designation"],
                "categorie_prestation": ligne["categorie"],
                "unite": ligne["unite"],
                "quantite": ligne["quantite"],
                "prix_unitaire_ht": ligne["prix_unitaire"],
                "montant_ht": montant_ht,
                "taux_tva": TAUX_TVA,
                "montant_ttc": montant_ttc,
            }
        )
    return lignes


def construire_csv_export(devis_id: str, categorie_devis: str, formule: dict) -> str:
    lignes = _lignes_export(devis_id, categorie_devis, formule)
    buffer = io.StringIO()
    ecrivain = csv.DictWriter(buffer, fieldnames=COLONNES_CSV)
    ecrivain.writeheader()
    ecrivain.writerows(lignes)
    return buffer.getvalue()


def construire_json_export(devis_id: str, categorie_devis: str, formule: dict) -> dict:
    lignes = _lignes_export(devis_id, categorie_devis, formule)
    total_ht = round(sum(ligne["montant_ht"] for ligne in lignes), 2)
    total_ttc = round(sum(ligne["montant_ttc"] for ligne in lignes), 2)
    return {
        "reference_devis": devis_id,
        "categorie_devis": categorie_devis,
        "formule": formule["niveau"],
        "devise": "EUR",
        "taux_tva": TAUX_TVA,
        "lignes": lignes,
        "total_ht": total_ht,
        "total_ttc": total_ttc,
    }
