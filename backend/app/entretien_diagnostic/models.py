from pydantic import BaseModel


class EstimationSurface(BaseModel):
    valeur: float
    unite: str
    a_confirmer: bool = True


class DiagnosticEntretienResultat(BaseModel):
    lieu: str = "exterieur"
    type_espace_cle: str
    type_espace_label: str
    observations_visuelles: str = ""
    categorie: str
    confiance: float
    taches_suggerees: list[str] = []
    estimation_surface: EstimationSurface | None = None
    questions_clarification: list[str] = []
    suggestions_clarification: list[list[str]] = []
    degrade: bool = False
    session_id: str | None = None
