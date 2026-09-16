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
    "actuel, traces d'humidite ou de moisissure visibles. Classe la ou les fissures par largeur estimee : "
    "fine/capillaire (<0,2mm, cosmetique, un enduit de finition fin suffit), moyenne (0,2 a 2mm, necessite un "
    "vrai enduit de rebouchage), large ou traversante (>2mm, ou qui traverse un enduit/une peinture par ailleurs "
    "intacte = fissure active) : dans ce dernier cas, signale-le clairement dans probleme_label comme un cas "
    "potentiellement structurel a faire verifier, plutot que de proposer un simple rebouchage cosmetique.\n"
    "- plomberie (fuite, robinet, siphon) : emplacement precis de la fuite (joint, corps du robinet, raccord, "
    "canalisation), materiau visible du tuyau (cuivre, PVC, multicouche), diametre approximatif. Classe la fuite "
    "par gravite : suintement/traces d'humidite seulement (goutte a goutte occasionnel), fuite reguliere a "
    "l'usage (quand le robinet/l'appareil fonctionne), ou fuite continue meme a l'arret (la plus urgente, "
    "risque dexces d'eau) - cette classification oriente l'urgence et le type d'intervention a suggerer.\n"
    "- fixation (etagere, objet a fixer, cadre) : dimensions de l'objet a fixer et type de mur visible "
    "(placo/BA13 blanc uniforme, beton brut gris, brique, parpaing/agglo), fixations existantes deja en place. "
    "Classe le poids estime de l'objet (a partir de sa taille/matiere apparente) : leger (<5kg, type cadre ou "
    "petite etagere - chevilles standard), moyen (5 a 20kg, type etagere chargee ou miroir - chevilles a "
    "expansion/molly), lourd (>20kg, type meuble suspendu ou television - fixations traversantes/renforcees "
    "necessaires) : cette classe determine le type de fixation a prevoir, pas seulement la quantite.\n"
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
    "Examine la ou les photos fournies en detail et decris precisement ce que tu vois reellement, sans "
    "supposer ce que tu ne peux pas voir. Si plusieurs photos sont fournies, elles peuvent montrer differents "
    "angles ou zooms du meme probleme : combine les informations de toutes les photos avant de conclure plutot "
    "que de n'en analyser qu'une seule. Decris : nature et etat du support/materiau, etendue visible du probleme (longueur/surface/nombre "
    "d'elements estimes a partir d'objets de reference visibles dans le cadre - une prise de courant ou un "
    "interrupteur fait environ 8x8 cm (a environ 1,10 m du sol pour un interrupteur), une porte standard environ "
    "80 cm de large et 2 m de haut, un carrelage courant 30x30 cm ou 60x60 cm, une brique environ 22 cm de long, "
    "une plinthe environ 10 cm de haut, un radiateur standard environ 60 cm de large, un evier de cuisine "
    "standard environ 60 cm de large), les criteres cles de la categorie probable (voir liste ci-dessus), et "
    "tout indice de contexte (interieur/exterieur, piece, luminosite). Base tes estimations sur ces reperes "
    "plutot que de deviner au hasard. Si aucun repere d'echelle n'est visible, dis-le explicitement plutot que "
    "d'inventer une mesure. Avant de conclure, verifie la coherence de ton diagnostic : les taches/quantites "
    "envisagees doivent correspondre a la gravite reellement observee (ex : une fissure large ou une fuite "
    "continue meritent d'etre signalees comme telles, pas traitees comme un cas mineur standard).\n\n"
    "ETAPE 2 - CLASSIFICATION :\n"
    "Choisis UNE valeur parmi cette liste exacte de cles (aucune autre valeur n'est valide) :\n"
    f"{', '.join(PROBLEMES_CONNUS)}\n\n"
    "ETAPE 2BIS - LOCALISATION VISUELLE DU DEFAUT (radar de zones) :\n"
    "Pour chaque defaut precis et visible sur une photo (une fissure, une trace de fuite, un point de rouille, "
    "l'endroit exact a fixer...), donne un rectangle englobant resserre sur ce defaut, en coordonnees "
    "normalisees par rapport a CETTE photo (0 = bord gauche/haut, 1 = bord droit/bas) : x et y = coin superieur "
    "gauche du rectangle, largeur et hauteur = ses dimensions. Un defaut allonge (fissure) doit avoir un "
    "rectangle allonge dans le meme sens, pas un carre autour de toute la photo. N'en mets QUE si tu peux "
    "reellement pointer une zone precise depuis l'image ; si le defaut n'est decrit que par le texte du client "
    "et non visible sur la photo, ne l'ajoute pas a cette liste. Maximum 4 zones.\n\n"
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
    'vide>], "suggestions_clarification": [<pour CHAQUE question ci-dessus, dans le meme ordre, une liste de 2 '
    "a 4 reponses courtes et concretes correspondant exactement aux choix ou fourchettes proposes dans cette "
    'question (exemple pour la question "moins de 5 m2, entre 5 et 15 m2, ou plus de 15 m2 ?" : ["moins de 5 '
    'm2", "entre 5 et 15 m2", "plus de 15 m2"]) ; liste vide [] si cette question precise est ouverte sans '
    "choix predefinis. Le tableau suggestions_clarification doit avoir exactement autant d'elements que "
    'questions_clarification, dans le meme ordre.>], "zones_detectees": [{"photo_index": <index de la photo '
    "concernee, 0 pour la premiere>, \"x\": <0 a 1>, \"y\": <0 a 1>, \"largeur\": <0 a 1>, \"hauteur\": <0 a 1>, "
    '"label": "<description courte du defaut, ex: \'fissure\', \'trace de fuite\'>"}, ...] (liste vide si aucun '
    "defaut n'est localisable precisement sur une photo)}"
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


