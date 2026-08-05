import { afterEach, describe, expect, it, vi } from 'vitest'
import { genererDevis } from './api'

describe('genererDevis — propagation des erreurs backend', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('propage le detail renvoye par le backend plutot qu\'un message generique', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({ detail: "Aucune règle d'association pour 'xyz'" }),
      }),
    )

    await expect(genererDevis('xyz')).rejects.toThrow("Aucune règle d'association pour 'xyz'")
  })

  it('retombe sur un message par defaut si le corps de la reponse n\'est pas exploitable', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('corps non JSON')
        },
      }),
    )

    await expect(genererDevis('xyz')).rejects.toThrow('Erreur 500')
  })
})
