const TAILLE_MAX_PX = 1600
const QUALITE_JPEG = 0.82

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
