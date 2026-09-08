from fastapi import APIRouter, File, Form, UploadFile

from app.entretien_diagnostic.models import DiagnosticEntretienResultat
from app.entretien_diagnostic.service import DiagnosticIndisponible, affiner_diagnostic, analyser_photo
from app.entretien_diagnostic.session_store import creer_session, mettre_a_jour_messages, recuperer_session

router = APIRouter(prefix="/entretien/diagnostic", tags=["entretien-diagnostic"])


@router.post("/analyser", response_model=DiagnosticEntretienResultat)
async def analyser(
    photos: list[UploadFile] = File(...),
    note: str | None = Form(None),
) -> DiagnosticEntretienResultat:
    photos_contenu = [(await photo.read(), photo.content_type or "image/jpeg") for photo in photos]
    session_id = creer_session(photos_contenu)

    try:
        resultat, messages = await analyser_photo(photos_contenu, note)
        mettre_a_jour_messages(session_id, messages)
        return DiagnosticEntretienResultat(**resultat, session_id=session_id)
    except DiagnosticIndisponible:
        return DiagnosticEntretienResultat(
            lieu="exterieur",
            type_espace_cle="pelouse",
            type_espace_label="Pelouse (diagnostic simulé — service IA indisponible)",
            categorie="tonte",
            confiance=0.5,
            taches_suggerees=["Tonte de pelouse"],
            questions_clarification=[],
            degrade=True,
            session_id=session_id,
        )


@router.post("/affiner", response_model=DiagnosticEntretienResultat)
async def affiner(
    lieu: str = Form(...),
    type_espace_cle: str = Form(...),
    categorie: str = Form(...),
    reponse: str = Form(...),
    session_id: str | None = Form(None),
) -> DiagnosticEntretienResultat:
    session = recuperer_session(session_id) if session_id else None
    resultat, messages = await affiner_diagnostic(lieu, type_espace_cle, categorie, reponse, session)
    if messages is not None and session_id:
        mettre_a_jour_messages(session_id, messages)
    return DiagnosticEntretienResultat(**resultat, session_id=session_id)
