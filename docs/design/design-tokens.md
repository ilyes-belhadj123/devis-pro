# SnapDevis — Design system (TICKET-001)

## Direction artistique

**"Atelier premium"** : l'univers visuel doit évoquer le geste technique et le matériau (bois clair, métal brossé) sans tomber dans le "artisanal daté", et intégrer un accent technologique net qui rend le travail de l'IA tangible — sans ressembler à "un énième chatbot IA générique".

- **Fond chaud** (linen / bois clair) plutôt que blanc pur ou gris SaaS générique.
- **Encre charbon chaud** pour le texte, jamais de noir pur.
- **Accent cuivre** (`copper`) comme couleur de marque — matière, chaleur, geste manuel — utilisé pour les actions principales et les éléments de marque.
- **Accent teal** (`tech`) réservé exclusivement aux moments IA : ligne de scan photo → devis, badges de diagnostic, indicateurs de confiance. Il ne doit jamais se substituer au cuivre pour les actions standards — c'est ce qui rend le travail de l'IA "visible" pendant une démo.
- Distinct des identités des enseignes ciblées (pas de vert Leroy Merlin, pas d'orange Bricorama, pas de bleu Castorama) et de l'identité Harington.

## Typographie

| Rôle | Police | Justification |
|---|---|---|
| Titres | **Fraunces** (serif variable) | Chaleur et caractère "matière" — évite le générique SaaS tout en restant premium, pas "daté artisanal". |
| Texte / UI / chiffres | **Space Grotesk** (sans) | Précision géométrique, incarne l'"accent technologique net" ; excellent pour les prix (chiffres tabulaires) et les labels. |

Échelle : `display` 44px → `h1` 36px → `h2` 28px → `h3` 22px → `body` 16px → `bodySmall` 14px → `label` 13px (majuscules, espacé).

## Couleurs

| Token | Valeur | Usage |
|---|---|---|
| `background.base` | `#F6F1E8` | Fond général (linen / bois clair) |
| `background.surface` | `#FFFDF9` | Cartes, panneaux |
| `background.surfaceSunken` | `#EDE6D8` | Zones creuses (dropzone, sections secondaires) |
| `text.primary` | `#2A2521` | Texte principal (charbon chaud) |
| `text.secondary` | `#6B6259` | Texte secondaire |
| `border.default` | `#DED6C7` | Bordures discrètes |
| `border.strong` | `#B8ADA0` | Bordures marquées (métal brossé) |
| `accent.copper` | `#C1662F` | Marque, CTA principal |
| `accent.tech` | `#15B8B0` | IA / scan / diagnostic uniquement |
| `metal.100 → 700` | `#F1EFEC → #5B5750` | Neutres "métal brossé" (fonds de badges, icônes, séparateurs) |
| `state.success/warning/error` | `#3F8F5F` / `#D69A2D` / `#C1392B` | Feedback système |

Ombres teintées chaudes (jamais de noir pur) : `shadow.sm/md/lg`, base `rgba(43, 37, 30, …)`.

Effet dédié : `effect.scanGradient` — dégradé teal utilisé pour l'animation de balayage lors de la transition photo → devis (TICKET-002).

## Espacements et rayons

Échelle d'espacement en base 4/8 (`space.1` à `space.9`, de 4px à 96px). Rayons `sm` 6px / `md` 10px / `lg` 16px / `pill` 999px — arrondis modérés, pour rester "structuré atelier" plutôt que "bulle SaaS".

## Propositions de wordmark (3)

1. **`Snap·Devis`** — "Snap" en Space Grotesk semibold cuivre, séparateur point en teal, "Devis" en Fraunces regular charbon. Évoque à la fois le déclic photo (Snap) et le document (Devis).
2. **`SNAPDEVIS`** — capitales Space Grotesk, monospatiale visuelle, avec une entaille diagonale teal traversant le "A" central façon ligne de scan.
3. **`snap`Devis** — "snap" en Fraunces italic minuscule (geste, matière), "Devis" en Space Grotesk majuscules (précision), soulignés d'une barre d'accent teal.

Les 3 variantes sont rendues dans l'aperçu HTML (`preview.html`) pour choix visuel.

## Fichiers livrés

- `design-tokens.json` — valeurs brutes, exploitables directement (CSS vars / Tailwind theme).
- `design-tokens.md` — ce document (rationale + valeurs).
- `preview.html` — aperçu statique : palette, typographies, bouton, carte, titre, 3 wordmarks.

**À valider visuellement avant de démarrer TICKET-002 (maquettes) et l'intégration dans le frontend (TICKET-003).**
