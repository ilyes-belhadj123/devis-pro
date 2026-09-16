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
        className={`chatbot-fab ${ouvert ? 'chatbot-fab-ouvert' : ''}`}
        onClick={() => setOuvert((valeur) => !valeur)}
        aria-label="Assistant SnapDevis"
        title="Une question sur ce devis ?"
      >
        <span className="chatbot-fab-ring" />
        <span className="chatbot-fab-ring chatbot-fab-ring-2" />
        <span className="chatbot-fab-icon">{ouvert ? '×' : '👷'}</span>
      </button>

      {ouvert && (
        <div className="chatbot-panel">
          <div className="chatbot-panel-header">
            <span className="chatbot-panel-title">👷 Assistant SnapDevis</span>
            <span className="chatbot-panel-sub">Une question sur ce devis ?</span>
          </div>

          <div className="chatbot-panel-body">
            {messages.length === 0 && (
              <p className="chatbot-empty">
                Posez-moi une question sur ce devis précis — quantités, prix, produits utilisés…
              </p>
            )}
            {messages.map((message, index) => (
              <div key={index} className={`chatbot-bulle chatbot-bulle-${message.role}`}>
                {message.content}
              </div>
            ))}
            {enCours && (
              <div className="chatbot-bulle chatbot-bulle-assistant chatbot-bulle-loading">
                <span />
                <span />
                <span />
              </div>
            )}
            <div ref={finRef} />
          </div>

          {messages.length === 0 && (
            <div className="chatbot-suggestions">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  className="chatbot-suggestion-chip"
                  onClick={() => envoyer(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}

          <form
            className="chatbot-panel-input"
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
