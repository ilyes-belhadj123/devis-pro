import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { affinerDiagnostic, genererDevis, type DevisApi, type DiagnosticApi } from '../api'
import { mockDiagnostic } from '../mocks/mockData'
import './DiagnosticPage.css'

const ICONES_CATEGORIE: Record<string, string> = {
  peinture: '🎨',
  plomberie: '🔧',
  fixation: '🪛',
  electricite: '💡',
  jardin: '🌱',
}

function DiagnosticPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as { photoUrl?: string; diagnostic?: DiagnosticApi } | null
  const photoUrl = state?.photoUrl ?? null

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

  return (
    <section className="page">
      <span className="page-eyebrow">Étape 2 sur 3</span>
      <h1>Diagnostic</h1>

      <div className="scan-frame">
        {photoUrl ? (
          <img src={photoUrl} alt="Photo analysée" className="scan-photo" />
        ) : (
          <div className="scan-photo scan-photo-placeholder" />
        )}
        {isScanning && (
          <div className="scan-overlay">
            <div className="scan-line" />
            <span className="scan-caption">Analyse en cours…</span>
          </div>
        )}
      </div>

      {!isScanning && (
        <div className="card diagnostic-result">
          <div className="diagnostic-result-head">
            <span className="icon-badge">{ICONES_CATEGORIE[diagnostic.categorie] ?? '🛠️'}</span>
            <div>
              <span className="badge">● {Math.round(diagnostic.confiance * 100)}% de confiance</span>
              <h2 style={{ fontSize: '1.375rem', marginTop: 'var(--space-2)' }}>{diagnostic.probleme_label}</h2>
              <p className="page-lead">Catégorie détectée : {diagnostic.categorie}</p>
            </div>
          </div>

          {diagnostic.observations_visuelles && (
            <p className="observations-visuelles">
              <span className="observations-visuelles-label">Ce que l'IA a observé sur la photo :</span>{' '}
              {diagnostic.observations_visuelles}
            </p>
          )}

          {diagnostic.degrade && (
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-state-warning)' }}>
              Diagnostic simulé — configurez votre clé OpenRouter dans{' '}
              <a href="/parametres" style={{ color: 'inherit', textDecoration: 'underline' }}>
                Paramètres
              </a>{' '}
              pour une analyse réelle.
            </p>
          )}

          {diagnostic.questions_clarification.length > 0 && (
            <div className="clarification">
              <h3 style={{ fontSize: '1rem', fontFamily: 'var(--font-body)', fontWeight: 600 }}>
                Pour un devis avec de vraies quantités, précisez :
              </h3>
              {diagnostic.questions_clarification.map((question) => (
                <p key={question}>{question}</p>
              ))}

              <form
                className="clarification-form"
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
                <button type="submit" className="btn btn-secondary" disabled={isAffining || !reponseLibre.trim()}>
                  {isAffining ? '…' : 'Valider'}
                </button>
              </form>

              <div className="clarification-options">
                {['Intérieur', 'Extérieur'].map((option) => (
                  <button
                    key={option}
                    type="button"
                    className="btn-link"
                    disabled={isAffining}
                    onClick={() => repondreClarification(option)}
                  >
                    {isAffining && reponseChoisie === option ? '…' : option}
                  </button>
                ))}
              </div>
            </div>
          )}

          {reponseChoisie && !isAffining && diagnostic.questions_clarification.length === 0 && (
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-state-success)' }}>
              Diagnostic affiné à partir de vos précisions ✓
            </p>
          )}

          {erreur && <p style={{ color: 'var(--color-state-error)', fontSize: '0.875rem' }}>{erreur}</p>}

          {diagnostic.questions_clarification.length === 0 ? (
            <button type="button" className="btn btn-primary" disabled={isGenerating} onClick={genererLeDevis}>
              {isGenerating ? 'Génération du devis…' : 'Générer le devis →'}
            </button>
          ) : (
            <button type="button" className="btn-link" disabled={isGenerating} onClick={genererLeDevis}>
              {isGenerating ? 'Génération du devis…' : 'Ignorer et générer un devis approximatif →'}
            </button>
          )}
        </div>
      )}
    </section>
  )
}

export default DiagnosticPage
