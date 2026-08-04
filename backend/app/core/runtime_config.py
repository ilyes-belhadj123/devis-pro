from app.core.config import settings
from app.core.database import database

DOC_ID = "openrouter"


async def get_openrouter_api_key() -> str | None:
    doc = await database.parametres.find_one({"_id": DOC_ID})
    if doc and doc.get("api_key"):
        return doc["api_key"]
    return settings.openrouter_api_key


async def set_openrouter_api_key(api_key: str) -> None:
    await database.parametres.update_one({"_id": DOC_ID}, {"$set": {"api_key": api_key}}, upsert=True)


async def clear_openrouter_api_key() -> None:
    await database.parametres.delete_one({"_id": DOC_ID})


async def is_openrouter_configured() -> bool:
    return bool(await get_openrouter_api_key())
