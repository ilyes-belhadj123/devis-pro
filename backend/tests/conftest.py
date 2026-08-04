import os

# Doit etre defini avant l'import de app.core.config : les tests ne doivent
# jamais lire/ecrire la base de donnees reelle (ca a deja efface une cle
# OpenRouter configuree en local par un test qui nettoie apres lui-meme).
os.environ["MONGODB_DB_NAME"] = "snapdevis_test"

import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.catalogue.seed_data import PRODUITS, REGLES_ASSOCIATION
from app.core.config import settings
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _seed_base_de_test():
    sync_client = MongoClient(settings.mongodb_uri)
    base_test = sync_client[settings.mongodb_db_name]
    base_test.produits.delete_many({})
    base_test.produits.insert_many(PRODUITS)
    base_test.regles_association.delete_many({})
    base_test.regles_association.insert_many(REGLES_ASSOCIATION)
    sync_client.close()
    yield


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
