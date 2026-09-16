import { useEffect, useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import Alert from '../../components/Alert'
import ZonesDetectees from '../../components/ZonesDetectees'
import { affinerDiagnosticEntretien, type DiagnosticEntretienApi } from '../api'
import { mockDiagnosticEntretien } from '../mocks/mockData'
import { useCompteur } from '../../utils/useCompteur'

function AnneauConfiance({ confiance }: { confiance: number }) {
  const pourcentageCible = Math.round(confiance * 100)
  const pourcentageAnime = Math.round(useCompteur(pourcentageCible, 900))
  return (
    <div className="ring-badge">
      <div
        className="ring"
        style={{
          background: `conic-gradient(var(--color-accent-tech) 0% ${pourcentageAnime}%, rgba(255,255,255,0.18) ${pourcentageAnime}% 100%)`,
        }}
      >
        <span>{pourcentageAnime}%</span>
      </div>
      <div className="ring-badge-text">
        Confiance
        <b>{confiance >= 0.75 ? 'Diagnostic fiable' : 'À préciser'}</b>
      </div>
    </div>
  )
}

function EntretienDiagnosticPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as { photoUrls?: string[]; diagnostic?: DiagnosticEntretienApi } | null
  const photoUrls = state?.photoUrls ?? []
  const photoUrl = photoUrls[0] ?? null

  const [diagnostic, setDiagnostic] = useState<DiagnosticEntretienApi>(state?.diagnostic ?? mockDiagnosticEntretien)
  const [isScanning, setIsScanning] = useState(true)
  const [reponsesQuestions, setReponsesQuestions] = useState<string[]>(() =>
    (state?.diagnostic ?? mockDiagnosticEntretien).questions_clarification.map(() => ''),
  )
  const [isAffining, setIsAffining] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)
  const [surfaceCorrigee, setSurfaceCorrigee] = useState(
    diagnostic.estimation_surface ? String(diagnostic.estimation_surface.valeur) : '',
  )

  useEffect(() => {
    const timer = setTimeout(() => setIsScanning(false), 1400)
    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    setReponsesQuestions(diagnostic.questions_clarification.map(() => ''))
  }, [diagnostic.questions_clarification])

  useEffect(() => {
    setSurfaceCorrigee(diagnostic.estimation_surface ? String(diagnostic.estimation_surface.valeur) : '')
  }, [diagnostic.estimation_surface])

  const repondreClarification = async (reponse: string) => {
    if (!reponse.trim()) return
    setIsAffining(true)
    setErreur(null)
    try {
      const diagnosticAffine = await affinerDiagnosticEntretien(diagnostic, reponse)
      setDiagnostic(diagnosticAffine)
    } catch (err) {
      setErreur(err instanceof Error ? err.message : "Impossible d'affiner le diagnostic pour le moment.")
    } finally {
      setIsAffining(false)
    }
  }

  const soumettreReponsesQuestions = (e: FormEvent) => {
    e.preventDefault()
    const paires = diagnostic.questions_clarification
      .map((question, i) => ({ question, reponse: (reponsesQuestions[i] ?? '').trim() }))
      .filter((paire) => paire.reponse)
    const texteReponse = paires.map((paire) => `${paire.question} → ${paire.reponse}`).join('\n')
    repondreClarification(texteReponse)
  }

  const continuerVersDevis = () => {
    const diagnosticAvecCorrection =
      surfaceCorrigee.trim() && diagnostic.estimation_surface
        ? {
            ...diagnostic,
            estimation_surface: { ...diagnostic.estimation_surface, valeur: Number(surfaceCorrigee), a_confirmer: false },
          }
        : diagnostic
    navigate('/entretien/devis', { state: { diagnostic: diagnosticAvecCorrection } })
  }


  return (
    <section className="page page-wide">
      <span className="page-eyebrow">
        <span className="page-eyebrow-ping" />
        Diagnostic — entretien intérieur & extérieur
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
              <>
                <ZonesDetectees zones={diagnostic.zones_detectees ?? []} />
                <AnneauConfiance confiance={diagnostic.confiance} />
              </>
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
            <span className="diag-tag">
              ✓ Catégorie détectée : {diagnostic.categorie} · {diagnostic.lieu === 'interieur' ? 'Intérieur' : 'Extérieur'}
            </span>
            <h2 className="diag-h">{diagnostic.type_espace_label}</h2>

            {diagnostic.observations_visuelles && <p className="diag-p">{diagnostic.observations_visuelles}</p>}

            <div className="note-field">
              <label>Ce n'est pas le bon lieu ?</label>
              <div className="chip-row">
                {(['interieur', 'exterieur'] as const).map((option) => (
                  <button
                    key={option}
                    type="button"
                    className={`chip ${diagnostic.lieu === option ? 'active' : ''}`}
                    disabled={isAffining}
                    onClick={() => repondreClarification(option === 'interieur' ? 'Intérieur' : 'Extérieur')}
                  >
                    <span className="chip-dot" />
                    {option === 'interieur' ? 'Intérieur' : 'Extérieur'}
                  </button>
                ))}
              </div>
            </div>

            {diagnostic.degrade && (
              <Alert type="warning">
                Diagnostic simulé — configurez votre clé OpenRouter dans{' '}
                <a href="/parametres" className="alert-link">
                  Paramètres
                </a>{' '}
                pour une analyse réelle.
              </Alert>
            )}

            {diagnostic.taches_suggerees.length > 0 && (
              <ul>
                {diagnostic.taches_suggerees.map((tache) => (
                  <li key={tache}>{tache}</li>
                ))}
              </ul>
            )}

            {diagnostic.estimation_surface && (
              <div className="note-field">
                <label>
                  Surface/longueur estimée{' '}
                  {diagnostic.estimation_surface.a_confirmer && <span className="badge">À confirmer</span>}
                </label>
                <div className="btn-row" style={{ alignItems: 'center' }}>
                  <input
                    type="number"
                    min={0}
                    step={0.5}
                    value={surfaceCorrigee}
                    onChange={(e) => setSurfaceCorrigee(e.target.value)}
                    style={{
                      width: '100px',
                      padding: '8px 12px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1.5px solid var(--color-border-strong)',
                    }}
                  />
                  <span className="text-numeric">{diagnostic.estimation_surface.unite}</span>
                </div>
              </div>
            )}

            {diagnostic.questions_clarification.length > 0 && (
              <div className="clarify">
                <form className="clarify-form" onSubmit={soumettreReponsesQuestions}>
                  <div className="clarify-questions">
                    {diagnostic.questions_clarification.map((question, i) => {
                      const suggestions = diagnostic.suggestions_clarification?.[i] ?? []
                      return (
                        <div className="clarify-question-row" key={question}>
                          <p className="clarify-q">{question}</p>
                          <input
                            type="text"
                            placeholder="Votre réponse (ex: environ 15 m)…"
                            value={reponsesQuestions[i] ?? ''}
                            onChange={(e) =>
                              setReponsesQuestions((actuelles) =>
                                actuelles.map((r, ri) => (ri === i ? e.target.value : r)),
                              )
                            }
                            disabled={isAffining}
                          />
                          {suggestions.length > 0 && (
                            <div className="suggestion-row">
                              {suggestions.map((suggestion) => (
                                <button
                                  key={suggestion}
                                  type="button"
                                  className={`suggestion-chip ${reponsesQuestions[i] === suggestion ? 'active' : ''}`}
                                  disabled={isAffining}
                                  onClick={() =>
                                    setReponsesQuestions((actuelles) =>
                                      actuelles.map((r, ri) => (ri === i ? suggestion : r)),
                                    )
                                  }
                                >
                                  {suggestion}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={isAffining || reponsesQuestions.every((r) => !r.trim())}
                  >
                    {isAffining ? '…' : 'Valider'}
                  </button>
                </form>
              </div>
            )}

            {erreur && <Alert type="error">{erreur}</Alert>}
          </div>
        )}
      </div>

      {!isScanning && (
        <div className="diag-actions">
          {diagnostic.questions_clarification.length === 0 ? (
            <button type="button" className="btn btn-primary" onClick={continuerVersDevis}>
              Voir le devis
            </button>
          ) : (
            <button type="button" className="btn btn-secondary" onClick={continuerVersDevis}>
              Ignorer et voir un devis approximatif
            </button>
          )}
        </div>
      )}
    </section>
  )
}

export default EntretienDiagnosticPage
