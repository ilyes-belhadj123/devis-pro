import csv
import io


def _creer_devis_valide(client):
    creation = client.post(
        "/entretien/validation/devis",
        json={
            "compte_id": "demo",
            "categorie": "tonte",
            "formules": [
                {
                    "niveau": "eco",
                    "label": "Éco",
                    "description": "Essentiel",
                    "lignes": [
                        {
                            "designation": "Tonte pelouse standard",
                            "categorie": "tonte",
                            "unite": "m2",
                            "prix_unitaire": 0.35,
                            "quantite": 120,
                        },
                    ],
                },
                {
                    "niveau": "standard",
                    "label": "Standard",
                    "description": "Recommandé",
                    "lignes": [
                        {
                            "designation": "Tonte pelouse standard",
                            "categorie": "tonte",
                            "unite": "m2",
                            "prix_unitaire": 0.35,
                            "quantite": 120,
                        },
                        {
                            "designation": "Ramassage et evacuation de l'herbe coupee",
                            "categorie": "evacuation",
                            "unite": "m2",
                            "prix_unitaire": 0.15,
                            "quantite": 120,
                        },
                    ],
                },
                {
                    "niveau": "premium",
                    "label": "Premium",
                    "description": "Complet",
                    "lignes": [
                        {
                            "designation": "Tonte pelouse standard",
                            "categorie": "tonte",
                            "unite": "m2",
                            "prix_unitaire": 0.35,
                            "quantite": 120,
                        },
                    ],
                },
            ],
        },
    )
    assert creation.status_code == 200
    devis_id = creation.json()["id"]

    validation = client.post(f"/entretien/validation/devis/{devis_id}/valider")
    assert validation.status_code == 200
    return devis_id


def test_export_refuse_si_devis_non_valide(client):
    creation = client.post(
        "/entretien/validation/devis",
        json={
            "compte_id": "demo",
            "categorie": "tonte",
            "formules": [{"niveau": "standard", "label": "Standard", "description": "x", "lignes": []}],
        },
    )
    devis_id = creation.json()["id"]

    response = client.get(f"/entretien/validation/devis/{devis_id}/export")
    assert response.status_code == 409


def test_export_csv_respecte_le_format_documente(client):
    devis_id = _creer_devis_valide(client)
    response = client.get(f"/entretien/validation/devis/{devis_id}/export?niveau=standard&format=csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")

    lignes = list(csv.DictReader(io.StringIO(response.text)))
    assert len(lignes) == 2

    colonnes_attendues = {
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
    }
    assert colonnes_attendues.issubset(lignes[0].keys())

    premiere = lignes[0]
    assert premiere["reference_devis"] == devis_id
    assert premiere["formule"] == "standard"
    montant_ht = float(premiere["montant_ht"])
    montant_ttc = float(premiere["montant_ttc"])
    assert round(montant_ttc, 2) == round(montant_ht * 1.2, 2)


def test_export_json_respecte_le_format_documente(client):
    devis_id = _creer_devis_valide(client)
    response = client.get(f"/entretien/validation/devis/{devis_id}/export?niveau=standard&format=json")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    corps = response.json()
    assert corps["reference_devis"] == devis_id
    assert corps["formule"] == "standard"
    assert corps["taux_tva"] == 0.2
    assert len(corps["lignes"]) == 2
    assert round(corps["total_ht"], 2) == round(sum(ligne["montant_ht"] for ligne in corps["lignes"]), 2)
    assert round(corps["total_ttc"], 2) == round(sum(ligne["montant_ttc"] for ligne in corps["lignes"]), 2)


def test_export_pdf_valide(client):
    devis_id = _creer_devis_valide(client)
    response = client.get(f"/entretien/validation/devis/{devis_id}/pdf?niveau=standard")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_export_format_inconnu_rejete(client):
    devis_id = _creer_devis_valide(client)
    response = client.get(f"/entretien/validation/devis/{devis_id}/export?format=xml")
    assert response.status_code == 400
