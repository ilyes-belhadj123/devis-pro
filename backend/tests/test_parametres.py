def test_definir_puis_supprimer_cle_openrouter(client):
    response = client.put("/parametres/openrouter", json={"api_key": "sk-or-test-123"})
    assert response.status_code == 200
    assert response.json() == {"configuree": True}

    statut = client.get("/parametres/openrouter")
    assert statut.json() == {"configuree": True}

    suppression = client.delete("/parametres/openrouter")
    assert suppression.status_code == 200
    assert suppression.json() == {"configuree": False}


def test_definir_cle_vide_rejetee(client):
    response = client.put("/parametres/openrouter", json={"api_key": "   "})
    assert response.status_code == 400
