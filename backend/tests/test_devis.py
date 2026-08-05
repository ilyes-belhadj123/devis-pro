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


def test_generer_devis_avec_session_utilise_la_selection_ia(client, monkeypatch):
    from app.devis import router as devis_router

    def fake_recuperer_session(session_id):
        return {"messages": [{"role": "system", "content": "..."}]}

    async def fake_selectionner_materiel(session, catalogue):
        candidat = catalogue[0]
        return [{**candidat, "quantite": 7}]

    monkeypatch.setattr(devis_router, "recuperer_session", fake_recuperer_session)
    monkeypatch.setattr(devis_router, "selectionner_materiel", fake_selectionner_materiel)

    response = client.post(
        "/devis/generer", json={"probleme": "mur_fissure_interieur", "session_id": "une-session"}
    )
    assert response.status_code == 200
    devis = response.json()
    # la selection IA (mockee) ne renvoie qu'un seul produit avec quantite 7,
    # au lieu des 4 produits fixes de la regle avec quantite 1
    assert len(devis["lignes"]) == 1
    assert devis["lignes"][0]["quantite"] == 7
