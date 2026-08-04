from pydantic import BaseModel


class DiagnosticResultat(BaseModel):
    probleme_cle: str
    probleme_label: str
    categorie: str
    confiance: float
    questions_clarification: list[str]
    degrade: bool = False
