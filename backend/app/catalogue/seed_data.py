"""Jeu de données démo SnapDevis : produits et references fictifs, prix plausibles
mais inventes. Aucune vraie marque tierce, aucun vrai catalogue d'enseigne."""

PRODUITS: list[dict] = [
    # Peinture
    {"reference": "PT-001", "nom": "Peinture acrylique mate blanche 2.5L", "categorie": "peinture", "prix": 24.90, "unite": "pot"},
    {"reference": "PT-002", "nom": "Enduit de rebouchage 1kg", "categorie": "peinture", "prix": 8.90, "unite": "pot"},
    {"reference": "PT-003", "nom": "Sous-couche universelle 1L", "categorie": "peinture", "prix": 11.50, "unite": "bidon"},
    {"reference": "PT-004", "nom": "Rouleau à peinture 18cm", "categorie": "peinture", "prix": 6.20, "unite": "unité"},
    {"reference": "PT-005", "nom": "Pinceau plat 40mm", "categorie": "peinture", "prix": 3.80, "unite": "unité"},
    {"reference": "PT-006", "nom": "Ruban de masquage 50m", "categorie": "peinture", "prix": 4.50, "unite": "rouleau"},
    {"reference": "PT-007", "nom": "Bâche de protection 4x5m", "categorie": "peinture", "prix": 5.90, "unite": "unité"},
    {"reference": "PT-008", "nom": "Spatule inox 10cm", "categorie": "peinture", "prix": 4.50, "unite": "unité"},
    {"reference": "PT-009", "nom": "Ponceuse manuelle bloc", "categorie": "peinture", "prix": 12.00, "unite": "unité"},
    {"reference": "PT-010", "nom": "Gants de protection latex", "categorie": "peinture", "prix": 3.20, "unite": "paire"},
    # Plomberie
    {"reference": "PL-001", "nom": "Joint fibre pour robinet (lot de 5)", "categorie": "plomberie", "prix": 2.10, "unite": "lot"},
    {"reference": "PL-002", "nom": "Flexible douche 1.5m", "categorie": "plomberie", "prix": 9.90, "unite": "unité"},
    {"reference": "PL-003", "nom": "Ruban téflon PTFE", "categorie": "plomberie", "prix": 1.80, "unite": "rouleau"},
    {"reference": "PL-004", "nom": "Clé à molette 250mm", "categorie": "plomberie", "prix": 14.50, "unite": "unité"},
    {"reference": "PL-005", "nom": "Siphon lavabo universel", "categorie": "plomberie", "prix": 12.90, "unite": "unité"},
    {"reference": "PL-006", "nom": "Mitigeur lavabo standard", "categorie": "plomberie", "prix": 45.00, "unite": "unité"},
    {"reference": "PL-007", "nom": "Colle joint silicone sanitaire", "categorie": "plomberie", "prix": 6.50, "unite": "tube"},
    {"reference": "PL-008", "nom": "Pince multiprise", "categorie": "plomberie", "prix": 16.90, "unite": "unité"},
    # Fixation
    {"reference": "FX-001", "nom": "Chevilles universelles (lot de 50)", "categorie": "fixation", "prix": 5.40, "unite": "boîte"},
    {"reference": "FX-002", "nom": "Vis à bois 4x40 (lot de 100)", "categorie": "fixation", "prix": 6.80, "unite": "boîte"},
    {"reference": "FX-003", "nom": "Chevilles Molly (lot de 10)", "categorie": "fixation", "prix": 7.20, "unite": "boîte"},
    {"reference": "FX-004", "nom": "Équerre de fixation métal", "categorie": "fixation", "prix": 2.30, "unite": "unité"},
    {"reference": "FX-005", "nom": "Rail de fixation murale 1m", "categorie": "fixation", "prix": 9.50, "unite": "unité"},
    {"reference": "FX-006", "nom": "Perceuse-visseuse sans fil 12V", "categorie": "fixation", "prix": 59.00, "unite": "unité"},
    {"reference": "FX-007", "nom": "Foret béton 6mm", "categorie": "fixation", "prix": 3.40, "unite": "unité"},
    {"reference": "FX-008", "nom": "Niveau à bulle 40cm", "categorie": "fixation", "prix": 8.90, "unite": "unité"},
    # Électricité
    {"reference": "EL-001", "nom": "Ampoule LED E27 9W", "categorie": "electricite", "prix": 4.90, "unite": "unité"},
    {"reference": "EL-002", "nom": "Interrupteur va-et-vient", "categorie": "electricite", "prix": 6.20, "unite": "unité"},
    {"reference": "EL-003", "nom": "Prise de courant 2P+T", "categorie": "electricite", "prix": 5.80, "unite": "unité"},
    {"reference": "EL-004", "nom": "Câble électrique 3G1.5 (5m)", "categorie": "electricite", "prix": 7.90, "unite": "unité"},
    {"reference": "EL-005", "nom": "Domino de connexion (lot de 10)", "categorie": "electricite", "prix": 2.50, "unite": "boîte"},
    {"reference": "EL-006", "nom": "Testeur de tension", "categorie": "electricite", "prix": 9.90, "unite": "unité"},
    {"reference": "EL-007", "nom": "Rallonge électrique 5m", "categorie": "electricite", "prix": 11.50, "unite": "unité"},
    {"reference": "EL-008", "nom": "Boîte de dérivation étanche", "categorie": "electricite", "prix": 4.30, "unite": "unité"},
    # Jardin
    {"reference": "JD-001", "nom": "Terreau universel 40L", "categorie": "jardin", "prix": 8.50, "unite": "sac"},
    {"reference": "JD-002", "nom": "Sécateur ergonomique", "categorie": "jardin", "prix": 14.90, "unite": "unité"},
    {"reference": "JD-003", "nom": "Gants de jardinage", "categorie": "jardin", "prix": 5.90, "unite": "paire"},
    {"reference": "JD-004", "nom": "Tuyau d'arrosage 20m", "categorie": "jardin", "prix": 22.90, "unite": "unité"},
    {"reference": "JD-005", "nom": "Engrais gazon 5kg", "categorie": "jardin", "prix": 13.50, "unite": "sac"},
    {"reference": "JD-006", "nom": "Bêche manche bois", "categorie": "jardin", "prix": 18.90, "unite": "unité"},
    {"reference": "JD-007", "nom": "Sac de plantation 10L", "categorie": "jardin", "prix": 6.90, "unite": "unité"},
    {"reference": "JD-008", "nom": "Pulvérisateur 5L", "categorie": "jardin", "prix": 12.90, "unite": "unité"},
]

