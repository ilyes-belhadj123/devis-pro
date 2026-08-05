import { describe, expect, it } from 'vitest'
import { compresserImage } from './compresserImage'

describe('compresserImage', () => {
  it('laisse passer un fichier HEIC sans le modifier (non decodable par un canvas)', async () => {
    const fichier = new File(['contenu'], 'photo.heic', { type: 'image/heic' })
    const resultat = await compresserImage(fichier)
    expect(resultat).toBe(fichier)
  })

  it('laisse passer un fichier non-image sans le modifier', async () => {
    const fichier = new File(['contenu'], 'document.pdf', { type: 'application/pdf' })
    const resultat = await compresserImage(fichier)
    expect(resultat).toBe(fichier)
  })
})
