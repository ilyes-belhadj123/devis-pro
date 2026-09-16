from pydantic import BaseModel, Field


class EstimationSurfaceInput(BaseModel):
    valeur: float
    unite: str


class GenererDevisInput(BaseModel):
    compte_id: str = "demo"
    lieu: str = "exterieur"
    categorie: str
    taches_suggerees: list[str] = []
    estimation_surface: EstimationSurfaceInput | None = None


class LigneDevisEntretien(BaseModel):
    designation: str
    categorie: str
    unite: str
    prix_unitaire: float = Field(ge=0)
    quantite: float = Field(ge=0)
    sous_total: float = Field(ge=0)


class FormuleDevis(BaseModel):
    niveau: str
    label: str
    description: str
    lignes: list[LigneDevisEntretien]
    total: float


class DevisEntretienGenere(BaseModel):
    compte_id: str
    categorie: str
    formules: list[FormuleDevis]
    ajustements_appris: list[str] = []


class LigneDevisEntretienInput(BaseModel):
    designation: str
    categorie: str
    unite: str
    prix_unitaire: float = Field(ge=0)
    quantite: float = Field(ge=0)


class ContratRecurrentInput(BaseModel):
    lignes: list[LigneDevisEntretienInput]
    frequence: str
    duree_mois: int = Field(default=12, ge=1)


class ContratRecurrentGenere(BaseModel):
    frequence: str
    frequence_label: str
    duree_mois: int
    interventions_an: int
    prix_intervention_ponctuel: float
    prix_intervention_contrat: float
    prix_annuel: float
    prix_mensuel: float
    economie_pourcentage: float


class ComparateurInput(BaseModel):
    designation: str
    prix_actuel: float = Field(ge=0)


class FournisseurComparateur(BaseModel):
    nom: str
    prix: float
    moins_cher: bool = False
    delai_livraison: str
    note: float
    nombre_avis: int


class ComparateurResultat(BaseModel):
    designation: str
    fournisseurs: list[FournisseurComparateur]
