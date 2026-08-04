def test_statistiques_apres_generation_de_devis(client):
    client.post("/devis/generer", json={"probleme": "mur_fissure_interieur"})
    client.post("/devis/generer", json={"probleme": "robinet_qui_fuit"})

    response = client.get("/devis/statistiques")
    assert response.status_code == 200
    stats = response.json()

    assert stats["nombre_sessions"] >= 2
    assert stats["panier_moyen_devis_complet"] >= stats["panier_moyen_produit_principal"]
    assert stats["delta_moyen"] >= 0

    problemes = {r["probleme"] for r in stats["repartition_par_probleme"]}
    assert "mur_fissure_interieur" in problemes
    assert "robinet_qui_fuit" in problemes