def _construire_messages_initiaux(
    photos: list[tuple[bytes, str]],
    note: str | None = None,
    points: list[dict] | None = None,
) -> list[dict]:
    consigne = (
        "Analyse la photo suivante et identifie le probleme a resoudre."
        if len(photos) == 1
        else f"Analyse les {len(photos)} photos suivantes (differents angles/zooms du meme probleme) et "
        "identifie le probleme a resoudre."
    )
    if note and note.strip():
        consigne += (
            f" Le client a ajoute cette precision : \"{note.strip()}\". Utilise-la comme un indice "
            "supplementaire (ce n'est pas necessairement visible sur la photo) mais base ta classification "
            "et tes observations en priorite sur ce que tu vois reellement."
        )
    for point in points or []:
        try:
            index = int(point["index"])
            x = float(point["x"])
            y = float(point["y"])
        except (KeyError, TypeError, ValueError):
            continue
        if 0 <= index < len(photos):
            label = str(point.get("label") or "").strip()
            precision_label = f' ("{label}")' if label else ""
            consigne += (
                f" Sur la photo {index + 1}, le client a indique precisement la zone du probleme aux "
                f"coordonnees relatives environ {round(x * 100)}% depuis la gauche et {round(y * 100)}% depuis "
                f"le haut de cette photo{precision_label} : concentre ton observation sur cette zone en priorite "
                "si plusieurs elements sont visibles sur cette photo."
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

    questions = resultat.get("questions_clarification", [])
    return {
        "probleme_cle": probleme_cle,
        "probleme_label": resultat.get("probleme_label", probleme_cle),
        "observations_visuelles": resultat.get("observations_visuelles", ""),
        "categorie": categorie,
        "confiance": float(resultat.get("confiance", 0.5)),
        "questions_clarification": questions,
        "suggestions_clarification": _normaliser_suggestions(resultat.get("suggestions_clarification"), questions),
        "zones_detectees": _normaliser_zones(resultat.get("zones_detectees")),
        "degrade": False,
    }


def _normaliser_suggestions(suggestions_brutes: object, questions: list[str]) -> list[list[str]]:
    """Garantit une liste de meme longueur que questions_clarification, meme si l'IA a omis le champ,
    renvoye un nombre d'elements different, ou un type inattendu (defense contre une reponse mal formee)."""
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


async def analyser_photo(
    photos: list[tuple[bytes, str]],
    note: str | None = None,
    points: list[dict] | None = None,
) -> tuple[dict, list[dict]]:
    messages = _construire_messages_initiaux(photos, note, points)

    try:
        texte_reponse = await _appeler_modele(messages)
        resultat_brut = extraire_json(texte_reponse)
    except (json.JSONDecodeError, ValueError) as exc:
        raise DiagnosticIndisponible(f"Reponse OpenRouter inattendue : {exc}") from exc

    messages.append({"role": "assistant", "content": texte_reponse})
    resultat = await _finaliser_resultat(resultat_brut)
    return resultat, messages


async def continuer_conversation(
    messages: list[dict],
    reponse_utilisateur: str,
    nouvelles_photos: list[tuple[bytes, str]] | None = None,
) -> tuple[dict, list[dict]]:
    texte = f"Précision apportée par le client : {reponse_utilisateur}"
    if nouvelles_photos:
        texte += (
            " Le client a egalement joint une ou plusieurs photos supplementaires a ce message "
            "(demandees ou ajoutees spontanement) : utilise-les pour affiner ton observation."
        )
        contenu: list[dict] = [{"type": "text", "text": texte}]
        for image_bytes, content_type in nouvelles_photos:
            image_b64 = base64.b64encode(image_bytes).decode("ascii")
            contenu.append({"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{image_b64}"}})
        nouveau_message = {"role": "user", "content": contenu}
    else:
        nouveau_message = {"role": "user", "content": texte}

    messages = [*messages, nouveau_message]

    try:
        texte_reponse = await _appeler_modele(messages)
        resultat_brut = extraire_json(texte_reponse)
    except (json.JSONDecodeError, ValueError) as exc:
        raise DiagnosticIndisponible(f"Reponse OpenRouter inattendue : {exc}") from exc

    messages = [*messages, {"role": "assistant", "content": texte_reponse}]
    resultat = await _finaliser_resultat(resultat_brut)
    return resultat, messages


async def affiner_diagnostic(
    probleme_cle: str,
    reponse: str,
    session: dict | None,
    nouvelles_photos: list[tuple[bytes, str]] | None = None,
) -> tuple[dict, list[dict] | None]:
    if session is not None and session.get("messages"):
        try:
            return await continuer_conversation(session["messages"], reponse, nouvelles_photos)
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
