import { useEffect, useRef, useState } from 'react'

// API Web Speech (SpeechRecognition) : non standardisee dans lib.dom, disponible sur
// Chrome/Edge (prefixe webkit encore necessaire), absente sur Firefox et limitee sur Safari.
// On detecte sa presence a l'execution plutot que de supposer qu'elle existe.
type ReconnaissanceVocaleInstance = {
  lang: string
  interimResults: boolean
  continuous: boolean
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null
  onerror: (() => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
}

type FenetreAvecReconnaissanceVocale = Window & {
  SpeechRecognition?: new () => ReconnaissanceVocaleInstance
  webkitSpeechRecognition?: new () => ReconnaissanceVocaleInstance
}

function obtenirConstructeur(): (new () => ReconnaissanceVocaleInstance) | null {
  if (typeof window === 'undefined') return null
  const fenetre = window as FenetreAvecReconnaissanceVocale
  return fenetre.SpeechRecognition ?? fenetre.webkitSpeechRecognition ?? null
}

export function dicteeVocaleDisponible(): boolean {
  return obtenirConstructeur() !== null
}

export function useDicteeVocale(onTranscription: (texte: string) => void) {
  const [ecoute, setEcoute] = useState(false)
  const reconnaissanceRef = useRef<ReconnaissanceVocaleInstance | null>(null)

  useEffect(() => {
    return () => {
      reconnaissanceRef.current?.stop()
    }
  }, [])

  const basculer = () => {
    if (ecoute) {
      reconnaissanceRef.current?.stop()
      return
    }

    const Constructeur = obtenirConstructeur()
    if (!Constructeur) return

    const reconnaissance = new Constructeur()
    reconnaissance.lang = 'fr-FR'
    reconnaissance.interimResults = false
    reconnaissance.continuous = false
    reconnaissance.onresult = (event) => {
      const dernier = event.results[event.results.length - 1]
      const transcript = dernier?.[0]?.transcript
      if (transcript) onTranscription(transcript)
    }
    reconnaissance.onerror = () => setEcoute(false)
    reconnaissance.onend = () => setEcoute(false)

    reconnaissanceRef.current = reconnaissance
    setEcoute(true)
    reconnaissance.start()
  }

  return { ecoute, disponible: dicteeVocaleDisponible(), basculer }
}
