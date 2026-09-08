import base64
import json
import unicodedata

import httpx

from app.core.ai_utils import extraire_json
from app.core.runtime_config import get_openrouter_api_key

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELE = "anthropic/claude-sonnet-5"

# Taxonomie fixe utilisee pour classifier le besoin, independante du catalogue CSV que chaque
# artisan peut importer (TICKET-103) - alignee sur les categories du catalogue de demo pour que
# la generation de devis (epique 3) puisse filtrer le catalogue par categorie.
CATEGORIES_CONNUES = [
    "tonte",
    "taille",
    "desherbage",
    "plantation",
    "evacuation",
    "fertilisation",
    "paillage",
    "traitement",
    "divers",
]

PROMPT_SYSTEME = (
    "Tu es l'IA de diagnostic de SnapDevis Entretien, un service qui analyse une photo d'un espace - "
    "exterieur (pelouse, haie, massif, arbre, allee, facade) ou interieur (hall, local, cage d'escalier, "
    "parking couvert, vitres...) - pour une entreprise d'entretien travaillant principalement en contrats "
    "recurrents (coproprietes, collectivites, bailleurs) - pas pour la creation de jardin sur mesure.\n\n"
    "ETAPE 1 - OBSERVATION VISUELLE (obligatoire, avant toute conclusion) :\n"
    "Determine d'abord si la photo montre un espace INTERIEUR ou EXTERIEUR. Decris ensuite precisement ce que "
    "tu vois : nature de l'espace (pelouse, haie, massif, arbre isole, allee, hall, local...), etat (hauteur "
    "d'herbe, densite de la haie, presence de mauvaises herbes, feuilles mortes, salissures, poussiere...), et "
    "etendue visible. Pour estimer une surface (m2) ou une longueur (metres lineaires), utilise en priorite un "
    "objet de taille connue ou une longueur de reference si le client les a signales dans sa note, sinon des "
    "reperes d'echelle visibles sur la photo (une porte standard environ 80 cm de large, une dalle de terrasse "
    "40x40 ou 50x50 cm, une voiture environ 4,5 m de long, un pas d'adulte environ 70 cm, une brouette environ "
    "1,5 m). Si aucun repere fiable n'est disponible, fais une estimation par defaut prudente et indique-le "
    "clairement (elle sera marquee 'a confirmer' pour que le client puisse la corriger manuellement).\n\n"
    "ETAPE 2 - CLASSIFICATION :\n"
    "Choisis UNE categorie parmi cette liste exacte de cles (aucune autre valeur n'est valide) - cette liste "
    "est actuellement orientee espaces verts, choisis 'divers' si aucune ne correspond a une prestation "
    "d'interieur :\n"
    f"{', '.join(CATEGORIES_CONNUES)}\n\n"
    "ETAPE 3 - TACHES SUGGEREES :\n"
    "Propose 2 a 5 taches concretes et realistes pour cet espace, avec si possible une quantite estimee entre "
    'parentheses (ex: "Tonte de la pelouse (~120 m2)", "Taille de la haie (~18 ml)", "Nettoyage du hall '
    '(~40 m2)").\n\n'
    "ETAPE 4 - CLARIFICATION :\n"
    "Ne pose une question que pour une information necessaire mais reellement impossible a determiner depuis "
    "la photo et la note du client (ex : la photo ne montre qu'une partie de l'espace). Questions CHIFFREES ou "
    "a choix precis uniquement. Si la reponse du client reste vague, repose une question avec des fourchettes "
    "chiffrees plutot que de deviner une valeur arbitraire. Continue sur plusieurs echanges si necessaire (sans "
    "depasser 3-4 questions au total). Ne termine (confiance >= 0.75, questions_clarification vide) que "
    "lorsque tu as assez d'elements pour proposer des taches et une estimation de surface fiables.\n\n"
    "Reponds UNIQUEMENT avec un objet JSON valide, sans texte autour ni markdown, au format exact :\n"
    '{"observations_visuelles": "<ce que tu observes precisement, avec les reperes d\'echelle utilises le cas '
    'echeant>", "lieu": "interieur ou exterieur", "type_espace_cle": "pelouse|haie|massif|arbre|allee|mixte '
    '(ou un court identifiant libre pour un espace interieur, ex: hall|local|cage_escalier|parking_couvert)", '
    '"type_espace_label": "<description courte en francais>", "categorie": "<une des cles ci-dessus>", '
    '"confiance": <nombre entre 0 et 1>, '
    '"taches_suggerees": ["...", ...], "estimation_surface": {"valeur": <nombre>, "unite": "m2 ou ml", '
    '"a_confirmer": <true si aucun repere fiable, false sinon>} ou null si aucune estimation n\'est possible, '
    '"questions_clarification": [<1 a 2 questions chiffrees en francais UNIQUEMENT pour ce qui n\'est pas '
    'deductible, sinon liste vide>], "suggestions_clarification": [<pour CHAQUE question ci-dessus, dans le '
    "meme ordre, une liste de 2 a 4 reponses courtes correspondant aux choix ou fourchettes proposes ; liste "
    "vide [] si la question est ouverte sans choix predefinis. Le tableau doit avoir exactement autant "
    'd\'elements que questions_clarification, dans le meme ordre.>]}'
)


class DiagnosticIndisponible(Exception):
    pass


