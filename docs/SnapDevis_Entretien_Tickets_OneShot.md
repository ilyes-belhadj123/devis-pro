# SnapDevis Entretien — Cahier de tickets (one-shot Claude Code)

## Contexte du projet

SnapDevis Entretien est un agent IA qui transforme une photo d'un espace vert en devis chiffré, destiné en priorité aux **entreprises d'entretien d'espaces verts travaillant en contrats récurrents** (copropriétés, collectivités, bailleurs), et non à la création de jardin sur-mesure. Un gestionnaire ou un client final photographie un espace (pelouse, haie, massif), et l'outil génère un devis avec plusieurs formules, que l'artisan valide avant envoi.

Ce document est conçu pour être exécuté directement par Claude Code, dans l'ordre des épics ci-dessous. Chaque ticket est autonome et contient tout le contexte nécessaire pour être implémenté sans aller-retour.

## Stack technique

- Frontend : React 18 + TypeScript + Vite
- Backend : FastAPI (Python 3.12)
- Base de données : MongoDB
- IA : Claude API via OpenRouter (vision + raisonnement)
- Infrastructure cible : Azure

## Règles transverses (à respecter sur tous les tickets)

- **Aucune donnée réelle** : noms de clients, entreprises, catalogues de fournisseurs — tout doit être fictif mais crédible (ex. "Verdura Paysage", "jane.doe@example.com").
- **Aucune clé API en dur** : toujours via variables d'environnement référencées par leur nom (`OPENROUTER_API_KEY`, `MONGODB_URI`, etc.), jamais lues ni affichées en clair dans le code, les logs ou les commits.
- **Aucune marque tierce réelle** (Obat, Batappli, Indy, UNEP...) utilisée dans l'interface ou les données de démo — utiliser des noms génériques du type "Logiciel de facturation X" pour les exports simulés.
- **Definition of Done commune** : testé manuellement sur le parcours complet concerné, cohérent avec les tickets précédents, pas de régression.

---

## Épique 1 — Socle technique et catalogue

### TICKET-101 — Setup frontend
- Initialiser React 18 + TypeScript + Vite.
- Routing pour les écrans : upload, diagnostic, devis, validation artisan.
- Design de base : fond clair, une couleur d'accent dégradé corail-ambre pour les CTA, cartes à coins arrondis avec ombre douce (repartir de la direction visuelle déjà validée pour SnapDevis V2 : sobre, premium, crédible pour un usage professionnel).
- **Critère d'acceptation** : projet démarrable en local, navigation entre écrans avec données factices.

### TICKET-102 — Setup backend
- Initialiser FastAPI, structure par domaine (upload, diagnostic, devis, catalogue, export).
- Connexion MongoDB via variable d'environnement.
- Endpoint `/health`.
- **Critère d'acceptation** : API démarrable, `/health` répond 200.

### TICKET-103 — Import du catalogue/grille tarifaire propre à l'artisan
- Écran d'import : l'artisan peut importer sa propre grille tarifaire (upload CSV : désignation, unité, prix, catégorie) plutôt que d'utiliser un catalogue générique imposé.
- Fournir un template CSV téléchargeable et un jeu de données de démonstration factice (30-40 lignes : tonte, taille de haie, désherbage, plantation, évacuation déchets verts, engrais, paillage...).
- Parsing et stockage MongoDB du catalogue par compte artisan.
- **Critère d'acceptation** : un CSV importé remplace correctement le catalogue démo pour le compte concerné ; erreurs de format signalées clairement.

---

## Épique 2 — Diagnostic visuel et estimation de surface

### TICKET-201 — Upload photo et prétraitement
- Écran d'upload (drag & drop + prise de photo mobile), formats jpg/png/heic, compression côté client.
- Endpoint `POST /diagnostic/analyser`.
- **Critère d'acceptation** : photo reçue côté backend, taille optimisée, session créée.

### TICKET-202 — Estimation de surface par objet de référence
- À l'upload, proposer à l'utilisateur de poser un objet de taille connue dans le cadre (ex. une bouteille de 30 cm, un mètre pliant) ou de renseigner manuellement une dimension approximative (longueur d'un côté visible).
- Le backend utilise cette référence pour convertir les proportions de l'image en estimation de surface/longueur réelle (m² de pelouse, mètres linéaires de haie).
- Si aucune référence n'est fournie, afficher une estimation par défaut avec un badge "à confirmer" et permettre une saisie manuelle de correction.
- **Critère d'acceptation** : sur un jeu de 10 photos de test avec objet de référence, l'estimation de surface est cohérente à ±20% par rapport à la mesure réelle simulée dans les données de test.

### TICKET-203 — Diagnostic IA du besoin
- Appel à Claude via OpenRouter avec l'image + éventuelle question de clarification (type d'espace vert, fréquence souhaitée : ponctuel ou contrat récurrent).
- Sortie structurée : catégorie de besoin, niveau de confiance, liste de tâches suggérées (tonte, taille, désherbage...).
- **Critère d'acceptation** : sur 10 photos variées (pelouse, haie, massif), diagnostic cohérent pour au moins 8.

