from pydantic import BaseModel


class DiagnosticResultat(BaseModel):
    probleme_cle: str
    probleme_label: str
    observations_visuelles: str = ""
    categorie: str
    confiance: float
    questions_clarification: list[str]
    degrade: bool = False
    session_id: str | None = None


class AffinerInput(BaseModel):
    session_id: str | None = None
    probleme_cle: str
    reponse: str
