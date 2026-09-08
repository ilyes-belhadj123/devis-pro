from datetime import datetime

from pydantic import BaseModel, Field

STATUT_EN_ATTENTE = "en_attente_validation"
STATUT_VALIDE = "valide"
STATUT_ENVOYE = "envoye"
STATUT_ACCEPTE = "accepte"


class LigneDevisInput(BaseModel):
    designation: str
    categorie: str
    unite: str
    prix_unitaire: float = Field(ge=0)
    quantite: float = Field(ge=0)


class FormuleInput(BaseModel):
    niveau: str
    label: str
    description: str
    lignes: list[LigneDevisInput]


class CreerDevisValidationInput(BaseModel):
    compte_id: str = "demo"
    categorie: str
    formules: list[FormuleInput]


class ModifierFormulesInput(BaseModel):
    formules: list[FormuleInput]


class AccepterInput(BaseModel):
    niveau_choisi: str


class LigneDevis(BaseModel):
    designation: str
    categorie: str
    unite: str
    prix_unitaire: float = Field(ge=0)
    quantite: float = Field(ge=0)
    sous_total: float = Field(ge=0)


class Formule(BaseModel):
    niveau: str
    label: str
    description: str
    lignes: list[LigneDevis]
    total: float


class DevisValidation(BaseModel):
    id: str
    compte_id: str
    categorie: str
    statut: str
    formules: list[Formule]
    formule_choisie: str | None = None
    cree_le: datetime
    valide_le: datetime | None = None
    envoye_le: datetime | None = None
    accepte_le: datetime | None = None


class DevisValidationResume(BaseModel):
    id: str
    categorie: str
    statut: str
    total_standard: float
    cree_le: datetime
