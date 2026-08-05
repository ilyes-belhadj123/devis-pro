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

PROMPT_CRITERES_PAR_CATEGORIE = (
    "CRITERES CLES PAR CATEGORIE (utilise ceux pertinents pour orienter tes observations et tes questions, "
    "dans cet ordre de priorite) :\n"
    "- peinture (mur a peindre/reboucher) : surface totale en m2, nombre de couches necessaires selon l'etat "
    "actuel, fissure(s) active(s) (bords nets, recente, traverse un enduit/peinture intact) vs stable(s) "
    "(bords erodes, ancienne peinture craquelee par-dessus), traces d'humidite ou de moisissure visibles.\n"
    "- plomberie (fuite, robinet, siphon) : emplacement precis de la fuite (joint, corps du robinet, raccord, "
    "canalisation), materiau visible du tuyau (cuivre, PVC, multicouche), diametre approximatif, fuite "
    "continue ou seulement a l'usage.\n"
    "- fixation (etagere, objet a fixer, cadre) : poids approximatif et dimensions de l'objet a fixer, type de "
    "mur visible (placo/BA13 blanc uniforme, beton brut gris, brique, parpaing/agglo), fixations existantes "
    "deja en place.\n"
    "- electricite (prise, interrupteur, eclairage) : remplacement a l'identique ou nouvelle installation, "
    "arrivee/gaine deja visible ou a creer, nombre de points concernes.\n"
    "- jardin (terrain, plantation, arrosage) : surface approximative de la zone concernee, type de sol "
    "visible (terre nue, gazon, gravier, dallage), exposition si deductible de la luminosite/ombre.\n\n"
)

PROMPT_SYSTEME = (
    "Tu es l'IA de diagnostic de SnapDevis, un service qui analyse une photo d'un probleme de "
    "bricolage (mur, plomberie, fixation, electricite, jardin) pour generer un devis chiffre realiste.\n\n"
    + PROMPT_CRITERES_PAR_CATEGORIE
    + "ETAPE 1 - OBSERVATION VISUELLE (obligatoire, avant toute conclusion) :\n"
    "Examine la photo en detail et decris precisement ce que tu vois reellement, sans supposer ce que tu ne "
    "peux pas voir : nature et etat du support/materiau, etendue visible du probleme (longueur/surface/nombre "
    "d'elements estimes a partir d'objets de reference visibles dans le cadre - une prise de courant fait "
    "environ 8x8 cm, une porte standard environ 80 cm de large, un carrelage courant 30x30 cm ou 60x60 cm, une "
    "brique environ 22 cm de long), les criteres cles de la categorie probable (voir liste ci-dessus), et tout "
    "indice de contexte (interieur/exterieur, piece, luminosite). Base tes estimations sur ces reperes plutot "
    "que de deviner au hasard. Si aucun repere d'echelle n'est visible, dis-le explicitement plutot que "
    "d'inventer une mesure.\n\n"
    "ETAPE 2 - CLASSIFICATION :\n"
    "Choisis UNE valeur parmi cette liste exacte de cles (aucune autre valeur n'est valide) :\n"
    f"{', '.join(PROBLEMES_CONNUS)}\n\n"
    "ETAPE 3 - CLARIFICATION :\n"
    "Ne pose une question au client QUE pour une information necessaire au devis mais reellement impossible a "
    "determiner depuis la photo (ex : la photo ne montre qu'un coin du mur, la surface totale de la piece "
    "n'est pas visible). Priorise les criteres cles de la categorie concernee (liste ci-dessus) pour choisir "
    "quoi demander. Si tu peux estimer une mesure a partir d'un repere visuel, utilise cette estimation au "
    "lieu de demander - precise alors dans probleme_label que c'est une estimation visuelle. Les questions "
    "doivent rester CHIFFREES ou a choix precis (surface en m2, longueur en metres, dimensions en cm, nombre "
    "d'elements, materiau parmi une liste courte). Si la reponse du client reste vague ou imprecise (ex : "
    "\"assez grand\", \"une taille normale\", \"je ne sais pas trop\"), NE DEVINE PAS un chiffre a sa place : "
    "repose une question plus precise avec des fourchettes chiffrees a choisir (ex : \"moins de 5 m2, entre 5 "
    "et 15 m2, ou plus de 15 m2 ?\") plutot que d'assumer une valeur arbitraire qui faussera le devis. Continue "
    "sur plusieurs echanges si necessaire (sans depasser 4-5 questions au total). Ne termine (confiance >= "
    "0.75, questions_clarification vide) que lorsque tu as assez d'elements fiables - observes ou obtenus par "
    "tes questions - pour estimer des quantites realistes.\n\n"
    "PRINCIPE GENERAL : une quantite surestimee fait payer au client du materiel dont il n'a pas besoin ; une "
    "quantite sous-estimee l'obligera a revenir en acheter plus (perte de temps et d'argent, mauvaise "
    "experience). Prends le temps necessaire pour obtenir des donnees fiables plutot que de conclure trop vite "
    "sur des hypotheses non verifiees.\n\n"
    "Reponds UNIQUEMENT avec un objet JSON valide, sans texte autour ni markdown, au format exact :\n"
    '{"observations_visuelles": "<ce que tu observes precisement sur la photo, avec les reperes d\'echelle '
    'utilises le cas echeant>", "probleme_cle": "<une des cles ci-dessus>", "probleme_label": "<description '
    'courte du probleme en francais>", "confiance": <nombre entre 0 et 1>, "questions_clarification": [<1 a 2 '
    "questions chiffrees en francais UNIQUEMENT pour ce qui n'est pas deductible de la photo, sinon liste "
    "vide>]}"
)

