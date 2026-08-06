import { describe, expect, it } from 'vitest'
import { evaluerQualitePhoto } from './evaluerQualitePhoto'

describe('evaluerQualitePhoto', () => {
  it("n'avertit pas a tort sur un fichier HEIC (non decodable par un canvas)", async () => {
    const fichier = new File(['contenu'], 'photo.heic', { type: 'image/heic' })
    const resultat = await evaluerQualitePhoto(fichier)
    expect(resultat).toEqual({ floue: false, sombre: false })
  })

  it("n'avertit pas a tort sur un fichier non-image", async () => {
    const fichier = new File(['contenu'], 'document.pdf', { type: 'application/pdf' })
    const resultat = await evaluerQualitePhoto(fichier)
    expect(resultat).toEqual({ floue: false, sombre: false })
  })
})
