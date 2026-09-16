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
    "tu vois : nature de l'espace (pelouse, haie, massif, arbre isole, allee, hall, local...), et etendue "
    "visible. Pour estimer une surface (m2) ou une longueur (metres lineaires), utilise en priorite un objet de "
    "taille connue ou une longueur de reference si le client les a signales dans sa note, sinon des reperes "
    "d'echelle visibles sur la photo - exterieur : une porte standard environ 80 cm de large, une dalle de "
    "terrasse 40x40 ou 50x50 cm, une voiture environ 4,5 m de long, un pas d'adulte environ 70 cm, une brouette "
    "environ 1,5 m, une cloture/palissade standard environ 1,80 m de haut, un bac/poubelle roulant environ 1 m "
    "de haut ; interieur : une porte standard environ 80 cm de large et 2 m de haut, un interrupteur environ "
    "8x8 cm a 1,10 m du sol, un carrelage 30x30 ou 60x60 cm. Si aucun repere fiable n'est disponible, fais une "
    "estimation par defaut prudente et indique-le clairement (elle sera marquee 'a confirmer' pour que le "
    "client puisse la corriger manuellement).\n\n"
    "ETAT DE L'ESPACE - classe ce que tu observes sur une echelle concrete plutot qu'une description vague, "
    "cela oriente directement les taches et leur ampleur :\n"
    "- hauteur d'herbe : tondue recemment (<5 cm), pousse moderee (5 a 15 cm, tonte standard), haute/negligee "
    "(>15 cm, necessite un premier passage renforce ou un debroussaillage avant une tonte normale).\n"
    "- envahissement par les mauvaises herbes : leger (<10% de la surface), modere (10 a 40%), important (>40%, "
    "necessite un desherbage approfondi a part entiere, pas une simple finition).\n"
    "- etat de la haie : entretenue (forme nette, pousse depuis le dernier passage <20 cm) vs negligee (forme "
    "irreguliere, pousse >40 cm, taille plus consequente et plus longue a prevoir).\n"
    "- proprete d'un espace interieur : entretien courant (poussiere legere) vs salissures marquees/tenaces "
    "(necessite un nettoyage renforce, pas un simple depoussierage).\n\n"
    "ETAPE 2 - CLASSIFICATION :\n"
    "Choisis UNE categorie parmi cette liste exacte de cles (aucune autre valeur n'est valide) - cette liste "
    "est actuellement orientee espaces verts, choisis 'divers' si aucune ne correspond a une prestation "
    "d'interieur :\n"
    f"{', '.join(CATEGORIES_CONNUES)}\n\n"
    "ETAPE 3 - TACHES SUGGEREES :\n"
    "Propose 2 a 5 taches concretes et realistes pour cet espace, avec si possible une quantite estimee entre "
    'parentheses (ex: "Tonte de la pelouse (~120 m2)", "Taille de la haie (~18 ml)", "Nettoyage du hall '
    '(~40 m2)"). Les taches doivent refleter l\'etat reellement observe (etape precedente) : un espace "haute/'
    'negligee" ou "important" justifie une tache renforcee ou prealable (debroussaillage, desherbage approfondi) '
    "en plus de l'entretien standard, pas seulement la tache habituelle comme si l'espace etait deja entretenu.\n\n"
    "ETAPE 3BIS - LOCALISATION VISUELLE (radar de zones) :\n"
    "Pour chaque zone precise et visible necessitant une intervention distincte (une zone de mauvaises herbes, "
    "une branche morte, une partie de haie particulierement degradee, une tache/salissure marquee...), donne un "
    "rectangle englobant resserre sur cette zone, en coordonnees normalisees par rapport a CETTE photo (0 = "
    "bord gauche/haut, 1 = bord droit/bas) : x et y = coin superieur gauche, largeur et hauteur = dimensions. "
    "N'en mets QUE si tu peux reellement pointer une zone precise depuis l'image (pas pour une tache generale "
    "comme 'tondre toute la pelouse' qui concerne l'espace entier). Maximum 4 zones.\n\n"
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
    'd\'elements que questions_clarification, dans le meme ordre.>], "zones_detectees": [{"photo_index": <index '
    'de la photo concernee, 0 pour la premiere>, "x": <0 a 1>, "y": <0 a 1>, "largeur": <0 a 1>, "hauteur": '
    '<0 a 1>, "label": "<description courte, ex: \'zone envahie\', \'branche morte\'>"}, ...] (liste vide si '
    "aucune zone n'est localisable precisement)}"
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


def _normaliser_zones(zones_brutes: object) -> list[dict]:
    """Valide et nettoie les zones detectees par l'IA (radar visuel) : coordonnees bornees a
    [0, 1], entrees mal formees ignorees plutot que de faire planter toute la reponse."""
    if not isinstance(zones_brutes, list):
        return []

    zones: list[dict] = []
    for item in zones_brutes[:4]:
        if not isinstance(item, dict):
            continue
        try:
            x = max(0.0, min(1.0, float(item["x"])))
            y = max(0.0, min(1.0, float(item["y"])))
            largeur = max(0.02, min(1.0 - x, float(item["largeur"])))
            hauteur = max(0.02, min(1.0 - y, float(item["hauteur"])))
        except (KeyError, TypeError, ValueError):
            continue
        try:
            photo_index = max(0, int(item.get("photo_index", 0)))
        except (TypeError, ValueError):
            photo_index = 0
        zones.append(
            {
                "photo_index": photo_index,
                "x": round(x, 4),
                "y": round(y, 4),
                "largeur": round(largeur, 4),
                "hauteur": round(hauteur, 4),
                "label": str(item.get("label", ""))[:60],
            }
        )
    return zones


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
        "zones_detectees": _normaliser_zones(resultat.get("zones_detectees")),
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
