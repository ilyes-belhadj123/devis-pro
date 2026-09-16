import { useEffect, useRef, useState } from 'react'
import { demanderAssistant, type LigneDevisPourPdf, type MessageAssistantApi } from '../api'
import './ChatbotDevis.css'

type ChatbotDevisProps = {
  lignes: LigneDevisPourPdf[]
  total: number
}

const SUGGESTIONS = ['Pourquoi cette quantité ?', 'Puis-je réduire le budget ?', "C'est quoi cette ligne ?"]

function ChatbotDevis({ lignes, total }: ChatbotDevisProps) {
  const [ouvert, setOuvert] = useState(false)
  const [messages, setMessages] = useState<MessageAssistantApi[]>([])
  const [saisie, setSaisie] = useState('')
  const [enCours, setEnCours] = useState(false)
  const finRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (ouvert) finRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, ouvert, enCours])

  const envoyer = async (texte: string) => {
    const contenu = texte.trim()
    if (!contenu || enCours) return

    const historique: MessageAssistantApi[] = [...messages, { role: 'user', content: contenu }]
    setMessages(historique)
    setSaisie('')
    setEnCours(true)

    try {
      const resultat = await demanderAssistant(lignes, total, historique)
      setMessages((precedent) => [...precedent, { role: 'assistant', content: resultat.reponse }])
    } catch (err) {
      setMessages((precedent) => [
        ...precedent,
        {
          role: 'assistant',
          content: err instanceof Error ? err.message : "Erreur lors de la réponse de l'assistant.",
        },
      ])
    } finally {
      setEnCours(false)
    }
  }

  return (
    <>
      <button
        type="button"
        className={`sd-assistant-fab ${ouvert ? 'sd-assistant-fab-ouvert' : ''}`}
        onClick={() => setOuvert((valeur) => !valeur)}
        aria-label="Assistant SnapDevis"
        title="Une question sur ce devis ?"
      >
        <span className="sd-assistant-fab-ring" />
        <span className="sd-assistant-fab-ring sd-assistant-fab-ring-2" />
        <span className="sd-assistant-fab-icon">{ouvert ? '×' : '👷'}</span>
      </button>

      {ouvert && (
        <div className="sd-assistant-panel">
          <div className="sd-assistant-panel-header">
            <span className="sd-assistant-panel-title">👷 Assistant SnapDevis</span>
            <span className="sd-assistant-panel-sub">Une question sur ce devis ?</span>
          </div>

          <div className="sd-assistant-panel-body">
            {messages.length === 0 && (
              <p className="sd-assistant-empty">
                Posez-moi une question sur ce devis précis — quantités, prix, produits utilisés…
              </p>
            )}
            {messages.map((message, index) => (
              <div key={index} className={`sd-assistant-bulle sd-assistant-bulle-${message.role}`}>
                {message.content}
              </div>
            ))}
            {enCours && (
              <div className="sd-assistant-bulle sd-assistant-bulle-assistant sd-assistant-bulle-loading">
                <span />
                <span />
                <span />
              </div>
            )}
            <div ref={finRef} />
          </div>

          {messages.length === 0 && (
            <div className="sd-assistant-suggestions">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  className="sd-assistant-suggestion-chip"
                  onClick={() => envoyer(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}

          <form
            className="sd-assistant-panel-input"
            onSubmit={(event) => {
              event.preventDefault()
              envoyer(saisie)
            }}
          >
            <input
              type="text"
              value={saisie}
              onChange={(event) => setSaisie(event.target.value)}
              placeholder="Votre question…"
              disabled={enCours}
            />
            <button type="submit" className="btn btn-primary" disabled={enCours || !saisie.trim()}>
              →
            </button>
          </form>
        </div>
      )}
    </>
  )
}

export default ChatbotDevis
