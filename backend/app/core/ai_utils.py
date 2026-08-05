import json
import re


def extraire_json(texte: str) -> dict:
    """Extrait le premier objet JSON d'une reponse de modele de langage,
    qui repond parfois avec du texte ou du markdown autour du JSON demande."""
    correspondance = re.search(r"\{.*\}", texte, re.DOTALL)
    if not correspondance:
        raise ValueError("Reponse du modele sans JSON exploitable")
    return json.loads(correspondance.group(0))
