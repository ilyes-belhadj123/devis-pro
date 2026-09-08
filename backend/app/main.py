from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.catalogue.router import router as catalogue_router
from app.core.config import settings
from app.core.database import ping_database
from app.devis.router import router as devis_router
from app.diagnostic.router import router as diagnostic_router
from app.entretien_catalogue.router import router as entretien_catalogue_router
from app.entretien_comptes.router import router as entretien_comptes_router
from app.entretien_devis.router import router as entretien_devis_router
from app.entretien_diagnostic.router import router as entretien_diagnostic_router
from app.entretien_validation.router import router as entretien_validation_router
from app.parametres.router import router as parametres_router

app = FastAPI(title="SnapDevis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalogue_router)
app.include_router(devis_router)
app.include_router(diagnostic_router)
app.include_router(parametres_router)
app.include_router(entretien_comptes_router)
app.include_router(entretien_catalogue_router)
app.include_router(entretien_diagnostic_router)
app.include_router(entretien_devis_router)
app.include_router(entretien_validation_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "mongodb": "connected" if await ping_database() else "unreachable"}
