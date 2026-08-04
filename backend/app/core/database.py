from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_uri)
database = client[settings.mongodb_db_name]


async def ping_database() -> bool:
    try:
        await client.admin.command("ping")
        return True
    except Exception:
        return False
