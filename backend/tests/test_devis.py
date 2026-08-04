def test_generer_devis_probleme_connu(client):
    response = client.post("/devis/generer", json={"probleme": "mur_fissure_interieur"})
    assert response.status_code == 200
    devis = response.json()
    assert devis["probleme"] == "mur_fissure_interieur"
    assert len(devis["lignes"]) == 4
    assert devis["total"] == round(sum(ligne["sous_total"] for ligne in devis["lignes"]), 2)
    assert devis["total"] > 0


def test_generer_devis_probleme_inconnu(client):
    response = client.post("/devis/generer", json={"probleme": "probleme_inexistant"})
    assert response.status_code == 404
