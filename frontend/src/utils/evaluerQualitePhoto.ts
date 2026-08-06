// Heuristique legere (variance du laplacien pour la nettete, luminosite moyenne pour l'exposition)
// calculee sur une version reduite de l'image : suffisant pour repartir un avertissement, pas pour
// une mesure scientifique. Seuils choisis pour ne signaler que les cas nets (image plate/tres sombre),
// afin d'eviter de faux avertissements sur de vraies photos texturees.
const TAILLE_ANALYSE_PX = 200
const SEUIL_NETTETE = 12
const SEUIL_LUMINOSITE = 35

export type QualitePhoto = {
  floue: boolean
  sombre: boolean
}

export async function evaluerQualitePhoto(fichier: File): Promise<QualitePhoto> {
  if (!fichier.type.startsWith('image/') || fichier.type === 'image/heic') {
    // pas decodable de maniere fiable par un canvas : on ne bloque ni n'avertit a tort
    return { floue: false, sombre: false }
  }

  const bitmap = await createImageBitmap(fichier)
  const ratio = Math.min(1, TAILLE_ANALYSE_PX / Math.max(bitmap.width, bitmap.height))
  const largeur = Math.max(1, Math.round(bitmap.width * ratio))
  const hauteur = Math.max(1, Math.round(bitmap.height * ratio))

  const canvas = document.createElement('canvas')
  canvas.width = largeur
  canvas.height = hauteur
  const contexte = canvas.getContext('2d')
  if (!contexte) {
    bitmap.close()
    return { floue: false, sombre: false }
  }

  contexte.drawImage(bitmap, 0, 0, largeur, hauteur)
  bitmap.close()

  const { data } = contexte.getImageData(0, 0, largeur, hauteur)
  const gris = new Float32Array(largeur * hauteur)
  let sommeLuminosite = 0

  for (let i = 0; i < largeur * hauteur; i++) {
    const r = data[i * 4]
    const g = data[i * 4 + 1]
    const b = data[i * 4 + 2]
    const luminosite = 0.299 * r + 0.587 * g + 0.114 * b
    gris[i] = luminosite
    sommeLuminosite += luminosite
  }

  let sommeLaplacien = 0
  let sommeLaplacienCarre = 0
  let compte = 0

  for (let y = 1; y < hauteur - 1; y++) {
    for (let x = 1; x < largeur - 1; x++) {
      const idx = y * largeur + x
      const laplacien = gris[idx - largeur] + gris[idx + largeur] + gris[idx - 1] + gris[idx + 1] - 4 * gris[idx]
      sommeLaplacien += laplacien
      sommeLaplacienCarre += laplacien * laplacien
      compte++
    }
  }

  const moyenneLaplacien = compte > 0 ? sommeLaplacien / compte : 0
  const varianceLaplacien = compte > 0 ? sommeLaplacienCarre / compte - moyenneLaplacien * moyenneLaplacien : 0
  const luminositeMoyenne = sommeLuminosite / (largeur * hauteur)

  return {
    floue: varianceLaplacien < SEUIL_NETTETE,
    sombre: luminositeMoyenne < SEUIL_LUMINOSITE,
  }
}
