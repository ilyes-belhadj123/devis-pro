"""Cache en memoire des sessions de diagnostic (photo + historique de conversation),
pour permettre un dialogue multi-tours et affiner un devis sans redemander la photo au
client. Suffisant pour un prototype de demo mono-process ; a remplacer par un stockage
partage si l'API tourne un jour en plusieurs instances."""

import uuid

_sessions: dict[str, dict] = {}


def creer_session(contenu: bytes, content_type: str) -> str:
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {"contenu": contenu, "content_type": content_type, "messages": None}
    return session_id


def recuperer_session(session_id: str) -> dict | None:
    return _sessions.get(session_id)


def mettre_a_jour_messages(session_id: str, messages: list[dict]) -> None:
    if session_id in _sessions:
        _sessions[session_id]["messages"] = messages
