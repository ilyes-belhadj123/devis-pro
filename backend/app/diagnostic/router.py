from fastapi import APIRouter, File, Form, UploadFile

from app.diagnostic.models import AffinerInput, DiagnosticResultat
from app.diagnostic.service import DiagnosticIndisponible, affiner_diagnostic, analyser_photo
from app.diagnostic.session_store import creer_session, mettre_a_jour_messages, recuperer_session

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


@router.post("/analyser", response_model=DiagnosticResultat)
async def analyser(photos: list[UploadFile] = File(...), note: str | None = Form(None)) -> DiagnosticResultat:
    photos_contenu = [(await photo.read(), photo.content_type or "image/jpeg") for photo in photos]
    session_id = creer_session(photos_contenu)

    try:
        resultat, messages = await analyser_photo(photos_contenu, note)
        mettre_a_jour_messages(session_id, messages)
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
    resultat, messages = await affiner_diagnostic(payload.probleme_cle, payload.reponse, session)
    if messages is not None and payload.session_id:
        mettre_a_jour_messages(payload.session_id, messages)
    return DiagnosticResultat(**resultat, session_id=payload.session_id)
