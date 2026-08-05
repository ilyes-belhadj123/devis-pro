import base64
import json
import unicodedata

import httpx

from app.catalogue.seed_data import REGLES_ASSOCIATION
from app.core.ai_utils import extraire_json
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


async def _categorie_pour_probleme(probleme_cle: str) -> str:
    regle = await database.regles_association.find_one({"probleme": probleme_cle})
    if not regle:
        return "indetermine"
    produit = await database.produits.find_one({"reference": regle["references_produits"][0]})
    return produit["categorie"] if produit else "indetermine"


def _sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")


def _basculer_interieur_exterieur(probleme_cle: str, reponse: str) -> str:
    # reponse libre (pas seulement les suggestions rapides) : on tolere la casse,
    # les accents et quelques synonymes courants plutot qu'une correspondance exacte.
    reponse_normalisee = _sans_accents(reponse.strip().lower())
    est_exterieur = "exterieur" in reponse_normalisee or "dehors" in reponse_normalisee
    est_interieur = "interieur" in reponse_normalisee or "dedans" in reponse_normalisee

    bascule = None
    if est_exterieur and probleme_cle.endswith("_interieur"):
        bascule = probleme_cle.replace("_interieur", "_exterieur")
    elif est_interieur and probleme_cle.endswith("_exterieur"):
        bascule = probleme_cle.replace("_exterieur", "_interieur")
    return bascule if bascule in PROBLEMES_CONNUS else probleme_cle


async def affiner_diagnostic(probleme_cle: str, reponse: str, session: tuple[bytes, str] | None) -> dict:
    if session is not None:
        contenu_image, content_type = session
        try:
            return await analyser_photo(
                contenu_image,
                content_type,
                contexte_clarification=f"Précision apportée par l'utilisateur : {reponse}.",
            )
        except DiagnosticIndisponible:
            pass

    probleme_affine = _basculer_interieur_exterieur(probleme_cle, reponse)
    return {
        "probleme_cle": probleme_affine,
        "probleme_label": f"Diagnostic affiné ({reponse.lower()})",
        "categorie": await _categorie_pour_probleme(probleme_affine),
        "confiance": 0.85,
        "questions_clarification": [],
        "degrade": False,
    }


async def analyser_photo(contenu_image: bytes, content_type: str, contexte_clarification: str | None = None) -> dict:
    api_key = await get_openrouter_api_key()
    if not api_key:
        raise DiagnosticIndisponible("Cle OpenRouter non configuree")

    image_b64 = base64.b64encode(contenu_image).decode("ascii")

    texte_utilisateur = "Analyse cette photo et identifie le probleme a resoudre."
    if contexte_clarification:
        texte_utilisateur += f" {contexte_clarification}"

    payload = {
        "model": MODELE,
        "messages": [
            {"role": "system", "content": PROMPT_SYSTEME},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": texte_utilisateur},
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
        resultat = extraire_json(contenu_reponse)
        probleme_cle = resultat["probleme_cle"]
    except (KeyError, IndexError, json.JSONDecodeError, ValueError) as exc:
        raise DiagnosticIndisponible(f"Reponse OpenRouter inattendue : {exc}") from exc

    categorie = await _categorie_pour_probleme(probleme_cle)
    if categorie == "indetermine":
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
