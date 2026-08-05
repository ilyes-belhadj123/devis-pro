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


def test_selectionner_materiel_filtre_les_references_invalides_et_convertit(monkeypatch):
    async def fake_appeler_modele(messages):
        return (
            '{"produits": [{"reference": "PT-002", "quantite": 3}, '
            '{"reference": "REF-INCONNUE", "quantite": 5}, '
            '{"reference": "PT-008", "quantite": "2"}]}'
        )

    monkeypatch.setattr(service, "_appeler_modele", fake_appeler_modele)

    session = {"messages": [{"role": "system", "content": "..."}]}
    catalogue = [
        {"reference": "PT-002", "nom": "Enduit", "categorie": "peinture", "unite": "pot", "prix": 8.9},
        {"reference": "PT-008", "nom": "Spatule", "categorie": "peinture", "unite": "unité", "prix": 4.5},
        {"reference": "PT-009", "nom": "Ponceuse", "categorie": "peinture", "unite": "unité", "prix": 12.0},
    ]

    materiel = asyncio.run(service.selectionner_materiel(session, catalogue))

    # seules PT-002 et PT-008 sont retenues (reference inconnue ignoree, PT-009 non choisie par l'IA)
    assert {p["reference"]: p["quantite"] for p in materiel} == {"PT-002": 3, "PT-008": 2}
    assert all("nom" in p and "prix" in p for p in materiel)


def test_selectionner_materiel_sans_session_renvoie_none():
    assert asyncio.run(service.selectionner_materiel(None, [])) is None


def test_selectionner_materiel_reponse_ia_illisible_renvoie_none(monkeypatch):
    async def fake_appeler_modele(messages):
        return "je ne comprends pas la demande"

    monkeypatch.setattr(service, "_appeler_modele", fake_appeler_modele)

    session = {"messages": [{"role": "system", "content": "..."}]}
    catalogue = [{"reference": "PT-002", "nom": "Enduit", "categorie": "peinture", "unite": "pot", "prix": 8.9}]
    materiel = asyncio.run(service.selectionner_materiel(session, catalogue))

    assert materiel is None
