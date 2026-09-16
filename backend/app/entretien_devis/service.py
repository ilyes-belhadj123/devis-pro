import hashlib
import json

import httpx

from app.core.ai_utils import extraire_json
from app.core.runtime_config import get_openrouter_api_key

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELE = "anthropic/claude-sonnet-5"

# Noms de fournisseurs generiques et fictifs specifiques a l'entretien d'espaces verts
# (aucune enseigne reelle) - meme principe que le comparateur du module bricolage
# (app/devis/service.py::comparer_fournisseurs), duplique volontairement plutot que
# partage entre modules pour rester coherent avec le reste de l'architecture (second
# module independant).
NOMS_FOURNISSEURS = [
    "Pépinière du Coin",
    "Négoce Paysager Plus",
    "Jardi Dépôt",
    "Grand Comptoir Végétal",
    "Végétal Distribution",
]

DELAIS_LIVRAISON = ["En stock", "Sous 2 jours", "Sous 3 jours", "Sous 5 jours"]


def comparer_fournisseurs(designation: str, prix_actuel: float) -> list[dict]:
    """Simule 3 fournisseurs fictifs pour la meme prestation/produit, avec une variation
    de prix, un delai de livraison et une note/nombre d'avis deterministes (bases sur un
    hash de la designation) plutot qu'aleatoires - la meme ligne renvoie toujours le
    meme comparatif."""
    hachage = int(hashlib.sha256(designation.encode()).hexdigest(), 16)

    noms_restants = list(NOMS_FOURNISSEURS)
    noms_choisis = []
    for i in range(3):
        index = (hachage >> (i * 5)) % len(noms_restants)
        noms_choisis.append(noms_restants.pop(index))

    fournisseurs = []
    for i, nom in enumerate(noms_choisis):
        octet_prix = (hachage >> (i * 8)) & 0xFF
        facteur = 0.88 + (octet_prix / 255) * 0.27  # entre -12% et +15% du prix actuel

        octet_delai = (hachage >> (24 + i * 4)) & 0x0F
        delai = DELAIS_LIVRAISON[octet_delai % len(DELAIS_LIVRAISON)]

        octet_note = (hachage >> (36 + i * 6)) & 0x3F
        note = round(3.6 + (octet_note / 63) * 1.3, 1)  # entre 3.6 et 4.9

        octet_avis = (hachage >> (54 + i * 10)) & 0x3FF
        nombre_avis = 25 + (octet_avis % 275)  # entre 25 et 300

        fournisseurs.append(
            {
                "nom": nom,
                "prix": round(prix_actuel * facteur, 2),
                "delai_livraison": delai,
                "note": note,
                "nombre_avis": nombre_avis,
            }
        )

    fournisseurs.sort(key=lambda f: f["prix"])
    for i, fournisseur in enumerate(fournisseurs):
        fournisseur["moins_cher"] = i == 0

    return fournisseurs

PROMPT_FORMULES_TEMPLATE = (
    "Tu dois construire 3 formules de devis (eco, standard, premium) pour ce diagnostic d'entretien :\n"
    "- Categorie principale du besoin : {categorie}\n"
    "- Lieu : {lieu}\n"
    "- Taches identifiees : {taches}\n"
    "- Surface/longueur estimee : {surface}\n\n"
    "Catalogue disponible pour ce compte (designation : prix / unite (categorie)) :\n{catalogue}\n\n"
    "Regles :\n"
    "- eco : uniquement les prestations essentielles, le strict minimum pour repondre au besoin signale - rien "
    "de plus, meme si d'autres prestations du catalogue seraient pertinentes.\n"
    "- standard (recommande) : eco + les prestations complementaires qu'un professionnel serieux inclut par "
    "defaut pour un travail bien fini (evacuation des dechets generes par les lignes de eco, petites "
    "finitions) - c'est la formule que tu recommanderais toi-meme a un client.\n"
    "- premium : standard + des prestations d'entretien renforce qui prolongent le resultat dans le temps "
    "(traitement, fertilisation, paillage...) UNIQUEMENT si elles existent dans le catalogue et font sens pour "
    "ce type d'espace - ne les invente pas si rien de pertinent n'est disponible.\n"
    "- N'utilise QUE des designations presentes EXACTEMENT dans le catalogue ci-dessus (copie-les telles "
    "quelles, sans les modifier).\n\n"
    "CALCUL DES QUANTITES - base-toi sur des taux d'usage reels du metier, pas des chiffres arbitraires :\n"
    "- Si l'unite du produit correspond exactement a la surface/longueur estimee (m2 ou ml), utilise "
    "directement cette valeur (ex : tonte, taille de haie au ml, desherbage/traitement/paillage au m2).\n"
    "- Engrais/fertilisation (sac de 10 ou 20kg) : dosage courant 20 a 40 g/m2 pour un engrais organique - un "
    "sac de 20kg traite environ 500 a 800 m2 selon ce dosage. Calcule le nombre de sacs = surface totale / "
    "couverture par sac (arrondi a l'entier superieur, minimum 1), pas systematiquement 1 sac quelle que soit "
    "la surface.\n"
    "- Plantation d'arbustes ou de vivaces isolees (prix a l'unite, pas au ml) : compte environ un plant tous "
    "les 1 a 1,5 m lineaire pour un alignement, ou 3 a 5 plants par m2 pour un massif dense de vivaces - deduis "
    "un nombre entier de plants a partir de la surface/longueur estimee plutot que de mettre 1 par defaut.\n"
    "- Evacuation de dechets verts (prix au m3) : compte environ 0,001 a 0,002 m3 de dechets par m2 de pelouse "
    "tondue/debroussaillee, et environ 0,03 a 0,05 m3 par metre lineaire de haie taillee - additionne les "
    "dechets generes par les autres lignes de la meme formule (minimum 0,5 m3 des qu'une evacuation est "
    "incluse, un volume ne se facture pas en dessous d'un seuil pratique).\n"
    "- Pour tout le reste (aucune correspondance d'unite ni de regle ci-dessus), utilise une quantite entiere "
    "raisonnable (1 le plus souvent), jamais une quantite gonflee sans justification.\n"
    "- Arrondis toujours a une quantite qui a du sens dans le metier : entiers pour les sacs/plants/unites, "
    "pas de decimales improbables (ex: 3,27 sacs).\n"
    "- standard doit apporter strictement plus de valeur que eco, et premium strictement plus que standard.\n"
    "- Si le catalogue ne contient rien de pertinent pour une prestation d'interieur, fais au mieux avec ce "
    "qui est disponible plutot que de renvoyer une liste vide.\n\n"
    "Reponds UNIQUEMENT avec un objet JSON valide, sans texte autour ni markdown, du type exact :\n"
    '{{"eco": [{{"designation": "<designation exacte du catalogue>", "quantite": <nombre>}}], '
    '"standard": [...], "premium": [...]}}'
)


