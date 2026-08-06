import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { affinerDiagnostic, genererDevis, type DevisApi, type DiagnosticApi } from '../api'
import Alert from '../components/Alert'
import { mockDiagnostic } from '../mocks/mockData'
import './DiagnosticPage.css'

function DiagnosticPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as { photoUrls?: string[]; diagnostic?: DiagnosticApi } | null
  const photoUrls = state?.photoUrls ?? []
  const photoUrl = photoUrls[0] ?? null

  const [diagnostic, setDiagnostic] = useState<DiagnosticApi>(state?.diagnostic ?? mockDiagnostic)
  const [isScanning, setIsScanning] = useState(true)
  const [reponseChoisie, setReponseChoisie] = useState<string | null>(null)
  const [reponseLibre, setReponseLibre] = useState('')
  const [isAffining, setIsAffining] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)

  useEffect(() => {
    const timer = setTimeout(() => setIsScanning(false), 1800)
    return () => clearTimeout(timer)
  }, [])

  const repondreClarification = async (reponse: string) => {
    if (!reponse.trim()) return
    setReponseChoisie(reponse)
    setIsAffining(true)
    setErreur(null)
    try {
      const diagnosticAffine = await affinerDiagnostic(diagnostic, reponse)
      setDiagnostic(diagnosticAffine)
      setReponseLibre('')
    } catch (err) {
      setErreur(err instanceof Error ? err.message : "Impossible d'affiner le diagnostic pour le moment.")
    } finally {
      setIsAffining(false)
    }
  }

  const genererLeDevis = async () => {
    setIsGenerating(true)
    setErreur(null)
    try {
      const devis: DevisApi = await genererDevis(diagnostic.probleme_cle, diagnostic.session_id)
      navigate('/devis', { state: { devis } })
    } catch (err) {
      setErreur(
        err instanceof Error
          ? err.message
          : 'Le service de diagnostic est momentanément indisponible. Réessayez dans un instant.',
      )
    } finally {
      setIsGenerating(false)
    }
  }

  const pourcentageConfiance = Math.round(diagnostic.confiance * 100)

  return (
    <section className="page page-wide">
      <span className="page-eyebrow">
        <span className="page-eyebrow-ping" />
        Étape 2 sur 3
      </span>

      <div className="diag-grid">
        <div className="photo-column">
          <div className="photo-frame">
            {photoUrl ? (
              <img src={photoUrl} alt="Photo analysée" className="scan-photo" />
            ) : (
              <div className="scan-photo scan-photo-placeholder">
                <svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5">
                  <path d="M4 8h3l1.5-2h7L17 8h3a1 1 0 011 1v9a1 1 0 01-1 1H4a1 1 0 01-1-1V9a1 1 0 011-1z" />
                  <circle cx="12" cy="13" r="3.4" />
                </svg>
              </div>
            )}

            {isScanning ? (
              <div className="scan-line" />
            ) : (
              <div className="ring-badge">
                <div
                  className="ring"
                  style={{
                    background: `conic-gradient(var(--color-accent-amber) 0% ${pourcentageConfiance}%, rgba(255,255,255,0.18) ${pourcentageConfiance}% 100%)`,
                  }}
                >
                  <span>{pourcentageConfiance}%</span>
                </div>
                <div className="ring-badge-text">
                  Confiance
                  <b>{diagnostic.confiance >= 0.75 ? 'Diagnostic fiable' : 'À préciser'}</b>
                </div>
              </div>
            )}
          </div>

          {photoUrls.length > 1 && (
            <div className="photo-thumbs-strip">
              {photoUrls.map((url, index) => (
                <img
                  key={url}
                  src={url}
                  alt={`Photo ${index + 1}`}
                  className={`photo-thumb-mini ${index === 0 ? 'active' : ''}`}
                />
              ))}
            </div>
          )}
        </div>

        {!isScanning && (
          <div className="diag-panel">
            <span className="diag-tag">✓ Catégorie détectée : {diagnostic.categorie}</span>
            <h2 className="diag-h">{diagnostic.probleme_label}</h2>

            {diagnostic.observations_visuelles && <p className="diag-p">{diagnostic.observations_visuelles}</p>}

            {diagnostic.degrade && (
              <Alert type="warning">
                Diagnostic simulé — configurez votre clé OpenRouter dans{' '}
                <a href="/parametres" className="alert-link">
                  Paramètres
                </a>{' '}
                pour une analyse réelle.
              </Alert>
            )}

            {diagnostic.questions_clarification.length > 0 && (
              <div className="clarify">
                {diagnostic.questions_clarification.map((question) => (
                  <p key={question} className="clarify-q">
                    {question}
                  </p>
                ))}

                <form
                  className="clarify-form"
                  onSubmit={(e) => {
                    e.preventDefault()
                    repondreClarification(reponseLibre)
                  }}
                >
                  <input
                    type="text"
                    placeholder="Votre réponse (ex: environ 8 m²)…"
                    value={reponseLibre}
                    onChange={(e) => setReponseLibre(e.target.value)}
                    disabled={isAffining}
                  />
                  <button type="submit" className="btn btn-primary" disabled={isAffining || !reponseLibre.trim()}>
                    {isAffining ? '…' : 'Valider'}
                  </button>
                </form>

                <div className="chip-row">
                  {['Intérieur', 'Extérieur'].map((option) => (
                    <button
                      key={option}
                      type="button"
                      className={`chip ${reponseChoisie === option ? 'active' : ''}`}
                      disabled={isAffining}
                      onClick={() => repondreClarification(option)}
                    >
                      <span className="chip-dot" />
                      {isAffining && reponseChoisie === option ? '…' : option}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {reponseChoisie && !isAffining && diagnostic.questions_clarification.length === 0 && (
              <Alert type="success">Diagnostic affiné à partir de vos précisions ✓</Alert>
            )}

            {erreur && <Alert type="error">{erreur}</Alert>}
          </div>
        )}
      </div>

      {!isScanning && (
        <div className="diag-actions">
          {diagnostic.questions_clarification.length === 0 ? (
            <button type="button" className="btn btn-primary" disabled={isGenerating} onClick={genererLeDevis}>
              {isGenerating ? 'Génération du devis…' : 'Générer le devis'}
            </button>
          ) : (
            <button type="button" className="btn btn-secondary" disabled={isGenerating} onClick={genererLeDevis}>
              {isGenerating ? 'Génération du devis…' : 'Ignorer et générer un devis approximatif'}
            </button>
          )}
        </div>
      )}
    </section>
  )
}

export default DiagnosticPage
