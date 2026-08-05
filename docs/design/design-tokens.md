# SnapDevis — Design system (v2, révisé après retours démo)

## Direction artistique

**"Retail énergique"** : après une première direction "atelier premium" (bois clair, cuivre terne), le design a été révisé pour se rapprocher des codes visuels des sites e-commerce bricolage/déco qui convertissent bien (IKEA, Conforama) — sans copier leur identité (couleurs propres à SnapDevis, cf. note ci-dessous).

- **Fond clair et net** (blanc / quasi-blanc) plutôt qu'une texture bois — plus universel, plus "produit fini" pour une démo commerciale.
- **Accent corail** (`copper`, nom du token conservé) : couleur de marque vive, à fort contraste sur blanc, utilisée pour les CTA principaux. Choisie distincte du jaune IKEA, de l'orange Bricorama, du vert Leroy Merlin et du bleu Castorama pour rester une marque neutre, revendable en marque blanche (contrainte du cahier des charges).
- **Accent teal** (`tech`) toujours réservé aux moments IA (scan, diagnostic, confiance) — inchangé, c'est ce qui rend le travail de l'IA visible pendant une démo.
- **Espace généreux** et hiérarchie claire (inspiré de la lisibilité des grilles produit IKEA) plutôt qu'une mise en page dense.

## Typographie

| Rôle | Police | Justification |
|---|---|---|
| Titres | **Sora** (sans, bold) | Géométrique, moderne, chaleureux sans être froid — lisible et "confiant" pour des titres d'accroche commerciale. |
| Texte / UI / chiffres | **Space Grotesk** (sans) | Conservé : précision géométrique, excellent pour les prix (chiffres tabulaires) et les labels. |

Une seule famille sans-serif dans toute l'app (plus de serif) pour une lecture plus rapide et un rendu plus "produit logiciel" que "éditorial".

## Couleurs

| Token | Valeur | Usage |
|---|---|---|
| `background.base` | `#FBFAF8` | Fond général (quasi-blanc) |
| `background.surface` | `#FFFFFF` | Cartes, panneaux |
| `background.surfaceSunken` | `#F3F1ED` | Zones creuses (dropzone, sections secondaires) |
| `text.primary` | `#1F2129` | Texte principal |
| `text.secondary` | `#6B7280` | Texte secondaire |
| `border.default` | `#E5E3DD` | Bordures discrètes |
| `border.strong` | `#C9C6BC` | Bordures marquées |
| `accent.copper` | `#FF5A3C` | Marque, CTA principal (corail) |
| `accent.tech` | `#14B8A6` | IA / scan / diagnostic uniquement |
| `metal.100 → 700` | `#F4F4F5 → #52525B` | Neutres gris (fonds de badges, séparateurs) |
| `state.success/warning/error` | `#16A34A` / `#D97706` / `#DC2626` | Feedback système |

Ombres neutres froides (jamais teintées) : `shadow.sm/md/lg`, base `rgba(15, 23, 42, …)`.

Effet dédié : `effect.scanGradient` — dégradé teal utilisé pour l'animation de balayage lors de la transition photo → devis.

## Espacements et rayons

Échelle d'espacement en base 4/8 (`space.1` à `space.9`, de 4px à 96px). Rayons relevés par rapport à la v1 : `sm` 8px / `md` 12px / `lg` 20px / `pill` 999px — plus arrondis, plus "accessible/friendly" que la version atelier.

## Wordmark

`Snap·Devis` conservé — "Snap" en corail, séparateur point en teal, "Devis" en encre. Fonctionne aussi bien sur fond blanc que sur les nouveaux accents vifs.

## Fichiers

- `design-tokens.json` — valeurs brutes, exploitables directement (CSS vars / Tailwind theme).
- `design-tokens.css` — variables CSS + classes de base, prêtes à copier.
- `design-tokens.md` — ce document (rationale + valeurs).

La référence vivante est désormais l'app elle-même (`frontend/src/index.css` + `App.css`) ; ces fichiers documentent l'intention mais peuvent dériver légèrement des valeurs exactes en cas d'ajustement rapide non reporté ici.
