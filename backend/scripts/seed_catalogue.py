"""Peuple la base MongoDB avec le catalogue demo SnapDevis.

Usage: python -m scripts.seed_catalogue (depuis le dossier backend/, venv active)
"""

import asyncio

from app.catalogue.seed_data import PRODUITS, REGLES_ASSOCIATION
from app.core.database import database


async def seed() -> None:
    await database.produits.delete_many({})
    await database.produits.insert_many(PRODUITS)

    await database.regles_association.delete_many({})
    await database.regles_association.insert_many(REGLES_ASSOCIATION)

    print(f"{len(PRODUITS)} produits inseres, {len(REGLES_ASSOCIATION)} regles d'association inserees.")


if __name__ == "__main__":
    asyncio.run(seed())
