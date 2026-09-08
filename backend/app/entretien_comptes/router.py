from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.database import database
from app.entretien_comptes.models import COMPTE_DEMO_ID, NOM_COMPTE_DEMO, CompteArtisan

router = APIRouter(prefix="/entretien/comptes", tags=["entretien-comptes"])


@router.get("/moi", response_model=CompteArtisan)
async def obtenir_compte_demo() -> CompteArtisan:
    compte = await database.entretien_comptes.find_one({"_id": COMPTE_DEMO_ID})
    if compte is None:
        compte = {
            "_id": COMPTE_DEMO_ID,
            "nom": NOM_COMPTE_DEMO,
            "cree_le": datetime.now(timezone.utc),
        }
        await database.entretien_comptes.insert_one(compte)

    return CompteArtisan(id=compte["_id"], nom=compte["nom"], cree_le=compte["cree_le"])