def _normaliser_unite(unite: str) -> str:
    return unite.strip().lower().replace("²", "2")


def _quantite_pour_produit(produit: dict, estimation_surface: dict | None) -> float:
    if estimation_surface and _normaliser_unite(produit["unite"]) == _normaliser_unite(estimation_surface["unite"]):
        return max(0.5, round(float(estimation_surface["valeur"]), 2))
    return 1.0


async def _appeler_modele_texte(prompt: str) -> str | None:
    api_key = await get_openrouter_api_key()
    if not api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(
                OPENROUTER_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": MODELE, "messages": [{"role": "user", "content": prompt}]},
            )
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError):
        return None


async def generer_formules(
    categorie: str,
    lieu: str,
    taches: list[str],
    estimation_surface: dict | None,
    catalogue: list[dict],
) -> dict[str, list[dict]] | None:
    """Laisse l'IA composer 3 formules a partir du catalogue reel du compte. Renvoie None si
    indisponible (repli deterministe sur _formules_par_defaut)."""
    if not catalogue:
        return None

    catalogue_texte = "\n".join(
        f"- {p['designation']} : {p['prix']:.2f} EUR / {p['unite']} ({p['categorie']})" for p in catalogue
    )
    surface_texte = (
        f"{estimation_surface['valeur']} {estimation_surface['unite']}" if estimation_surface else "non precisee"
    )
    prompt = PROMPT_FORMULES_TEMPLATE.format(
        categorie=categorie,
        lieu=lieu,
        taches=", ".join(taches) or "non precisees",
        surface=surface_texte,
        catalogue=catalogue_texte,
    )

    texte_reponse = await _appeler_modele_texte(prompt)
    if texte_reponse is None:
        return None

    try:
        resultat = extraire_json(texte_reponse)
    except (json.JSONDecodeError, ValueError):
        return None

    catalogue_par_designation = {p["designation"]: p for p in catalogue}
    formules: dict[str, list[dict]] = {}
    for niveau in ("eco", "standard", "premium"):
        lignes: list[dict] = []
        for item in resultat.get(niveau) or []:
            if not isinstance(item, dict):
                continue
            produit = catalogue_par_designation.get(item.get("designation"))
            if produit is None:
                continue
            try:
                quantite = max(0.5, round(float(item.get("quantite", 1)), 2))
            except (TypeError, ValueError):
                quantite = 1.0
            lignes.append({**produit, "quantite": quantite})
        formules[niveau] = lignes

    return formules if any(formules.values()) else None


def formules_par_defaut(
    categorie: str,
    estimation_surface: dict | None,
    catalogue: list[dict],
) -> dict[str, list[dict]] | None:
    """Repli deterministe si l'IA est indisponible : construit 3 niveaux en empilant les
    produits les moins chers de la categorie concernee, puis evacuation, puis traitement/
    fertilisation - une progression de contenu simple mais toujours coherente."""
    candidats = sorted((p for p in catalogue if p["categorie"] == categorie), key=lambda p: p["prix"])
    if not candidats:
        candidats = sorted(catalogue, key=lambda p: p["prix"])[:1]
    if not candidats:
        return None

    def ligne(produit: dict) -> dict:
        return {**produit, "quantite": _quantite_pour_produit(produit, estimation_surface)}

    evacuation = next((p for p in catalogue if p["categorie"] == "evacuation"), None)
    renforcement = next((p for p in catalogue if p["categorie"] in ("traitement", "fertilisation")), None)

    # chaque niveau reconstruit ses propres lignes (appels separes a ligne()) plutot que de
    # reutiliser les listes precedentes : des dicts partages entre niveaux se feraient
    # modifier plusieurs fois par appliquer_ponderation (TICKET-601), faussant le resultat.
    eco = [ligne(candidats[0])]

    standard = [ligne(candidats[0])]
    if evacuation is not None:
        standard.append(ligne(evacuation))
    elif len(candidats) > 1:
        standard.append(ligne(candidats[1]))

    premium = [ligne(candidats[0])]
    if evacuation is not None:
        premium.append(ligne(evacuation))
    elif len(candidats) > 1:
        premium.append(ligne(candidats[1]))
    if renforcement is not None:
        premium.append(ligne(renforcement))
    elif len(candidats) > 2:
        premium.append(ligne(candidats[2]))

    return {"eco": eco, "standard": standard, "premium": premium}
