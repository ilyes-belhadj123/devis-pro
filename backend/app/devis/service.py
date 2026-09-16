import hashlib
import re

import httpx

from app.core.ai_utils import extraire_json
from app.core.database import database
from app.core.runtime_config import get_openrouter_api_key

# Noms de fournisseurs generiques et fictifs (aucune enseigne reelle) pour le comparateur
# de prix simule (TICKET comparateur) - un vrai comparateur demanderait un partenariat/API
# officiel avec chaque enseigne, hors de portee d'un prototype de demo.
NOMS_FOURNISSEURS = [
    "Atelier du Bâtiment",
    "Dépôt Matériaux Plus",
    "Quincaillerie Générale",
    "Grand Comptoir Pro",
    "Comptoir des Artisans",
]

DELAIS_LIVRAISON = ["En stock", "Sous 2 jours", "Sous 3 jours", "Sous 5 jours"]


def comparer_fournisseurs(reference: str, prix_actuel: float) -> list[dict]:
    """Simule 3 fournisseurs fictifs pour le meme article, avec une variation de prix,
    un delai de livraison et une note/nombre d'avis deterministes (bases sur un hash de
    la reference) plutot qu'aleatoires a chaque appel - le meme article renvoie toujours
    le meme comparatif."""
    hachage = int(hashlib.sha256(reference.encode()).hexdigest(), 16)

    noms_restants = list(NOMS_FOURNISSEURS)
    noms_choisis = []
    for i in range(3):
        index = (hachage >> (i * 5)) % len(noms_restants)
        noms_choisis.append(noms_restants.pop(index))

    fournisseurs = []
    for i, nom in enumerate(noms_choisis):
        # facteur de prix deterministe entre 0.88 (-12%) et 1.15 (+15%) du prix actuel
        octet_prix = (hachage >> (i * 8)) & 0xFF
        facteur = 0.88 + (octet_prix / 255) * 0.27

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


# Entreprises generiques et fictives (aucune enseigne/artisan reel) proposees en alternative
# a l'achat du materiel soi-meme - meme principe deterministe que le comparateur de
# fournisseurs, aucune vraie donnee ni scraping.
NOMS_ENTREPRISES_REPARATION = [
    "Rénov Services Plus",
    "Atelier Multi-Travaux",
    "Bâti Confort Pro",
    "Artisans Réunis",
    "Solution Habitat Services",
]

DELAIS_INTERVENTION = ["Disponible sous 2 jours", "Disponible sous 4 jours", "Disponible sous 1 semaine"]

_TABLE_ACCENTS = str.maketrans("éèêëàâäôöûüîïç'", "eeeeaaaoouuiic ")


def _slug_entreprise(nom: str) -> str:
    """Adresse mail fictive deduite du nom de l'entreprise (elle aussi fictive) - permet
    un lien mailto: reellement fonctionnel (le client mail de l'utilisateur s'ouvre pour
    de vrai) sans pretendre qu'une vraie entreprise existe derriere."""
    minuscule = nom.lower().translate(_TABLE_ACCENTS)
    return re.sub(r"[^a-z0-9]+", "", minuscule)


def proposer_entreprises_reparation(categorie: str) -> list[dict]:
    """Simule 3 entreprises fictives pouvant realiser les travaux, avec note/avis,
    distance et delai deterministes (bases sur un hash de la categorie) plutot
    qu'aleatoires - la meme categorie renvoie toujours les memes propositions."""
    hachage = int(hashlib.sha256(categorie.encode()).hexdigest(), 16)

    noms_restants = list(NOMS_ENTREPRISES_REPARATION)
    noms_choisis = []
    for i in range(3):
        index = (hachage >> (i * 5)) % len(noms_restants)
        noms_choisis.append(noms_restants.pop(index))

    entreprises = []
    for i, nom in enumerate(noms_choisis):
        octet_note = (hachage >> (20 + i * 6)) & 0x3F
        note = round(3.8 + (octet_note / 63) * 1.1, 1)  # entre 3.8 et 4.9

        octet_avis = (hachage >> (38 + i * 10)) & 0x3FF
        nombre_avis = 15 + (octet_avis % 180)  # entre 15 et 195

        octet_distance = (hachage >> (58 + i * 7)) & 0x7F
        distance_km = round(1.0 + (octet_distance / 127) * 14, 1)  # entre 1 et 15 km

        octet_delai = (hachage >> (70 + i * 3)) & 0x03
        delai = DELAIS_INTERVENTION[octet_delai % len(DELAIS_INTERVENTION)]

        entreprises.append(
            {
                "nom": nom,
                "specialite": categorie,
                "note": note,
                "nombre_avis": nombre_avis,
                "distance_km": distance_km,
                "delai_intervention": delai,
                "email": f"contact@{_slug_entreprise(nom)}.fr",
            }
        )

    entreprises.sort(key=lambda e: e["distance_km"])
    return entreprises


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELE = "anthropic/claude-sonnet-5"


