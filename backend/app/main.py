from fastapi import FastAPI

from app.catalogue.router import router as catalogue_router
from app.core.database import ping_database

app = FastAPI(title="SnapDevis API")
app.include_router(catalogue_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "mongodb": "connected" if await ping_database() else "unreachable"}
