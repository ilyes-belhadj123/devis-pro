import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { affinerDiagnostic, genererDevis, type DevisApi, type DiagnosticApi } from '../api'
import Alert from '../components/Alert'
import ZonesDetectees from '../components/ZonesDetectees'
import { mockDiagnostic } from '../mocks/mockData'
import { compresserImage } from '../utils/compresserImage'
import './DiagnosticPage.css'

type PhotoClarification = { file: File; url: string }

function DiagnosticPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as { photoUrls?: string[]; diagnostic?: DiagnosticApi } | null
  const photoUrls = state?.photoUrls ?? []
  const photoUrl = photoUrls[0] ?? null

  const [diagnostic, setDiagnostic] = useState<DiagnosticApi>(state?.diagnostic ?? mockDiagnostic)
  const [isScanning, setIsScanning] = useState(true)
  const [reponseChoisie, setReponseChoisie] = useState<string | null>(null)
  const [reponsesQuestions, setReponsesQuestions] = useState<string[]>(() =>
    (state?.diagnostic ?? mockDiagnostic).questions_clarification.map(() => ''),
  )
  const [isAffining, setIsAffining] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)
  const [clarificationPhotos, setClarificationPhotos] = useState<PhotoClarification[]>([])
  const clarificationInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const timer = setTimeout(() => setIsScanning(false), 1800)
    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    setReponsesQuestions(diagnostic.questions_clarification.map(() => ''))
  }, [diagnostic.questions_clarification])

  const ajouterPhotoClarification = async (fichiers: FileList | null) => {
    if (!fichiers || fichiers.length === 0) return
    const nouvelles = await Promise.all(
      Array.from(fichiers).map(async (fichier) => {
        const fichierPret = await compresserImage(fichier)
        return { file: fichierPret, url: URL.createObjectURL(fichierPret) }
      }),
    )
    setClarificationPhotos((actuelles) => [...actuelles, ...nouvelles])
  }

  const retirerPhotoClarification = (index: number) => {
    setClarificationPhotos((actuelles) => actuelles.filter((_, i) => i !== index))
  }

  const repondreClarification = async (reponse: string) => {
    if (!reponse.trim() && clarificationPhotos.length === 0) return
    const texteReponse = reponse.trim() || 'Voici une photo supplémentaire.'
    setReponseChoisie(reponse || 'Photo ajoutée')
    setIsAffining(true)
    setErreur(null)
    try {
      const diagnosticAffine = await affinerDiagnostic(
        diagnostic,
        texteReponse,
        clarificationPhotos.map((photo) => photo.file),
      )
      setDiagnostic(diagnosticAffine)
      setClarificationPhotos([])
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
              <>
                <ZonesDetectees zones={diagnostic.zones_detectees ?? []} />
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
                <form className="clarify-form" onSubmit={soumettreReponsesQuestions}>
                  <div className="clarify-questions">
                    {diagnostic.questions_clarification.map((question, i) => {
                      const suggestions = diagnostic.suggestions_clarification?.[i] ?? []
                      return (
                        <div className="clarify-question-row" key={question}>
                          <p className="clarify-q">{question}</p>
                          <input
                            type="text"
                            placeholder="Votre réponse (ex: environ 8 m²)…"
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
                    disabled={
                      isAffining ||
                      (reponsesQuestions.every((r) => !r.trim()) && clarificationPhotos.length === 0)
                    }
                  >
                    {isAffining ? '…' : 'Valider'}
                  </button>
                </form>

                <div className="clarify-photo-row">
                  {clarificationPhotos.map((photo, index) => (
                    <div className="clarify-photo-thumb" key={photo.url}>
                      <img src={photo.url} alt={`Photo ajoutée ${index + 1}`} />
                      <button
                        type="button"
                        aria-label="Retirer cette photo"
                        onClick={() => retirerPhotoClarification(index)}
                      >
                        ×
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    className="clarify-photo-add"
                    disabled={isAffining}
                    onClick={() => clarificationInputRef.current?.click()}
                  >
                    📷 Ajouter une photo
                  </button>
                  <input
                    ref={clarificationInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/heic"
                    multiple
                    hidden
                    onChange={(e) => {
                      ajouterPhotoClarification(e.target.files)
                      e.target.value = ''
                    }}
                  />
                </div>

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
