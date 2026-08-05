export const ICONES_CATEGORIE: Record<string, string> = {
  peinture: '🎨',
  plomberie: '🔧',
  fixation: '🪛',
  electricite: '💡',
  jardin: '🌱',
}

export function iconePourCategorie(categorie: string): string {
  return ICONES_CATEGORIE[categorie.toLowerCase()] ?? '🛠️'
}
