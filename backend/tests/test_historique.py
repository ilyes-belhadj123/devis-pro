def test_historique_liste_et_detail_fideles(client):
    genere = client.post("/devis/generer", json={"probleme": "etagere_a_fixer"})
    total_genere = genere.json()["total"]

    liste = client.get("/devis/historique")
    assert liste.status_code == 200
    resumes = liste.json()
    assert len(resumes) > 0
    assert resumes[0]["probleme"] is not None

    correspondant = next((r for r in resumes if r["probleme"] == "etagere_a_fixer" and r["total"] == total_genere), None)
    assert correspondant is not None

    detail = client.get(f"/devis/historique/{correspondant['session_id']}")
    assert detail.status_code == 200
    donnees = detail.json()
    assert donnees["probleme"] == "etagere_a_fixer"
    assert donnees["total"] == total_genere
    assert len(donnees["lignes"]) == correspondant["nombre_lignes"]


def test_historique_detail_id_invalide(client):
    response = client.get("/devis/historique/pas-un-id-mongo")
    assert response.status_code == 400


def test_historique_detail_introuvable(client):
    response = client.get("/devis/historique/000000000000000000000000")
    assert response.status_code == 404
