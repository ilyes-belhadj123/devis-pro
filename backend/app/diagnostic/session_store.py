"""Cache en memoire des photos par session, pour permettre d'affiner un
diagnostic (question de clarification) sans redemander la photo au client.
Suffisant pour un prototype de demo mono-process ; a remplacer par un
stockage partage si l'API tourne un jour en plusieurs instances."""

import uuid

_sessions: dict[str, tuple[bytes, str]] = {}


def creer_session(contenu: bytes, content_type: str) -> str:
    session_id = str(uuid.uuid4())
    _sessions[session_id] = (contenu, content_type)
    return session_id


def recuperer_session(session_id: str) -> tuple[bytes, str] | None:
    return _sessions.get(session_id)