async def _demander_choix_ia(nom_actuel: str, candidats: list[dict]) -> dict | None:
    api_key = await get_openrouter_api_key()
    if not api_key:
        return None

    liste_candidats = "\n".join(f"- {c['reference']} : {c['nom']} ({c['prix']:.2f} €)" for c in candidats)
    prompt = (
        f"Un client a le produit suivant dans son devis : \"{nom_actuel}\".\n"
        f"Voici des alternatives moins cheres disponibles dans le meme rayon :\n{liste_candidats}\n\n"
        "Choisis celle qui remplace le mieux fonctionnellement ce produit precis (pas juste la moins chere "
        "si elle n'a pas de sens comme substitut). Reponds UNIQUEMENT avec un JSON du type "
        '{"reference": "<une des references ci-dessus>"}.'
    )

    try:
        async with httpx.AsyncClient(timeout=20.0) as http_client:
            response = await http_client.post(
                OPENROUTER_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": MODELE, "messages": [{"role": "user", "content": prompt}]},
            )
            response.raise_for_status()
            data = response.json()
        resultat = extraire_json(data["choices"][0]["message"]["content"])
        reference_choisie = resultat.get("reference")
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        return None

    return next((c for c in candidats if c["reference"] == reference_choisie), None)


async def trouver_alternative_moins_chere(reference_actuelle: str, categorie: str, prix_actuel: float) -> dict:
    produit_actuel = await database.produits.find_one({"reference": reference_actuelle}, {"_id": 0})
    nom_actuel = produit_actuel["nom"] if produit_actuel else reference_actuelle

    candidats = (
        await database.produits.find(
            {"categorie": categorie, "reference": {"$ne": reference_actuelle}, "prix": {"$lt": prix_actuel}},
            {"_id": 0},
        )
        .sort("prix", 1)
        .to_list()
    )

    if not candidats:
        return {"trouve": False}

    choix = await _demander_choix_ia(nom_actuel, candidats) or candidats[0]

    return {
        "trouve": True,
        "reference": choix["reference"],
        "nom": choix["nom"],
        "prix": choix["prix"],
        "unite": choix["unite"],
    }


PROMPT_SYSTEME_ASSISTANT = (
    "Tu es l'assistant SnapDevis, integre a l'ecran de devis d'un client. Tu reponds UNIQUEMENT a des questions "
    "sur LE DEVIS PRECIS fourni ci-dessous (ses lignes, quantites, prix, categories, total) - jamais de conseils "
    "bricolage generaux sans rapport avec ce devis, jamais de prix ou de produit invente qui n'est pas dans la "
    "liste. Si la question sort de ce cadre (un autre projet, une question sans rapport avec ce devis), dis "
    "poliment que tu ne peux repondre qu'aux questions sur ce devis precis. Reponds en francais, de maniere "
    "concise et utile (2 a 4 phrases, sauf si le client demande explicitement plus de detail).\n\n"
    "DEVIS ACTUEL :\n{devis}"
)


def _formater_devis_pour_prompt(lignes: list[dict], total: float) -> str:
    lignes_texte = "\n".join(
        f"- {l['nom']} : {l['quantite']} {l['unite']} x {l['prix_unitaire']:.2f} € "
        f"= {l['quantite'] * l['prix_unitaire']:.2f} € ({l['categorie']})"
        for l in lignes
    )
    return f"{lignes_texte}\nTotal : {total:.2f} €"


async def repondre_assistant(lignes: list[dict], total: float, messages: list[dict]) -> str | None:
    api_key = await get_openrouter_api_key()
    if not api_key:
        return None

    prompt_systeme = PROMPT_SYSTEME_ASSISTANT.format(devis=_formater_devis_pour_prompt(lignes, total))
    messages_completes = [{"role": "system", "content": prompt_systeme}, *messages]

    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(
                OPENROUTER_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": MODELE, "messages": messages_completes},
            )
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError):
        return None
