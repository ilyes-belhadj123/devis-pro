// Simule des creneaux d'intervention disponibles, de maniere deterministe a partir de
// l'identifiant du devis (pas de vrai systeme de planification/calendrier artisan derriere -
// prototype de demo, meme esprit que le comparateur de fournisseurs simule).
const PLAGES_HORAIRES = ['8h - 10h', '10h - 12h', '14h - 16h', '16h - 18h']

function hashSimple(texte: string): number {
  let hachage = 0
  for (let i = 0; i < texte.length; i++) {
    hachage = (hachage * 31 + texte.charCodeAt(i)) >>> 0
  }
  return hachage
}

export type Creneau = { id: string; libelle: string }

export function genererCreneaux(devisId: string): Creneau[] {
  const base = hashSimple(devisId)

  return Array.from({ length: 3 }, (_, i) => {
    const decalageJours = 2 + i * 2 + ((base >> (i * 4)) % 3)
    const date = new Date()
    date.setDate(date.getDate() + decalageJours)
    const jourLabel = date.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })
    const plage = PLAGES_HORAIRES[(base >> (8 + i * 3)) % PLAGES_HORAIRES.length]

    return {
      id: String(i),
      libelle: `${jourLabel.charAt(0).toUpperCase()}${jourLabel.slice(1)} · ${plage}`,
    }
  })
}
