import { useNavigate } from 'react-router-dom'
import { mockDiagnostic } from '../mocks/mockData'

function DiagnosticPage() {
  const navigate = useNavigate()

  return (
    <section className="page page-diagnostic">
      <h1>Diagnostic</h1>
      <p>
        Problème détecté : <strong>{mockDiagnostic.probleme}</strong> ({mockDiagnostic.categorie})
      </p>
      <p>Confiance : {Math.round(mockDiagnostic.confiance * 100)}%</p>

      {mockDiagnostic.questionsClarification.length > 0 && (
        <div className="clarification">
          <h2>Une précision ?</h2>
          {mockDiagnostic.questionsClarification.map((question) => (
            <p key={question}>{question}</p>
          ))}
        </div>
      )}

      <button type="button" onClick={() => navigate('/devis')}>
        Générer le devis
      </button>
    </section>
  )
}

export default DiagnosticPage
