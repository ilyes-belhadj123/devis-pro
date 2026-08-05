import asyncio

from app.diagnostic import service


def test_continuer_conversation_accumule_les_messages(monkeypatch):
    # test unitaire pur : on ne touche pas Mongo ici (evite le couplage motor/event-loop
    # entre plusieurs asyncio.run() independants dans la meme session de tests).
    async def fake_appeler_modele(messages):
        return (
            '{"probleme_cle": "mur_fissure_interieur", "probleme_label": "Mur fissuré", '
            '"confiance": 0.9, "questions_clarification": []}'
        )

    async def fake_categorie_pour_probleme(probleme_cle):
        return "peinture"

    monkeypatch.setattr(service, "_appeler_modele", fake_appeler_modele)
    monkeypatch.setattr(service, "_categorie_pour_probleme", fake_categorie_pour_probleme)

    messages_initiaux = [{"role": "system", "content": "..."}, {"role": "user", "content": "photo"}]
    resultat, nouveaux_messages = asyncio.run(service.continuer_conversation(messages_initiaux, "8 m2 environ"))

    assert resultat["probleme_cle"] == "mur_fissure_interieur"
    assert resultat["confiance"] == 0.9
    assert resultat["categorie"] == "peinture"
    # system + user(photo) + user(reponse) + assistant : l'historique complet est conserve
    assert len(nouveaux_messages) == 4
    assert "8 m2 environ" in nouveaux_messages[2]["content"]
    assert nouveaux_messages[3]["role"] == "assistant"


def test_estimer_quantites_filtre_les_references_invalides_et_convertit(monkeypatch):
    async def fake_appeler_modele(messages):
        return '{"quantites": {"PT-002": 3, "REF-INCONNUE": 5, "PT-008": "2"}}'

    monkeypatch.setattr(service, "_appeler_modele", fake_appeler_modele)

    session = {"messages": [{"role": "system", "content": "..."}]}
    candidats = [
        {"reference": "PT-002", "nom": "Enduit", "unite": "pot"},
        {"reference": "PT-008", "nom": "Spatule", "unite": "unité"},
    ]

    quantites = asyncio.run(service.estimer_quantites(session, candidats))

    assert quantites == {"PT-002": 3, "PT-008": 2}


def test_estimer_quantites_sans_session_renvoie_none():
    assert asyncio.run(service.estimer_quantites(None, [])) is None


def test_estimer_quantites_reponse_ia_illisible_renvoie_none(monkeypatch):
    async def fake_appeler_modele(messages):
        return "je ne comprends pas la demande"

    monkeypatch.setattr(service, "_appeler_modele", fake_appeler_modele)

    session = {"messages": [{"role": "system", "content": "..."}]}
    quantites = asyncio.run(service.estimer_quantites(session, [{"reference": "PT-002", "nom": "Enduit", "unite": "pot"}]))

    assert quantites is None
