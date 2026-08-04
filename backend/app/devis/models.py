from pydantic import BaseModel


class DiagnosticInput(BaseModel):
    probleme: str


class LigneDevis(BaseModel):
    reference: str
    nom: str
    categorie: str
    unite: str
    prix_unitaire: float
    quantite: int
    sous_total: float


class GroupeCategorie(BaseModel):
    categorie: str
    sous_total: float


class DevisGenere(BaseModel):
    probleme: str
    lignes: list[LigneDevis]
    groupes: list[GroupeCategorie]
    total: float
