from fastapi import APIRouter, File, UploadFile

from app.diagnostic.models import DiagnosticResultat
from app.diagnostic.service import DiagnosticIndisponible, analyser_photo

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])

DIAGNOSTIC_DEGRADE = DiagnosticResultat(
    probleme_cle="mur_fissure_interieur",
    probleme_label="Mur fissuré intérieur (diagnostic simulé — service IA indisponible)",
    categorie="peinture",
    confiance=0.5,
    questions_clarification=[],
    degrade=True,
)


@router.post("/analyser", response_model=DiagnosticResultat)
async def analyser(photo: UploadFile = File(...)) -> DiagnosticResultat:
    contenu = await photo.read()
    try:
        resultat = await analyser_photo(contenu, photo.content_type or "image/jpeg")
        return DiagnosticResultat(**resultat)
    except DiagnosticIndisponible:
        return DIAGNOSTIC_DEGRADE
