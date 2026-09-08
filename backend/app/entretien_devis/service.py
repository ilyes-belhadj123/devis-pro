import json

import httpx

from app.core.ai_utils import extraire_json
from app.core.runtime_config import get_openrouter_api_key

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELE = "anthropic/claude-sonnet-5"

PROMPT_FORMULES_TEMPLATE = (
    "Tu dois construire 3 formules de devis (eco, standard, premium) pour ce diagnostic d'entretien :\n"
    "- Categorie principale du besoin : {categorie}\n"
    "- Lieu : {lieu}\n"
    "- Taches identifiees : {taches}\n"
    "- Surface/longueur estimee : {surface}\n\n"
    "Catalogue disponible pour ce compte (designation : prix / unite (categorie)) :\n{catalogue}\n\n"
    "Regles :\n"
    "- eco : uniquement les prestations essentielles, le minimum pour repondre au besoin.\n"
    "- standard (recommande) : eco + les prestations complementaires usuelles pour un resultat soigne "
    "(par exemple evacuation des dechets, finitions).\n"
    "- premium : standard + des options de qualite ou d'entretien renforce si elles existent dans le "
    "catalogue (traitement, fertilisation, paillage...).\n"
    "- N'utilise QUE des designations presentes EXACTEMENT dans le catalogue ci-dessus (copie-les telles "
    "quelles, sans les modifier).\n"
    "- Calcule une quantite realiste pour chaque ligne : si l'unite du produit correspond a la surface/longueur "
    "estimee (m2 ou ml), utilise cette valeur ; sinon utilise une quantite entiere raisonnable (1 le plus "
    "souvent).\n"
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
