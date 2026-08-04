from pydantic import BaseModel


class Produit(BaseModel):
    reference: str
    nom: str
    categorie: str
    prix: float
    unite: str


class RegleAssociation(BaseModel):
    probleme: str
    references_produits: list[str]
