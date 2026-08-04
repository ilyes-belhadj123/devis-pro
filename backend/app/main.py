from fastapi import FastAPI

from app.core.database import ping_database

app = FastAPI(title="SnapDevis API")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "mongodb": "connected" if await ping_database() else "unreachable"}
