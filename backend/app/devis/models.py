from datetime import datetime

from pydantic import BaseModel, Field


class DiagnosticInput(BaseModel):
    probleme: str
    session_id: str | None = None


class LigneDevis(BaseModel):
    reference: str
    nom: str
    categorie: str
    unite: str
    prix_unitaire: float = Field(ge=0)
    quantite: int = Field(ge=0)
    sous_total: float = Field(ge=0)


class GroupeCategorie(BaseModel):
    categorie: str
    sous_total: float


class DevisGenere(BaseModel):
    probleme: str
    lignes: list[LigneDevis]
    groupes: list[GroupeCategorie]
    total: float


class LigneDevisPdfInput(BaseModel):
    nom: str
    categorie: str
    unite: str
    prix_unitaire: float = Field(ge=0)
    quantite: float = Field(ge=0)


class DevisPdfInput(BaseModel):
    lignes: list[LigneDevisPdfInput]


class AlternativeInput(BaseModel):
    reference_actuelle: str
    categorie: str
    prix_actuel: float = Field(ge=0)


class AlternativeResultat(BaseModel):
    trouve: bool
    reference: str | None = None
    nom: str | None = None
    prix: float | None = None
    unite: str | None = None


class RepartitionProbleme(BaseModel):
    probleme: str
    nombre: int
    panier_moyen: float


class StatistiquesDevis(BaseModel):
    nombre_sessions: int
    panier_moyen_produit_principal: float
    panier_moyen_devis_complet: float
    delta_moyen: float
    delta_pourcentage: float
    repartition_par_probleme: list[RepartitionProbleme]


class HistoriqueResume(BaseModel):
    session_id: str
    probleme: str
    date: datetime
    total: float
    nombre_lignes: int


class HistoriqueDetail(BaseModel):
    session_id: str
    probleme: str
    date: datetime
    lignes: list[LigneDevis]
    groupes: list[GroupeCategorie]
    total: float