PROMPT_MATERIEL_TEMPLATE = (
    "En te basant sur toute la conversation precedente (photo + precisions chiffrees apportees par le "
    "client), selectionne dans le catalogue suivant UNIQUEMENT les produits reellement necessaires pour "
    "resoudre ce probleme precis, avec une quantite realiste pour chacun :\n{catalogue}\n\n"
    "Ne selectionne pas systematiquement tout le catalogue : seulement ce qui est pertinent pour ce cas "
    "precis, en te basant sur les mesures/quantites discutees.\n\n"
    "CALCUL DES QUANTITES - base-toi sur des taux de couverture/usage reels et connus, pas des chiffres "
    "arbitraires. Exemples de reference : un pot de peinture standard (2.5L) couvre environ 10 a 12 m2 par "
    "couche (2 couches necessaires si le support est neuf, rebouche, ou de couleur tres differente) ; un pot "
    "d'enduit de rebouchage (1kg) traite environ 1 a 2 m2 de petites fissures ; un tube de silicone/mastic "
    "traite environ 3 a 4 metres lineaires de joint ; une boite de vis/chevilles standard convient pour "
    "plusieurs petites fixations (pas besoin d'une boite entiere par fixation). Applique une marge de "
    "securite minimale et raisonnable (5 a 10%) uniquement pour les consommables ou les chutes/erreurs sont "
    "normales (peinture, enduit) - jamais une quantite gonflee sans justification. Chaque unite superflue est "
    "de l'argent depense en trop par le client ; chaque unite manquante l'oblige a un aller-retour couteux. "
    "Si les informations disponibles restent insuffisantes pour calculer une quantite fiable pour un produit, "
    "ne l'inclus pas plutot que de deviner.\n\n"
    "Reponds UNIQUEMENT avec un objet JSON valide "
    'du type {{"produits": [{{"reference": "<reference du catalogue>", "quantite": <entier >= 1>}}, ...]}}. '
    "Selectionne au moins 1 produit et au maximum 6."
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
        "observations_visuelles": resultat.get("observations_visuelles", ""),
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
        "observations_visuelles": "",
        "categorie": await _categorie_pour_probleme(probleme_affine),
        "confiance": 0.85,
        "questions_clarification": [],
        "degrade": False,
    }
    return resultat, None


async def selectionner_materiel(session: dict | None, catalogue: list[dict]) -> list[dict] | None:
    """Laisse l'IA choisir, dans le catalogue de la categorie concernee, les produits
    reellement necessaires (et leur quantite) a partir de toute la conversation de
    diagnostic (mesures, dimensions...). Renvoie None si indisponible (repli sur la
    regle d'association fixe, quantite=1)."""
    if session is None or not session.get("messages") or not catalogue:
        return None

    liste_catalogue = "\n".join(f"- {p['reference']} : {p['nom']} ({p['prix']:.2f} €, {p['unite']})" for p in catalogue)
    prompt = PROMPT_MATERIEL_TEMPLATE.format(catalogue=liste_catalogue)
    messages = [*session["messages"], {"role": "user", "content": prompt}]

    try:
        texte_reponse = await _appeler_modele(messages)
        resultat = extraire_json(texte_reponse)
        selection_brute = resultat["produits"]
    except (DiagnosticIndisponible, json.JSONDecodeError, ValueError, KeyError):
        return None

    catalogue_par_reference = {p["reference"]: p for p in catalogue}
    materiel: list[dict] = []
    for item in selection_brute:
        try:
            reference = item["reference"]
            quantite = max(1, int(item["quantite"]))
        except (KeyError, TypeError, ValueError):
            continue
        produit = catalogue_par_reference.get(reference)
        if produit is None:
            continue
        materiel.append({**produit, "quantite": quantite})

    return materiel or None