def _construire_messages_initiaux(photos: list[tuple[bytes, str]], note: str | None = None) -> list[dict]:
    consigne = (
        "Analyse la photo suivante d'un espace vert et identifie les travaux d'entretien necessaires."
        if len(photos) == 1
        else f"Analyse les {len(photos)} photos suivantes (differents angles/zooms du meme espace) et "
        "identifie les travaux d'entretien necessaires."
    )
    if note and note.strip():
        consigne += (
            f" Le client a ajoute cette precision : \"{note.strip()}\". Utilise-la comme un indice "
            "supplementaire (ce n'est pas necessairement visible sur la photo) mais base ta classification "
            "et tes observations en priorite sur ce que tu vois reellement."
        )

    contenu: list[dict] = [{"type": "text", "text": consigne}]
    for image_bytes, content_type in photos:
        image_b64 = base64.b64encode(image_bytes).decode("ascii")
        contenu.append({"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{image_b64}"}})

    return [
        {"role": "system", "content": PROMPT_SYSTEME},
        {"role": "user", "content": contenu},
    ]


async def _appeler_modele(messages: list[dict]) -> str:
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


def _normaliser_suggestions(suggestions_brutes: object, questions: list[str]) -> list[list[str]]:
    suggestions: list[list[str]] = []
    for i in range(len(questions)):
        item = suggestions_brutes[i] if isinstance(suggestions_brutes, list) and i < len(suggestions_brutes) else None
        suggestions.append([str(option) for option in item] if isinstance(item, list) else [])
    return suggestions


def _finaliser_resultat(resultat: dict) -> dict:
    try:
        type_espace_cle = resultat["type_espace_cle"]
    except KeyError as exc:
        raise DiagnosticIndisponible("Reponse OpenRouter sans type_espace_cle") from exc

    categorie = resultat.get("categorie", "divers")
    questions = resultat.get("questions_clarification", [])
    confiance = float(resultat.get("confiance", 0.5))

    if categorie not in CATEGORIES_CONNUES:
        # categorie hors liste : on garde la reponse mais on force une clarification manuelle
        categorie = "divers"
        confiance = min(confiance, 0.4)
        if not questions:
            questions = ["Pouvez-vous préciser le type de prestation (tonte, taille, désherbage, plantation...) ?"]

    estimation_brute = resultat.get("estimation_surface")
    estimation_surface = None
    if isinstance(estimation_brute, dict) and "valeur" in estimation_brute and "unite" in estimation_brute:
        try:
            estimation_surface = {
                "valeur": float(estimation_brute["valeur"]),
                "unite": str(estimation_brute["unite"]),
                "a_confirmer": bool(estimation_brute.get("a_confirmer", True)),
            }
        except (TypeError, ValueError):
            estimation_surface = None

    lieu = resultat.get("lieu")
    if lieu not in ("interieur", "exterieur"):
        lieu = "exterieur"

    return {
        "lieu": lieu,
        "type_espace_cle": type_espace_cle,
        "type_espace_label": resultat.get("type_espace_label", type_espace_cle),
        "observations_visuelles": resultat.get("observations_visuelles", ""),
        "categorie": categorie,
        "confiance": confiance,
        "taches_suggerees": [str(tache) for tache in resultat.get("taches_suggerees", [])],
        "estimation_surface": estimation_surface,
        "questions_clarification": questions,
        "suggestions_clarification": _normaliser_suggestions(resultat.get("suggestions_clarification"), questions),
        "degrade": False,
    }


async def analyser_photo(photos: list[tuple[bytes, str]], note: str | None = None) -> tuple[dict, list[dict]]:
    messages = _construire_messages_initiaux(photos, note)

    try:
        texte_reponse = await _appeler_modele(messages)
        resultat_brut = extraire_json(texte_reponse)
    except (json.JSONDecodeError, ValueError) as exc:
        raise DiagnosticIndisponible(f"Reponse OpenRouter inattendue : {exc}") from exc

    messages.append({"role": "assistant", "content": texte_reponse})
    resultat = _finaliser_resultat(resultat_brut)
    return resultat, messages


async def continuer_conversation(messages: list[dict], reponse_utilisateur: str) -> tuple[dict, list[dict]]:
    nouveau_message = {"role": "user", "content": f"Précision apportée par le client : {reponse_utilisateur}"}
    messages = [*messages, nouveau_message]

    try:
        texte_reponse = await _appeler_modele(messages)
        resultat_brut = extraire_json(texte_reponse)
    except (json.JSONDecodeError, ValueError) as exc:
        raise DiagnosticIndisponible(f"Reponse OpenRouter inattendue : {exc}") from exc

    messages = [*messages, {"role": "assistant", "content": texte_reponse}]
    resultat = _finaliser_resultat(resultat_brut)
    return resultat, messages


def _sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")


def _basculer_lieu(lieu_actuel: str, reponse: str) -> str:
    # reponse libre : on tolere la casse, les accents et quelques synonymes courants plutot
    # qu'une correspondance exacte (comme dans le module bricolage).
    reponse_normalisee = _sans_accents(reponse.strip().lower())
    if "exterieur" in reponse_normalisee or "dehors" in reponse_normalisee:
        return "exterieur"
    if "interieur" in reponse_normalisee or "dedans" in reponse_normalisee:
        return "interieur"
    return lieu_actuel


async def affiner_diagnostic(
    lieu: str,
    type_espace_cle: str,
    categorie: str,
    reponse: str,
    session: dict | None,
) -> tuple[dict, list[dict] | None]:
    if session is not None and session.get("messages"):
        try:
            return await continuer_conversation(session["messages"], reponse)
        except DiagnosticIndisponible:
            pass

    resultat = {
        "lieu": _basculer_lieu(lieu, reponse),
        "type_espace_cle": type_espace_cle,
        "type_espace_label": f"Diagnostic affiné ({reponse.lower()})",
        "observations_visuelles": "",
        "categorie": categorie if categorie in CATEGORIES_CONNUES else "divers",
        "confiance": 0.7,
        "taches_suggerees": [],
        "estimation_surface": None,
        "questions_clarification": [],
        "suggestions_clarification": [],
        "degrade": False,
    }
    return resultat, None
