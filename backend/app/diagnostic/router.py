import json

from fastapi import APIRouter, File, Form, UploadFile

from app.diagnostic.models import DiagnosticResultat
from app.diagnostic.service import DiagnosticIndisponible, affiner_diagnostic, analyser_photo
from app.diagnostic.session_store import creer_session, mettre_a_jour_messages, recuperer_session

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


@router.post("/analyser", response_model=DiagnosticResultat)
async def analyser(
    photos: list[UploadFile] = File(...),
    note: str | None = Form(None),
    points: str | None = Form(None),
) -> DiagnosticResultat:
    photos_contenu = [(await photo.read(), photo.content_type or "image/jpeg") for photo in photos]
    session_id = creer_session(photos_contenu)

    points_reperage: list[dict] | None = None
    if points:
        try:
            points_reperage = json.loads(points)
        except (json.JSONDecodeError, TypeError):
            points_reperage = None

    try:
        resultat, messages = await analyser_photo(photos_contenu, note, points_reperage)
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
async def affiner(
    probleme_cle: str = Form(...),
    reponse: str = Form(...),
    session_id: str | None = Form(None),
    photos: list[UploadFile] = File(default=[]),
) -> DiagnosticResultat:
    session = recuperer_session(session_id) if session_id else None
    nouvelles_photos = [(await photo.read(), photo.content_type or "image/jpeg") for photo in photos]
    resultat, messages = await affiner_diagnostic(probleme_cle, reponse, session, nouvelles_photos or None)
    if messages is not None and session_id:
        mettre_a_jour_messages(session_id, messages)
    return DiagnosticResultat(**resultat, session_id=session_id)
