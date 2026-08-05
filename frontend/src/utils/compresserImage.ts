// 1568px correspond au redimensionnement interne des modeles de vision Claude : au-dela,
// l'image est de toute facon redimensionnee cote IA sans gain de precision. La qualite JPEG
// est volontairement elevee pour ne pas lisser les details fins (largeur d'une fissure,
// texture d'un materiau) qui comptent pour un diagnostic precis.
const TAILLE_MAX_PX = 1568
const QUALITE_JPEG = 0.92

/**
 * Redimensionne et recompresse une image côté client avant envoi (TICKET-006).
 * Le HEIC n'est pas décodable par un canvas dans la plupart des navigateurs :
 * on le laisse passer tel quel, le backend le recevra sans prétraitement.
 */
export async function compresserImage(fichier: File): Promise<File> {
  if (!fichier.type.startsWith('image/') || fichier.type === 'image/heic') {
    return fichier
  }

  const bitmap = await createImageBitmap(fichier)
  const ratio = Math.min(1, TAILLE_MAX_PX / Math.max(bitmap.width, bitmap.height))
  const largeur = Math.round(bitmap.width * ratio)
  const hauteur = Math.round(bitmap.height * ratio)

  const canvas = document.createElement('canvas')
  canvas.width = largeur
  canvas.height = hauteur
  const contexte = canvas.getContext('2d')
  if (!contexte) return fichier

  contexte.drawImage(bitmap, 0, 0, largeur, hauteur)
  bitmap.close()

  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', QUALITE_JPEG))
  if (!blob) return fichier

  const nomCompresse = fichier.name.replace(/\.\w+$/, '.jpg')
  return new File([blob], nomCompresse, { type: 'image/jpeg' })
}
