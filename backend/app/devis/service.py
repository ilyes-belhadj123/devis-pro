import hashlib

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


def comparer_fournisseurs(reference: str, prix_actuel: float) -> list[dict]:
    """Simule 3 fournisseurs fictifs pour le meme article, avec une variation de prix
    deterministe (basee sur un hash de la reference) plutot qu'aleatoire a chaque appel -
    le meme article renvoie toujours le meme comparatif."""
    hachage = int(hashlib.sha256(reference.encode()).hexdigest(), 16)

    noms_restants = list(NOMS_FOURNISSEURS)
    noms_choisis = []
    for i in range(3):
        index = (hachage >> (i * 5)) % len(noms_restants)
        noms_choisis.append(noms_restants.pop(index))

    fournisseurs = []
    for i, nom in enumerate(noms_choisis):
        # facteur deterministe entre 0.88 (-12%) et 1.15 (+15%) du prix actuel
        octet = (hachage >> (i * 8)) & 0xFF
        facteur = 0.88 + (octet / 255) * 0.27
        fournisseurs.append({"nom": nom, "prix": round(prix_actuel * facteur, 2)})

    fournisseurs.sort(key=lambda f: f["prix"])
    for i, fournisseur in enumerate(fournisseurs):
        fournisseur["moins_cher"] = i == 0

    return fournisseurs

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
