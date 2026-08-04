import base64
import json
import re

import httpx

from app.catalogue.seed_data import REGLES_ASSOCIATION
from app.core.database import database
from app.core.runtime_config import get_openrouter_api_key

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELE = "anthropic/claude-sonnet-5"

PROBLEMES_CONNUS = [regle["probleme"] for regle in REGLES_ASSOCIATION]

PROMPT_SYSTEME = (
    "Tu es l'IA de diagnostic de SnapDevis, un service qui analyse une photo d'un probleme de "
    "bricolage (mur, plomberie, fixation, electricite, jardin) pour identifier ce dont le client a "
    "besoin.\n\n"
    "Tu dois choisir UNE valeur parmi cette liste exacte de cles (aucune autre valeur n'est valide) :\n"
    f"{', '.join(PROBLEMES_CONNUS)}\n\n"
    "Reponds UNIQUEMENT avec un objet JSON valide, sans texte autour ni markdown, au format exact :\n"
    '{"probleme_cle": "<une des cles ci-dessus>", "probleme_label": "<description courte du probleme en '
    'francais>", "confiance": <nombre entre 0 et 1>, "questions_clarification": [<0 a 2 questions en '
    "francais si la confiance est inferieure a 0.75, sinon liste vide>]}"
)


class DiagnosticIndisponible(Exception):
    pass


def _extraire_json(texte: str) -> dict:
    correspondance = re.search(r"\{.*\}", texte, re.DOTALL)
    if not correspondance:
        raise DiagnosticIndisponible("Reponse du modele sans JSON exploitable")
    return json.loads(correspondance.group(0))


async def analyser_photo(contenu_image: bytes, content_type: str) -> dict:
    api_key = await get_openrouter_api_key()
    if not api_key:
        raise DiagnosticIndisponible("Cle OpenRouter non configuree")

    image_b64 = base64.b64encode(contenu_image).decode("ascii")

    payload = {
        "model": MODELE,
        "messages": [
            {"role": "system", "content": PROMPT_SYSTEME},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyse cette photo et identifie le probleme a resoudre."},
                    {"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{image_b64}"}},
                ],
            },
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(
                OPENROUTER_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        raise DiagnosticIndisponible(f"Appel OpenRouter en echec : {exc}") from exc

    try:
        contenu_reponse = data["choices"][0]["message"]["content"]
        resultat = _extraire_json(contenu_reponse)
        probleme_cle = resultat["probleme_cle"]
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        raise DiagnosticIndisponible(f"Reponse OpenRouter inattendue : {exc}") from exc

    categorie = "indetermine"
    regle = await database.regles_association.find_one({"probleme": probleme_cle})
    if regle:
        produit = await database.produits.find_one({"reference": regle["references_produits"][0]})
        if produit:
            categorie = produit["categorie"]
    else:
        # cle hors liste : on garde la reponse mais on force une clarification manuelle
        resultat["confiance"] = min(float(resultat.get("confiance", 0.5)), 0.4)
        resultat.setdefault("questions_clarification", [])
        if not resultat["questions_clarification"]:
            resultat["questions_clarification"] = [
                "Pouvez-vous préciser le type de problème (mur, plomberie, fixation, électricité, jardin) ?"
            ]

    return {
        "probleme_cle": probleme_cle,
        "probleme_label": resultat.get("probleme_label", probleme_cle),
        "categorie": categorie,
        "confiance": float(resultat.get("confiance", 0.5)),
        "questions_clarification": resultat.get("questions_clarification", []),
        "degrade": False,
    }
