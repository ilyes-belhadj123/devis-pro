// Correction simple gain+decalage (pas d'egalisation d'histogramme, trop couteuse pour un geste
// instantane cote client) : suffisant pour rendre une photo sombre exploitable par l'IA vision.
const FACTEUR_GAIN = 1.6
const DECALAGE = 25
const QUALITE_JPEG = 0.92

export async function eclaircirImage(fichier: File): Promise<File> {
  if (!fichier.type.startsWith('image/') || fichier.type === 'image/heic') {
    return fichier
  }

  const bitmap = await createImageBitmap(fichier)
  const canvas = document.createElement('canvas')
  canvas.width = bitmap.width
  canvas.height = bitmap.height
  const contexte = canvas.getContext('2d')
  if (!contexte) {
    bitmap.close()
    return fichier
  }

  contexte.drawImage(bitmap, 0, 0)
  bitmap.close()

  const imageData = contexte.getImageData(0, 0, canvas.width, canvas.height)
  const { data } = imageData
  for (let i = 0; i < data.length; i += 4) {
    data[i] = Math.min(255, data[i] * FACTEUR_GAIN + DECALAGE)
    data[i + 1] = Math.min(255, data[i + 1] * FACTEUR_GAIN + DECALAGE)
    data[i + 2] = Math.min(255, data[i + 2] * FACTEUR_GAIN + DECALAGE)
  }
  contexte.putImageData(imageData, 0, 0)

  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', QUALITE_JPEG))
  if (!blob) return fichier

  return new File([blob], fichier.name.replace(/\.\w+$/, '.jpg'), { type: 'image/jpeg' })
}
