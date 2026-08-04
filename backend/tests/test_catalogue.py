def test_catalogue_returns_products(client):
    response = client.get("/catalogue")
    assert response.status_code == 200
    produits = response.json()
    assert len(produits) > 0
    assert {"reference", "nom", "categorie", "prix", "unite"} <= produits[0].keys()


def test_catalogue_filtre_par_categorie(client):
    response = client.get("/catalogue", params={"categorie": "jardin"})
    assert response.status_code == 200
    produits = response.json()
    assert len(produits) > 0
    assert all(p["categorie"] == "jardin" for p in produits)
