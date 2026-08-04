from fastapi import APIRouter, HTTPException

from app.core.runtime_config import clear_openrouter_api_key, is_openrouter_configured, set_openrouter_api_key
from app.parametres.models import CleApiInput, StatutCle

router = APIRouter(prefix="/parametres", tags=["parametres"])


@router.get("/openrouter", response_model=StatutCle)
async def statut_cle_openrouter() -> StatutCle:
    return StatutCle(configuree=await is_openrouter_configured())


@router.put("/openrouter", response_model=StatutCle)
async def definir_cle_openrouter(payload: CleApiInput) -> StatutCle:
    cle = payload.api_key.strip()
    if not cle:
        raise HTTPException(status_code=400, detail="La clé ne peut pas être vide")
    await set_openrouter_api_key(cle)
    return StatutCle(configuree=True)


@router.delete("/openrouter", response_model=StatutCle)
async def supprimer_cle_openrouter() -> StatutCle:
    await clear_openrouter_api_key()
    return StatutCle(configuree=await is_openrouter_configured())
