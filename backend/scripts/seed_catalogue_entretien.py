"""Peuple la base MongoDB avec le compte et le catalogue demo SnapDevis Entretien.

Usage: python -m scripts.seed_catalogue_entretien (depuis le dossier backend/, venv active)
"""

import asyncio
from datetime import datetime, timezone

from app.core.database import database
from app.entretien_catalogue.seed_data import PRODUITS_DEMO
from app.entretien_comptes.models import COMPTE_DEMO_ID, NOM_COMPTE_DEMO


async def seed() -> None:
    await database.entretien_comptes.update_one(
        {"_id": COMPTE_DEMO_ID},
        {"$setOnInsert": {"nom": NOM_COMPTE_DEMO, "cree_le": datetime.now(timezone.utc)}},
        upsert=True,
    )

    await database.entretien_catalogue_produits.delete_many({"compte_id": COMPTE_DEMO_ID})
    await database.entretien_catalogue_produits.insert_many(
        [{**produit, "compte_id": COMPTE_DEMO_ID} for produit in PRODUITS_DEMO]
    )

    print(f"Compte demo '{NOM_COMPTE_DEMO}' pret, {len(PRODUITS_DEMO)} produits d'entretien inseres.")


if __name__ == "__main__":
    asyncio.run(seed())
