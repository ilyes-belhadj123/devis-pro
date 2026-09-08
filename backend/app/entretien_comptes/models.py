from datetime import datetime

from pydantic import BaseModel

COMPTE_DEMO_ID = "demo"
NOM_COMPTE_DEMO = "Verdura Paysage"


class CompteArtisan(BaseModel):
    id: str
    nom: str
    cree_le: datetime
