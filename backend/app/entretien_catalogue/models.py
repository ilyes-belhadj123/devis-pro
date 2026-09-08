from pydantic import BaseModel, Field


class ProduitEntretien(BaseModel):
    designation: str
    unite: str
    prix: float = Field(ge=0)
    categorie: str
