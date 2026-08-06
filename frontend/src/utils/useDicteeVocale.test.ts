import { describe, expect, it } from 'vitest'
import { dicteeVocaleDisponible } from './useDicteeVocale'

describe('dicteeVocaleDisponible', () => {
  it("renvoie false quand l'API SpeechRecognition n'existe pas (ex: jsdom, Firefox)", () => {
    expect(dicteeVocaleDisponible()).toBe(false)
  })
})
