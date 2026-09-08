# SnapDevis Entretien — Backlog de tickets

Second module de SnapDevis, dédié aux **entreprises d'entretien d'espaces verts travaillant en contrats récurrents** (copropriétés, collectivités, bailleurs) — distinct du module bricolage existant (catalogue global, mono-compte). Voir `docs/SnapDevis_Entretien_Tickets_OneShot.md` pour le cahier complet fourni par le client, et la mémoire projet pour le contexte de décision (second module dans le même repo, pas un pivot).

Stack : React 18 + TypeScript + Vite (frontend) · FastAPI Python 3.12 (backend) · MongoDB · Claude API via OpenRouter · Azure — infrastructure partagée avec le module bricolage, packages backend/frontend namespacés `entretien`.

Règles transverses : aucune donnée réelle, aucune clé API en dur, aucune marque tierce réelle — cf. cahier complet.

---

## Épique 1 — Socle technique et catalogue

- [x] **TICKET-101** — Setup frontend : routes `/entretien/*` (upload, diagnostic, devis, validation), écrans coquille avec données factices, identité visuelle SnapDevis réutilisée.
- [x] **TICKET-102** — Setup backend : packages `app/entretien_comptes/`, `app/entretien_catalogue/`, routers enregistrés dans `main.py`, même Mongo (collections préfixées `entretien_`).
- [x] **TICKET-103** — Import du catalogue/grille tarifaire propre à l'artisan : template CSV téléchargeable, import qui remplace le catalogue du compte, erreurs de format signalées clairement, jeu de démo fictif (36 lignes) seedable via `backend/scripts/seed_catalogue_entretien.py`.

## Épique 2 — Diagnostic visuel et estimation de surface

- [x] **TICKET-201** — Upload photo et prétraitement : écran d'upload (drag & drop + appareil photo), compression client (`compresserImage`), `POST /entretien/diagnostic/analyser`, session créée côté serveur.
- [x] **TICKET-202** — Estimation de surface par objet de référence : note enrichie avec objet de référence ou longueur manuelle d'un côté visible, l'IA renvoie `estimation_surface` (valeur, unité, `a_confirmer`), badge "À confirmer" + champ de correction manuelle côté client.
- [x] **TICKET-203** — Diagnostic IA du besoin : appel Claude via OpenRouter (`app/entretien_diagnostic/`), sortie structurée (catégorie, confiance, tâches suggérées), clarification multi-tours (`POST /entretien/diagnostic/affiner`).
- [x] **Ajustement demandé par le client** : l'activité couverte n'est pas limitée aux espaces verts (extérieur) — le diagnostic classe désormais aussi le lieu (intérieur/extérieur), comme le fait déjà le module bricolage. Champ `lieu` ajouté au résultat, badge + chips de correction rapide sur l'écran diagnostic. Les 9 catégories restent orientées espaces verts pour l'instant (catégorie "divers" en repli pour l'intérieur) — une vraie couverture de prestations d'intérieur (nettoyage de locaux, parties communes...) reste à faire si besoin.

## Épique 3 — Génération du devis (options + contrat récurrent)

- [x] **TICKET-301** — Devis à 3 niveaux (éco/standard/premium) : `POST /entretien/devis/generer` (`app/entretien_devis/`), l'IA compose 3 formules à partir du catalogue réel du compte (repli déterministe sinon), progression de contenu/prix vérifiée (ex. 123€ → 169€ → 455€).
- [x] **TICKET-302** — Mode contrat d'entretien récurrent : `POST /entretien/devis/contrat-recurrent`, fréquence (mensuelle/bimensuelle/saisonnière) + durée d'engagement, dégressivité de 10% sur le prix unitaire par rapport au ponctuel.
- [x] **TICKET-303** — Écran de devis interactif : 3 formules sélectionnables, ajustement de quantité (+/-) et suppression de ligne avec recalcul du total en temps réel, bascule ponctuel/récurrent.

## Épique 4 — Validation humaine et signature

- [x] **TICKET-401** — File de validation artisan : `app/entretien_validation/`, statuts `en_attente_validation → valide → envoye → accepte` persistés en base (`entretien_devis_valides`), artisan peut ajuster désignation/prix/quantité tant que non validé, `/envoyer` refuse (409) tant que le statut n'est pas `valide`.
- [x] **TICKET-402** — Acceptation en ligne par le client final : lien unique `/entretien/devis-client/:id` (public), le client choisit sa formule et coche une case pour accepter, statut passe à `accepte` — l'artisan voit la notification (bandeau "✓ Accepté par le client") en rouvrant le devis dans sa file de validation (pas d'email/push réel, notification in-app uniquement).

## Épique 5 — Export et intégration

- [x] **TICKET-501** — Export PDF du devis : `GET /entretien/validation/devis/{id}/pdf?niveau=...` (reportlab, mise en page reprenant l'identité SnapDevis), disponible dès que le devis est validé (statuts `valide`/`envoye`/`accepte`).
- [x] **TICKET-502** — Export facturation générique : `GET /entretien/validation/devis/{id}/export?niveau=...&format=csv|json`, format documenté dans `docs/EXPORT_FORMAT.md` (TVA générique 20%, colonnes/clés détaillées), validé par `backend/tests/test_entretien_export.py` (5 tests, dont la vérification montant_ttc = montant_ht × 1.2).

## Épique 6 — Apprentissage des corrections

- [x] **TICKET-601** — Mémorisation des corrections par compte artisan : `app/entretien_devis/apprentissage.py`, chaque correction significative (>10% d'écart) de quantité/prix détectée à la validation (`/entretien/validation/devis/{id}/valider`) est enregistrée dans `entretien_corrections` (compte_id, catégorie, désignation, champ, ratio) ; `POST /entretien/devis/generer` pondère les futures suggestions par la moyenne des ratios appris pour ce compte+catégorie+désignation, et renvoie `ajustements_appris` (affiché côté artisan). Strictement local au compte — validé par un test dédié qui vérifie qu'un compte sans historique n'est pas influencé par les corrections d'un autre. Un vrai bug de partage de références entre formules a été détecté et corrigé au passage (le repli déterministe partageait les mêmes objets `dict` entre éco/standard/premium, faisant tripler la pondération en cascade).

---

## Ordre d'exécution

1. Épique 1 (fait) — fondation.
2. Épique 2 — diagnostic + surface, cœur technique différenciant.
3. Épique 3 — devis à options + récurrent, cœur de la valeur commerciale.
4. Épique 4 — validation + acceptation, rend le produit utilisable en conditions réelles.
5. Épique 5 — export, lève la friction d'adoption.
6. Épique 6 — apprentissage, raffinement final.

Chaque épique est livrée et testée indépendamment avant de passer à la suivante.
