import { compresserImage } from './compresserImage'

// Cote du carre recadre, en fraction du plus petit cote de la photo source : assez genereux
// pour tolerer un pointage imprecis (doigt sur un petit écran) sans perdre la zone visee.
const MARGE_RATIO = 0.4
const QUALITE_JPEG = 0.92

export async function recadrerZoom(fichier: File, point: { x: number; y: number }): Promise<File | null> {
  if (!fichier.type.startsWith('image/') || fichier.type === 'image/heic') {
    // pas decodable de maniere fiable par un canvas : mieux vaut renoncer au zoom que
    // d'envoyer un crop errone a l'IA
    return null
  }

  const bitmap = await createImageBitmap(fichier)
  const cote = Math.round(Math.min(bitmap.width, bitmap.height) * MARGE_RATIO)
  if (cote <= 0) {
    bitmap.close()
    return null
  }

  const centreX = point.x * bitmap.width
  const centreY = point.y * bitmap.height
  const sx = Math.max(0, Math.min(bitmap.width - cote, Math.round(centreX - cote / 2)))
  const sy = Math.max(0, Math.min(bitmap.height - cote, Math.round(centreY - cote / 2)))

  const canvas = document.createElement('canvas')
  canvas.width = cote
  canvas.height = cote
  const contexte = canvas.getContext('2d')
  if (!contexte) {
    bitmap.close()
    return null
  }

  contexte.drawImage(bitmap, sx, sy, cote, cote, 0, 0, cote, cote)
  bitmap.close()

  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', QUALITE_JPEG))
  if (!blob) return null

  const nomZoom = `${fichier.name.replace(/\.\w+$/, '')}-zoom.jpg`
  const fichierZoom = new File([blob], nomZoom, { type: 'image/jpeg' })
  return compresserImage(fichierZoom)
}
