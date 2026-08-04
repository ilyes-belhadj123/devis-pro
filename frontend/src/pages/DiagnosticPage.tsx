import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { mockDiagnostic } from '../mocks/mockData'
import './DiagnosticPage.css'

function DiagnosticPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const photoUrl = (location.state as { photoUrl?: string } | null)?.photoUrl ?? null

  const [isScanning, setIsScanning] = useState(true)
  const [reponse, setReponse] = useState<string | null>(null)

  useEffect(() => {
    const timer = setTimeout(() => setIsScanning(false), 1800)
    return () => clearTimeout(timer)
  }, [])

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
            <span className="icon-badge">🎨</span>
            <div>
              <span className="badge">● {Math.round(mockDiagnostic.confiance * 100)}% de confiance</span>
              <h2 style={{ fontSize: '1.375rem', marginTop: 'var(--space-2)' }}>{mockDiagnostic.probleme}</h2>
              <p className="page-lead">Catégorie détectée : {mockDiagnostic.categorie}</p>
            </div>
          </div>

          {mockDiagnostic.questionsClarification.length > 0 && (
            <div className="clarification">
              <h3 style={{ fontSize: '1rem', fontFamily: 'var(--font-body)', fontWeight: 600 }}>
                Une dernière précision
              </h3>
              {mockDiagnostic.questionsClarification.map((question) => (
                <div key={question} className="clarification-question">
                  <p>{question}</p>
                  <div className="clarification-options">
                    {['Intérieur', 'Extérieur'].map((option) => (
                      <button
                        key={option}
                        type="button"
                        className={`btn btn-secondary ${reponse === option ? 'clarification-selected' : ''}`}
                        onClick={() => setReponse(option)}
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          <button type="button" className="btn btn-primary" onClick={() => navigate('/devis')}>
            Générer le devis →
          </button>
        </div>
      )}
    </section>
  )
}

export default DiagnosticPage
