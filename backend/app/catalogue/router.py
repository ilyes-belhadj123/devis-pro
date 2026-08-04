from fastapi import APIRouter

from app.catalogue.models import Produit
from app.core.database import database

router = APIRouter(prefix="/catalogue", tags=["catalogue"])


@router.get("", response_model=list[Produit])
async def lister_catalogue(categorie: str | None = None) -> list[dict]:
    filtre = {"categorie": categorie} if categorie else {}
    return await database.produits.find(filtre, {"_id": 0}).to_list()
