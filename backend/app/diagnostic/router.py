from fastapi import APIRouter, File, UploadFile

from app.diagnostic.models import AffinerInput, DiagnosticResultat
from app.diagnostic.service import DiagnosticIndisponible, affiner_diagnostic, analyser_photo
from app.diagnostic.session_store import creer_session, recuperer_session

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


@router.post("/analyser", response_model=DiagnosticResultat)
async def analyser(photo: UploadFile = File(...)) -> DiagnosticResultat:
    contenu = await photo.read()
    content_type = photo.content_type or "image/jpeg"
    session_id = creer_session(contenu, content_type)

    try:
        resultat = await analyser_photo(contenu, content_type)
        return DiagnosticResultat(**resultat, session_id=session_id)
    except DiagnosticIndisponible:
        return DiagnosticResultat(
            probleme_cle="mur_fissure_interieur",
            probleme_label="Mur fissuré intérieur (diagnostic simulé — service IA indisponible)",
            categorie="peinture",
            confiance=0.5,
            questions_clarification=[],
            degrade=True,
            session_id=session_id,
        )


@router.post("/affiner", response_model=DiagnosticResultat)
async def affiner(payload: AffinerInput) -> DiagnosticResultat:
    session = recuperer_session(payload.session_id) if payload.session_id else None
    resultat = await affiner_diagnostic(payload.probleme_cle, payload.reponse, session)
    return DiagnosticResultat(**resultat, session_id=payload.session_id)
