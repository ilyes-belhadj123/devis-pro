def test_export_pdf_renvoie_un_pdf_valide(client):
    response = client.post(
        "/devis/pdf",
        json={
            "lignes": [
                {"nom": "Enduit de rebouchage 1kg", "categorie": "peinture", "unite": "pot", "prix_unitaire": 8.9, "quantite": 1},
                {"nom": "Spatule inox 10cm", "categorie": "fixation", "unite": "unité", "prix_unitaire": 4.5, "quantite": 2},
            ]
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_export_pdf_sans_lignes_rejete(client):
    response = client.post("/devis/pdf", json={"lignes": []})
    assert response.status_code == 400
