# Format d'export SnapDevis Entretien → logiciel de facturation

Ce document décrit le format des exports produits par `GET /entretien/validation/devis/{id}/export` (CSV ou JSON), pensés pour être ré-importés dans un logiciel de facturation tiers générique (nommé "mon logiciel de facturation" côté interface — aucune marque tierce réelle n'est ciblée).

## Pré-requis

- Le devis doit être **validé** par l'artisan (statut `valide`, `envoye` ou `accepte`) — un devis encore `en_attente_validation` renvoie une erreur 409.
- L'export porte sur **une seule formule** du devis (éco, standard ou premium), sélectionnée via le paramètre `niveau` (`?niveau=standard`). Si omis : la formule choisie par le client si le devis a été accepté, sinon `standard` par défaut.

## Hypothèses de calcul

- **TVA** : taux générique fixe de **20%** appliqué à chaque ligne (`TAUX_TVA = 0.20` dans `app/entretien_validation/export.py`). Une vraie intégration facturation devra remplacer ceci par le taux réel applicable (produit, pays, régime de l'entreprise).
- **Devise** : EUR uniquement.
- Les montants sont arrondis à 2 décimales.

## Format CSV (`?format=csv`, par défaut)

Un fichier CSV avec en-tête, une ligne par prestation de la formule exportée.

| Colonne | Type | Description |
|---|---|---|
| `reference_devis` | texte | Identifiant du devis SnapDevis (Mongo ObjectId) |
| `categorie_devis` | texte | Catégorie de besoin détectée par le diagnostic (ex. `tonte`) |
| `formule` | texte | Niveau exporté : `eco`, `standard` ou `premium` |
| `designation` | texte | Désignation de la prestation |
| `categorie_prestation` | texte | Catégorie de la ligne dans le catalogue (ex. `evacuation`) |
| `unite` | texte | Unité (`m2`, `ml`, `unite`, `sac 20kg`...) |
| `quantite` | nombre | Quantité facturée |
| `prix_unitaire_ht` | nombre | Prix unitaire hors taxes |
| `montant_ht` | nombre | `quantite × prix_unitaire_ht`, arrondi à 2 décimales |
| `taux_tva` | nombre | Taux de TVA appliqué (ex. `0.2` pour 20%) |
| `montant_ttc` | nombre | `montant_ht × (1 + taux_tva)`, arrondi à 2 décimales |

Exemple :

```csv
reference_devis,categorie_devis,formule,designation,categorie_prestation,unite,quantite,prix_unitaire_ht,montant_ht,taux_tva,montant_ttc
66f1a2b3c4d5e6f7a8b9c0d1,tonte,standard,Tonte pelouse standard,tonte,m2,120,0.35,42.0,0.2,50.4
66f1a2b3c4d5e6f7a8b9c0d1,tonte,standard,Ramassage et evacuation de l'herbe coupee,evacuation,m2,120,0.15,18.0,0.2,21.6
```

## Format JSON (`?format=json`)

```json
{
  "reference_devis": "66f1a2b3c4d5e6f7a8b9c0d1",
  "categorie_devis": "tonte",
  "formule": "standard",
  "devise": "EUR",
  "taux_tva": 0.2,
  "lignes": [
    {
      "reference_devis": "66f1a2b3c4d5e6f7a8b9c0d1",
      "categorie_devis": "tonte",
      "formule": "standard",
      "designation": "Tonte pelouse standard",
      "categorie_prestation": "tonte",
      "unite": "m2",
      "quantite": 120,
      "prix_unitaire_ht": 0.35,
      "montant_ht": 42.0,
      "taux_tva": 0.2,
      "montant_ttc": 50.4
    }
  ],
  "total_ht": 42.0,
  "total_ttc": 50.4
}
```

Chaque ligne du tableau `lignes` reprend exactement les mêmes clés que les colonnes CSV, pour garder les deux formats interchangeables. `total_ht` et `total_ttc` sont la somme arrondie des lignes.

## Validation

Le script de test `backend/tests/test_entretien_export.py` crée un devis de test, le fait passer par le cycle `en_attente_validation → valide`, appelle les deux endpoints d'export et vérifie que les colonnes/clés ci-dessus sont bien présentes et cohérentes (montant_ttc = montant_ht × 1.2, total = somme des lignes).
