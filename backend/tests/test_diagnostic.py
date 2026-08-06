def test_analyser_sans_cle_configuree_renvoie_mode_degrade(client):
    client.delete("/parametres/openrouter")

    response = client.post(
        "/diagnostic/analyser",
        files={"photos": ("test.jpg", b"contenu-image-factice", "image/jpeg")},
    )
    assert response.status_code == 200
    resultat = response.json()
    assert resultat["degrade"] is True
    assert resultat["probleme_cle"] == "mur_fissure_interieur"
    assert resultat["session_id"] is not None


def test_analyser_accepte_plusieurs_photos(client):
    client.delete("/parametres/openrouter")

    response = client.post(
        "/diagnostic/analyser",
        files=[
            ("photos", ("angle1.jpg", b"contenu-image-1", "image/jpeg")),
            ("photos", ("angle2.jpg", b"contenu-image-2", "image/jpeg")),
        ],
    )
    assert response.status_code == 200
    resultat = response.json()
    assert resultat["degrade"] is True
    assert resultat["session_id"] is not None


def test_analyser_accepte_note_et_point_de_reperage(client):
    client.delete("/parametres/openrouter")

    response = client.post(
        "/diagnostic/analyser",
        files={"photos": ("test.jpg", b"contenu-image-factice", "image/jpeg")},
        data={
            "note": "La fuite n'apparaît qu'à l'usage",
            "points": '[{"index": 0, "x": 0.62, "y": 0.4}]',
        },
    )
    assert response.status_code == 200
    resultat = response.json()
    assert resultat["degrade"] is True
    assert resultat["session_id"] is not None


def test_analyser_ignore_points_mal_formes(client):
    client.delete("/parametres/openrouter")

    response = client.post(
        "/diagnostic/analyser",
        files={"photos": ("test.jpg", b"contenu-image-factice", "image/jpeg")},
        data={"points": "pas-du-json-valide"},
    )
    assert response.status_code == 200
    assert response.json()["degrade"] is True


def test_affiner_sans_session_bascule_interieur_exterieur(client):
    response = client.post(
        "/diagnostic/affiner",
        data={"session_id": "", "probleme_cle": "mur_fissure_interieur", "reponse": "Extérieur"},
    )
    assert response.status_code == 200
    resultat = response.json()
    assert resultat["probleme_cle"] == "mur_fissure_exterieur"
    assert resultat["questions_clarification"] == []
    assert resultat["degrade"] is False


def test_affiner_reponse_sans_correspondance_garde_la_cle(client):
    response = client.post(
        "/diagnostic/affiner",
        data={"session_id": "", "probleme_cle": "robinet_qui_fuit", "reponse": "Extérieur"},
    )
    assert response.status_code == 200
    resultat = response.json()
    assert resultat["probleme_cle"] == "robinet_qui_fuit"


def test_affiner_accepte_une_photo_supplementaire_sans_session(client):
    response = client.post(
        "/diagnostic/affiner",
        data={"session_id": "", "probleme_cle": "robinet_qui_fuit", "reponse": "Voici un gros plan"},
        files={"photos": ("detail.jpg", b"contenu-image-factice", "image/jpeg")},
    )
    assert response.status_code == 200
    resultat = response.json()
    assert resultat["probleme_cle"] == "robinet_qui_fuit"
    assert resultat["degrade"] is False
