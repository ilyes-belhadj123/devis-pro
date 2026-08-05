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
    "bricolage (mur, plomberie, fixation, electricite, jardin) pour generer un devis chiffre realiste.\n\n"
    "Tu dois choisir UNE valeur parmi cette liste exacte de cles (aucune autre valeur n'est valide) :\n"
    f"{', '.join(PROBLEMES_CONNUS)}\n\n"
    "Pour que le devis final soit concret (de vraies quantites, pas des estimations au hasard), pose des "
    "questions de clarification CHIFFREES tant qu'il te manque des informations essentielles pour dimensionner "
    "le projet : surface en m2 (mur a peindre/reboucher), longueur en metres ou diametre (tuyau, cable), "
    "dimensions en cm (etagere, objet a fixer), nombre d'elements (prises, points lumineux)... Continue a "
    "questionner sur plusieurs echanges si necessaire (evite juste de depasser 4-5 questions au total). Ne "
    "termine (confiance >= 0.75, questions_clarification vide) que lorsque tu as assez d'elements concrets "
    "pour estimer des quantites realistes, pas seulement pour identifier la categorie du probleme.\n\n"
    "Reponds UNIQUEMENT avec un objet JSON valide, sans texte autour ni markdown, au format exact :\n"
    '{"probleme_cle": "<une des cles ci-dessus>", "probleme_label": "<description courte du probleme en '
    'francais>", "confiance": <nombre entre 0 et 1>, "questions_clarification": [<1 a 2 questions chiffrees '
    "en francais si la confiance est inferieure a 0.75, sinon liste vide>]}"
)

PROMPT_QUANTITES_TEMPLATE = (
    "En te basant sur toute la conversation precedente (photo + precisions chiffrees apportees par le "
    "client), estime une quantite realiste pour chacun des produits suivants necessaires pour ce projet "
    "precis :\n{liste_candidats}\n\n"
    "Reponds UNIQUEMENT avec un objet JSON valide du type "
    '{{"quantites": {{"<reference>": <quantite entiere >= 1>, ...}}}}. Inclus obligatoirement toutes les '
    "references listees ci-dessus, avec une quantite d'au moins 1 pour chacune."
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


def _construire_messages_initiaux(content_type: str, contenu_image: bytes) -> list[dict]:
    image_b64 = base64.b64encode(contenu_image).decode("ascii")
    return [
        {"role": "system", "content": PROMPT_SYSTEME},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyse cette photo et identifie le probleme a resoudre."},
                {"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{image_b64}"}},
            ],
        },
    ]


async def _appeler_modele(messages: list[dict]) -> str:
    """Appelle OpenRouter avec l'historique de messages donne, renvoie le texte brut de la reponse."""
    api_key = await get_openrouter_api_key()
    if not api_key:
        raise DiagnosticIndisponible("Cle OpenRouter non configuree")

    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(
                OPENROUTER_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": MODELE, "messages": messages},
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        raise DiagnosticIndisponible(f"Appel OpenRouter en echec : {exc}") from exc

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise DiagnosticIndisponible(f"Reponse OpenRouter inattendue : {exc}") from exc


async def _finaliser_resultat(resultat: dict) -> dict:
    try:
        probleme_cle = resultat["probleme_cle"]
    except KeyError as exc:
        raise DiagnosticIndisponible("Reponse OpenRouter sans probleme_cle") from exc

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


async def analyser_photo(contenu_image: bytes, content_type: str) -> tuple[dict, list[dict]]:
    messages = _construire_messages_initiaux(content_type, contenu_image)

    try:
        texte_reponse = await _appeler_modele(messages)
        resultat_brut = extraire_json(texte_reponse)
    except (json.JSONDecodeError, ValueError) as exc:
        raise DiagnosticIndisponible(f"Reponse OpenRouter inattendue : {exc}") from exc

    messages.append({"role": "assistant", "content": texte_reponse})
    resultat = await _finaliser_resultat(resultat_brut)
    return resultat, messages


async def continuer_conversation(messages: list[dict], reponse_utilisateur: str) -> tuple[dict, list[dict]]:
    messages = [*messages, {"role": "user", "content": f"Précision apportée par le client : {reponse_utilisateur}"}]

    try:
        texte_reponse = await _appeler_modele(messages)
        resultat_brut = extraire_json(texte_reponse)
    except (json.JSONDecodeError, ValueError) as exc:
        raise DiagnosticIndisponible(f"Reponse OpenRouter inattendue : {exc}") from exc

    messages = [*messages, {"role": "assistant", "content": texte_reponse}]
    resultat = await _finaliser_resultat(resultat_brut)
    return resultat, messages


async def affiner_diagnostic(probleme_cle: str, reponse: str, session: dict | None) -> tuple[dict, list[dict] | None]:
    if session is not None and session.get("messages"):
        try:
            return await continuer_conversation(session["messages"], reponse)
        except DiagnosticIndisponible:
            pass

    probleme_affine = _basculer_interieur_exterieur(probleme_cle, reponse)
    resultat = {
        "probleme_cle": probleme_affine,
        "probleme_label": f"Diagnostic affiné ({reponse.lower()})",
        "categorie": await _categorie_pour_probleme(probleme_affine),
        "confiance": 0.85,
        "questions_clarification": [],
        "degrade": False,
    }
    return resultat, None


async def estimer_quantites(session: dict | None, candidats: list[dict]) -> dict[str, int] | None:
    """Estime une quantite par produit a partir de la conversation de diagnostic (mesures,
    dimensions... donnees par le client). Renvoie None si indisponible (repli sur quantite=1)."""
    if session is None or not session.get("messages"):
        return None

    liste_candidats = "\n".join(f"- {c['reference']} : {c['nom']} ({c['unite']})" for c in candidats)
    prompt = PROMPT_QUANTITES_TEMPLATE.format(liste_candidats=liste_candidats)
    messages = [*session["messages"], {"role": "user", "content": prompt}]

    try:
        texte_reponse = await _appeler_modele(messages)
        resultat = extraire_json(texte_reponse)
        quantites_brutes = resultat["quantites"]
    except (DiagnosticIndisponible, json.JSONDecodeError, ValueError, KeyError):
        return None

    references_valides = {c["reference"] for c in candidats}
    quantites: dict[str, int] = {}
    for reference, quantite in quantites_brutes.items():
        if reference not in references_valides:
            continue
        try:
            quantites[reference] = max(1, int(quantite))
        except (TypeError, ValueError):
            continue

    return quantites or None