REGLES_ASSOCIATION: list[dict] = [
    {"probleme": "mur_fissure_interieur", "references_produits": ["PT-002", "PT-008", "PT-009", "PT-010"]},
    {"probleme": "mur_fissure_exterieur", "references_produits": ["PT-002", "PT-008", "PT-009", "PT-010", "PT-006"]},
    {"probleme": "mur_a_repeindre", "references_produits": ["PT-001", "PT-003", "PT-004", "PT-005", "PT-006", "PT-007"]},
    {"probleme": "robinet_qui_fuit", "references_produits": ["PL-001", "PL-003", "PL-004"]},
    {"probleme": "mitigeur_a_remplacer", "references_produits": ["PL-006", "PL-003", "PL-007", "PL-004"]},
    {"probleme": "siphon_bouche_ou_a_remplacer", "references_produits": ["PL-005", "PL-007", "PL-004"]},
    {"probleme": "etagere_a_fixer", "references_produits": ["FX-001", "FX-002", "FX-006", "FX-008"]},
    {"probleme": "objet_lourd_a_fixer_placo", "references_produits": ["FX-003", "FX-006", "FX-008"]},
    {"probleme": "prise_ou_interrupteur_defectueux", "references_produits": ["EL-002", "EL-003", "EL-006", "EL-005"]},
    {"probleme": "eclairage_a_installer", "references_produits": ["EL-001", "EL-002", "EL-004", "EL-005"]},
    {"probleme": "entretien_jardin", "references_produits": ["JD-001", "JD-002", "JD-003"]},
    {"probleme": "arrosage_exterieur", "references_produits": ["JD-004", "JD-005"]},
]
