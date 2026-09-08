"""Cache en memoire des sessions de diagnostic entretien (photo(s) + historique de conversation).
Instance separee du module bricolage (app/diagnostic/session_store.py) - second module autonome,
meme limitation assumee : suffisant pour un prototype de demo mono-process."""

import uuid

_sessions: dict[str, dict] = {}


def creer_session(photos: list[tuple[bytes, str]]) -> str:
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {"photos": photos, "messages": None}
    return session_id


def recuperer_session(session_id: str) -> dict | None:
    return _sessions.get(session_id)


def mettre_a_jour_messages(session_id: str, messages: list[dict]) -> None:
    if session_id in _sessions:
        _sessions[session_id]["messages"] = messages
