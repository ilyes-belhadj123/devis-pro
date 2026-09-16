from pydantic import BaseModel


class ZoneDetectee(BaseModel):
    photo_index: int = 0
    x: float
    y: float
    largeur: float
    hauteur: float
    label: str = ""


class DiagnosticResultat(BaseModel):
    probleme_cle: str
    probleme_label: str
    observations_visuelles: str = ""
    categorie: str
    confiance: float
    questions_clarification: list[str]
    suggestions_clarification: list[list[str]] = []
    zones_detectees: list[ZoneDetectee] = []
    degrade: bool = False
    session_id: str | None = None