---

## Épique 3 — Génération du devis (options + contrat récurrent)

### TICKET-301 — Génération de devis à 3 niveaux (éco/standard/premium)
- Endpoint `POST /devis/generer` qui croise le diagnostic + surface estimée + catalogue de l'artisan pour produire **trois versions** du devis : éco (prestations essentielles), standard (recommandé), premium (options supplémentaires : traitement phytosanitaire, engrais renforcé...).
- Chaque version affiche clairement ce qui la différencie des autres.
- **Critère d'acceptation** : les 3 devis sont générés à partir du même diagnostic, avec un delta de prix et de contenu cohérent entre les niveaux.

### TICKET-302 — Mode contrat d'entretien récurrent
- En plus du devis ponctuel, permettre de générer un **forfait récurrent** : fréquence de passage (mensuelle, bimensuelle, saisonnière), engagement (durée du contrat), prix mensuel ou annuel calculé à partir du devis ponctuel de référence.
- Interface dédiée pour basculer entre "devis ponctuel" et "contrat récurrent" sur un même diagnostic.
- **Critère d'acceptation** : à partir d'un même diagnostic, on peut générer soit un devis ponctuel, soit un forfait récurrent cohérent (le prix mensuel doit refléter une dégressivité logique par rapport au ponctuel).

### TICKET-303 — Écran de devis interactif
- Affichage des 3 formules côte à côte (ou en onglets sur mobile), sélection d'une formule, ajustement des quantités, suppression d'une ligne.
- **Critère d'acceptation** : changement de formule ou de quantité recalcule le total en temps réel sans rechargement.

---

## Épique 4 — Validation humaine et signature

### TICKET-401 — File de validation artisan
- Avant tout envoi au client final, le devis généré passe par un écran de validation dédié à l'artisan : il peut ajuster une quantité, un prix, ou un texte avant de valider.
- Statut du devis : "généré", "en attente de validation", "validé", "envoyé".
- **Critère d'acceptation** : un devis ne peut pas être envoyé au client final tant qu'il n'est pas passé par le statut "validé" par l'artisan.

### TICKET-402 — Acceptation en ligne par le client final
- Le devis validé est envoyé au client final via un lien unique. Le client peut choisir sa formule (éco/standard/premium) et accepter en ligne (case à cocher + bouton, pas de signature manuscrite complexe pour le MVP).
- Notification à l'artisan dès qu'un devis est accepté.
- **Critère d'acceptation** : le parcours validation artisan → envoi → acceptation client → notification fonctionne de bout en bout avec des données de test.

---

## Épique 5 — Export et intégration

### TICKET-501 — Export PDF du devis
- Génération PDF côté serveur, mise en page professionnelle, couleurs personnalisables (logo/couleur de l'entreprise artisan, factices en démo).
- **Critère d'acceptation** : le PDF reprend fidèlement le devis validé, avec une mise en page soignée.

### TICKET-502 — Export vers un format de facturation externe générique
- Permettre l'export du devis validé au format CSV/JSON structuré, compatible avec une ré-importation dans un logiciel de facturation tiers générique (nommé de façon neutre dans l'interface, ex. "Exporter vers mon logiciel de facturation").
- Documenter le format d'export dans un fichier `EXPORT_FORMAT.md` pour faciliter une intégration future avec un vrai logiciel du marché.
- **Critère d'acceptation** : un export généré respecte le format documenté et peut être relu/validé par un script de test.

---

## Épique 6 — Apprentissage des corrections

### TICKET-601 — Mémorisation des corrections par compte artisan
- Lorsque l'artisan corrige une quantité ou un prix lors de la validation (TICKET-401), enregistrer cette correction associée à son compte et au type de besoin concerné.
- Lors d'un diagnostic futur similaire (même catégorie de besoin, même artisan), pondérer la suggestion initiale de l'IA avec l'historique des corrections propres à ce compte.
- **Important** : cet apprentissage reste strictement local au compte de l'artisan concerné, jamais mutualisé entre comptes.
- **Critère d'acceptation** : après 3 corrections similaires enregistrées sur un compte de test, une nouvelle suggestion générée pour ce compte reflète la tendance des corrections précédentes.

---

## Ordre d'exécution recommandé pour Claude Code

1. Épique 1 (socle + catalogue) — fondation indispensable.
2. Épique 2 (diagnostic + surface) — cœur technique différenciant.
3. Épique 3 (devis à options + récurrent) — cœur de la valeur commerciale.
4. Épique 4 (validation + acceptation) — rend le produit utilisable en conditions réelles.
5. Épique 5 (export) — lève la friction d'adoption.
6. Épique 6 (apprentissage) — raffinement, à faire en dernier.

Chaque épique peut être livrée et testée indépendamment avant de passer à la suivante.
