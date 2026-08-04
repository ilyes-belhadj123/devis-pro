def test_alternative_trouvee_moins_chere(client):
    # Ponceuse manuelle bloc (fixation, 12.00 EUR) a des candidats moins chers dans sa categorie
    response = client.post(
        "/devis/alternative",
        json={"reference_actuelle": "FX-006", "categorie": "fixation", "prix_actuel": 59.0},
    )
    assert response.status_code == 200
    resultat = response.json()
    assert resultat["trouve"] is True
    assert resultat["prix"] < 59.0
    assert resultat["reference"] != "FX-006"


def test_alternative_aucun_candidat(client):
    # Produit le moins cher de sa categorie : aucune alternative moins chere possible
    response = client.post(
        "/devis/alternative",
        json={"reference_actuelle": "JD-003", "categorie": "jardin", "prix_actuel": 0.01},
    )
    assert response.status_code == 200
    resultat = response.json()
    assert resultat["trouve"] is False
    assert resultat["reference"] is None
