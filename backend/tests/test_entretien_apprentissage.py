"""TICKET-601 : apres 3 corrections similaires enregistrees sur un compte, une nouvelle
suggestion generee pour ce compte doit refleter la tendance des corrections precedentes -
et rester strictement locale a ce compte (jamais mutualisee)."""

import io


def _importer_catalogue_test(client, compte_id: str) -> None:
    csv_contenu = "designation,unite,prix,categorie\nTonte test apprentissage,m2,1.00,tonte\n"
    reponse = client.post(
        f"/entretien/catalogue/import?compte_id={compte_id}",
        files={"fichier": ("catalogue.csv", io.BytesIO(csv_contenu.encode("utf-8")), "text/csv")},
    )
    assert reponse.status_code == 200


def _creer_et_valider_avec_correction(client, compte_id: str, quantite_generee: float, quantite_corrigee: float) -> None:
    formule = {
        "niveau": "standard",
        "label": "Standard",
        "description": "Recommandé",
        "lignes": [
            {
                "designation": "Tonte test apprentissage",
                "categorie": "tonte",
                "unite": "m2",
                "prix_unitaire": 1.0,
                "quantite": quantite_generee,
            }
        ],
    }
    creation = client.post(
        "/entretien/validation/devis", json={"compte_id": compte_id, "categorie": "tonte", "formules": [formule]}
    )
    assert creation.status_code == 200
    devis_id = creation.json()["id"]

    # l'artisan corrige la quantite avant de valider (simule l'edition sur l'ecran de validation)
    formule_corrigee = {**formule, "lignes": [{**formule["lignes"][0], "quantite": quantite_corrigee}]}
    modification = client.put(f"/entretien/validation/devis/{devis_id}", json={"formules": [formule_corrigee]})
    assert modification.status_code == 200

    validation = client.post(f"/entretien/validation/devis/{devis_id}/valider")
    assert validation.status_code == 200


def test_apprentissage_influence_les_futures_suggestions(client):
    compte_id = "compte-test-apprentissage-influence"
    _importer_catalogue_test(client, compte_id)

    # 3 corrections similaires : l'artisan multiplie systematiquement la quantite generee par 3
    for _ in range(3):
        _creer_et_valider_avec_correction(client, compte_id, quantite_generee=1.0, quantite_corrigee=3.0)

    generation = client.post(
        "/entretien/devis/generer",
        json={"compte_id": compte_id, "lieu": "exterieur", "categorie": "tonte", "taches_suggerees": [], "estimation_surface": None},
    )
    assert generation.status_code == 200
    corps = generation.json()

    assert "Tonte test apprentissage" in corps["ajustements_appris"]

    ligne = next(l for l in corps["formules"][0]["lignes"] if l["designation"] == "Tonte test apprentissage")
    # sans apprentissage, le repli deterministe donne quantite=1 (pas d'estimation de surface) ;
    # avec la tendance apprise (ratio moyen x3), la suggestion doit refleter ce x3.
    assert ligne["quantite"] == 3.0


def test_apprentissage_reste_strictement_local_au_compte(client):
    compte_avec_historique = "compte-test-apprentissage-source"
    compte_isole = "compte-test-apprentissage-isole"
    _importer_catalogue_test(client, compte_avec_historique)
    _importer_catalogue_test(client, compte_isole)

    for _ in range(3):
        _creer_et_valider_avec_correction(client, compte_avec_historique, quantite_generee=1.0, quantite_corrigee=5.0)

    generation = client.post(
        "/entretien/devis/generer",
        json={
            "compte_id": compte_isole,
            "lieu": "exterieur",
            "categorie": "tonte",
            "taches_suggerees": [],
            "estimation_surface": None,
        },
    )
    assert generation.status_code == 200
    corps = generation.json()

    assert corps["ajustements_appris"] == []
    ligne = next(l for l in corps["formules"][0]["lignes"] if l["designation"] == "Tonte test apprentissage")
    assert ligne["quantite"] == 1.0
