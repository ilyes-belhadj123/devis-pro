import { describe, expect, it } from 'vitest'
import { recadrerZoom } from './recadrerZoom'

describe('recadrerZoom', () => {
  it('renvoie null pour un fichier HEIC (non decodable par un canvas)', async () => {
    const fichier = new File(['contenu'], 'photo.heic', { type: 'image/heic' })
    const resultat = await recadrerZoom(fichier, { x: 0.5, y: 0.5 })
    expect(resultat).toBeNull()
  })

  it('renvoie null pour un fichier non-image', async () => {
    const fichier = new File(['contenu'], 'document.pdf', { type: 'application/pdf' })
    const resultat = await recadrerZoom(fichier, { x: 0.5, y: 0.5 })
    expect(resultat).toBeNull()
  })
})
