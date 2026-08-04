import { useEffect, useState } from 'react'
import { definirCleOpenRouter, getStatutCleOpenRouter } from '../api'
import './ParametresPage.css'

function ParametresPage() {
  const [configuree, setConfiguree] = useState<boolean | null>(null)
  const [valeur, setValeur] = useState('')
  const [statutMessage, setStatutMessage] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)

  useEffect(() => {
    getStatutCleOpenRouter()
      .then((res) => setConfiguree(res.configuree))
      .catch(() => setConfiguree(null))
  }, [])

  const enregistrer = async () => {
    if (!valeur.trim()) return
    setIsSaving(true)
    setErreur(null)
    setStatutMessage(null)
    try {
      const res = await definirCleOpenRouter(valeur.trim())
      setConfiguree(res.configuree)
      setValeur('')
      setStatutMessage('Clé enregistrée. Le diagnostic IA utilisera cette clé pour les prochaines analyses.')
    } catch {
      setErreur("Impossible d'enregistrer la clé — vérifiez que l'API backend est bien lancée.")
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <section className="page">
      <span className="page-eyebrow">Paramètres</span>
      <h1>Clé API OpenRouter</h1>
      <p className="page-lead">
        Utilisée pour le diagnostic IA (analyse de la photo). La clé est stockée côté serveur uniquement —
        elle n'est jamais renvoyée au navigateur ni visible dans le code source.
      </p>

      <div className="card parametres-card">
        {configuree !== null && (
          <span className={`badge ${configuree ? 'badge-ok' : 'badge-off'}`}>
            {configuree ? '● Clé configurée' : '○ Aucune clé configurée — diagnostic simulé'}
          </span>
        )}

        <label className="parametres-label" htmlFor="openrouter-key">
          Nouvelle clé OpenRouter
        </label>
        <div className="parametres-row">
          <input
            id="openrouter-key"
            type="password"
            placeholder="sk-or-..."
            value={valeur}
            onChange={(e) => setValeur(e.target.value)}
            autoComplete="off"
          />
          <button type="button" className="btn btn-primary" disabled={isSaving || !valeur.trim()} onClick={enregistrer}>
            {isSaving ? 'Enregistrement…' : 'Enregistrer'}
          </button>
        </div>

        {statutMessage && <p className="parametres-feedback parametres-feedback-ok">{statutMessage}</p>}
        {erreur && <p className="parametres-feedback parametres-feedback-error">{erreur}</p>}
      </div>
    </section>
  )
}

export default ParametresPage
