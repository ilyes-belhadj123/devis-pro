# SnapDevis — Backlog de tickets (Phase 1 : Prototype vendable)

Stack : React 18 + TypeScript + Vite (frontend) · FastAPI Python 3.12 (backend) · MongoDB · Claude API via OpenRouter · Azure.

Priorisation pensée pour arriver le plus vite possible à **une démo présentable en rendez-vous commercial**, avec un design unique dès le départ (pas de coquille générique qu'on retape après).

---

## Épique 0 — Identité visuelle & design system SnapDevis
*Objectif : avoir un design distinctif validé avant d'écrire la moindre ligne de logique métier, pour que chaque écran codé ensuite soit déjà "vendable".*

### TICKET-001 — Moodboard et direction artistique SnapDevis
**Priorité : Critique**
- Définir une palette de couleurs propre à SnapDevis (distincte de l'identité Harington), inspirée d'un univers "atelier / bricolage premium" (bois clair, métal brossé, accent technologique net).
- Choisir une typographie principale (titres) et une typographie texte, avec des tailles cohérentes pour titres, sous-titres, corps de texte, labels.
- Produire 3 propositions de logo/wordmark "SnapDevis" (texte stylisé suffisant, pas besoin d'un logo illustré complexe).
- Livrable : fichier de design tokens (couleurs, typographies, espacements, rayons de bordure, ombres) exploitable directement en CSS/Tailwind.
- **Critère d'acceptation** : un fichier `design-tokens.md` ou `.json` avec toutes les valeurs, + un aperçu HTML statique des couleurs/typos appliqués à des composants de base (bouton, carte, titre).

### TICKET-002 — Maquettes des 3 écrans clés (upload / diagnostic / devis)
**Priorité : Critique**
- Maquette haute-fidélité (HTML/CSS statique ou description détaillée) des 3 écrans du parcours : écran d'upload photo, écran de diagnostic/questions de clarification, écran de devis final.
- Soigner particulièrement la transition "photo → devis" : prévoir un effet visuel de scan/analyse qui rend le travail de l'IA tangible à l'oeil pendant une démo live.
- Le devis final doit avoir une mise en page présentable comme un livrable client, pas comme un ticket de caisse.
- **Critère d'acceptation** : 3 maquettes statiques visibles dans le navigateur, validées visuellement avant de démarrer le développement des composants React.

---

## Épique 1 — Socle technique
*Objectif : structure de base fonctionnelle, sans encore la logique IA.*

### TICKET-003 — Setup du projet frontend
**Priorité : Critique**
- Initialiser le projet React 18 + TypeScript + Vite.
- Intégrer les design tokens du TICKET-001 (Tailwind config custom ou CSS variables).
- Mettre en place le routing pour les 3 écrans principaux (upload, diagnostic, devis).
- **Critère d'acceptation** : projet qui démarre en local, navigation entre les 3 écrans avec des données factices (mock), style conforme aux maquettes.

### TICKET-004 — Setup du projet backend
**Priorité : Critique**
- Initialiser FastAPI (Python 3.12), structure de dossiers par domaine (upload, diagnostic, devis, catalogue).
- Connexion MongoDB (variables d'environnement pour la connection string — jamais de valeur en dur, voir note sécurité en fin de document).
- Endpoint de santé `/health`.
- **Critère d'acceptation** : API qui démarre, `/health` répond 200, connexion MongoDB validée par un test simple.

### TICKET-005 — Modèle de données catalogue démo
**Priorité : Critique**
- Concevoir le schéma MongoDB pour le catalogue démo : catégories (peinture, plomberie, fixation, électricité, jardin), produits (nom, référence fictive, prix, unité, catégorie), règles d'association (ex : "mur fissuré" → enduit + spatule + ponceuse + gants).
- Peupler la base avec un jeu de données réaliste (30 à 50 produits fictifs mais crédibles, prix cohérents avec le marché du bricolage).
- **Attention donnée factice uniquement** : noms de produits génériques/fictifs, aucune vraie marque tierce déposée à utiliser sans vérification, prix plausibles mais inventés.
- **Critère d'acceptation** : script de seed exécutable, catalogue consultable via un endpoint `GET /catalogue`.

---

## Épique 2 — Diagnostic IA (photo → besoin identifié)
*Objectif : la brique la plus différenciante techniquement.*

### TICKET-006 — Upload et prétraitement de la photo
**Priorité : Critique**
- Écran d'upload (drag & drop + prise de photo mobile), formats jpg/png/heic.
- Compression/redimensionnement côté client avant envoi.
- Endpoint backend `POST /diagnostic/analyser` qui reçoit l'image.
- **Critère d'acceptation** : une photo uploadée arrive bien côté backend, taille optimisée, retour d'un identifiant de session.

### TICKET-007 — Appel au modèle IA pour le diagnostic visuel
**Priorité : Critique**
- Intégrer l'appel à Claude via OpenRouter avec l'image en entrée.
- Prompt système qui structure la sortie : catégorie de problème détectée, niveau de confiance, besoin ou non de question de clarification.
- Gestion du cas "confiance insuffisante" → génération d'une ou deux questions de clarification à poser à l'utilisateur.
- **Critère d'acceptation** : sur un jeu de 10 photos de test variées (peinture, plomberie, fixation), le diagnostic renvoyé est cohérent pour au moins 8 d'entre elles.

### TICKET-008 — Écran de clarification
**Priorité : Haute**
- Interface qui affiche les questions de clarification générées par le backend et collecte les réponses.
- Renvoi des réponses au backend pour affiner le diagnostic.
- **Critère d'acceptation** : le parcours photo ambiguë → question → réponse → diagnostic affiné fonctionne de bout en bout.

---

## Épique 3 — Génération et édition du devis
*Objectif : transformer le diagnostic en devis chiffré, modifiable.*

### TICKET-009 — Génération du devis à partir du diagnostic
**Priorité : Critique**
- Endpoint `POST /devis/generer` qui croise le diagnostic IA avec le catalogue démo pour produire une liste de produits + quantités suggérées.
- Calcul du total, avec regroupement par catégorie.
- **Critère d'acceptation** : à partir d'un diagnostic donné, un devis structuré (JSON) est généré avec produits, quantités, prix unitaires et total.

### TICKET-010 — Écran de devis interactif
**Priorité : Critique**
- Affichage du devis conforme à la maquette du TICKET-002.
- Actions utilisateur : modifier une quantité, supprimer un article, demander une alternative moins chère (nouvel appel IA restreint au produit concerné).
- **Critère d'acceptation** : toutes les actions mettent à jour le total en temps réel sans rechargement de page.

### TICKET-011 — Export PDF du devis
**Priorité : Haute**
- Génération PDF côté serveur du devis final, mise en page soignée aux couleurs de SnapDevis (ou de l'enseigne pilote si définie).
- **Critère d'acceptation** : le PDF téléchargé reprend fidèlement le contenu du devis affiché à l'écran, avec une mise en page professionnelle.

---

## Épique 4 — Argumentaire commercial (tableau de bord simulation)
*Objectif : donner des chiffres à présenter en rendez-vous.*

### TICKET-012 — Simulation panier moyen avant/après
**Priorité : Moyenne**
- Calculer et afficher, pour chaque devis généré, le delta entre "produit principal seul" et "devis complet SnapDevis".
- Vue agrégée sur l'ensemble des sessions de test (panier moyen simulé).
- **Critère d'acceptation** : un écran (interne, pas forcément client-facing) affiche ces métriques de façon claire et présentable en réunion commerciale.

### TICKET-013 — Historique des sessions
**Priorité : Basse**
- Liste des devis générés précédemment, consultable et réexportable.
- **Critère d'acceptation** : navigation vers un devis passé, réaffichage fidèle.

---

## Notes transverses (toutes tickets)

- **Sécurité des données** : aucune vraie donnée client, aucun vrai catalogue d'enseigne tierce, aucune clé API en dur dans le code — toujours via variables d'environnement référencées par leur nom.
- **Marques tierces** : ne jamais utiliser de vrais logos/marques déposées (Leroy Merlin, Bricorama, etc.) dans le prototype de démo sans accord préalable ; utiliser un branding SnapDevis neutre, adaptable ensuite en marque blanche.
- **Definition of Done** commune : code testé manuellement sur le parcours complet, style conforme aux design tokens, pas de régression sur les écrans précédents.
