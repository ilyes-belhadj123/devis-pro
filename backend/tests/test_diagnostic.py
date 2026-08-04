def test_analyser_sans_cle_configuree_renvoie_mode_degrade(client):
    client.delete("/parametres/openrouter")

    response = client.post(
        "/diagnostic/analyser",
        files={"photo": ("test.jpg", b"contenu-image-factice", "image/jpeg")},
    )
    assert response.status_code == 200
    resultat = response.json()
    assert resultat["degrade"] is True
    assert resultat["probleme_cle"] == "mur_fissure_interieur"
