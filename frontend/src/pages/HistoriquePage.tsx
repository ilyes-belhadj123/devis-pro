import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getHistorique, getHistoriqueDetail, type HistoriqueResumeApi } from '../api'

function HistoriquePage() {
  const navigate = useNavigate()
  const [sessions, setSessions] = useState<HistoriqueResumeApi[] | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)
  const [sessionEnChargement, setSessionEnChargement] = useState<string | null>(null)

  useEffect(() => {
    getHistorique()
      .then(setSessions)
      .catch(() => setErreur("Impossible de charger l'historique — vérifiez que l'API backend est lancée."))
  }, [])

  const revoir = async (sessionId: string) => {
    setSessionEnChargement(sessionId)
    try {
      const devis = await getHistoriqueDetail(sessionId)
      navigate('/devis', { state: { devis } })
    } catch {
      setErreur('Impossible de charger ce devis pour le moment.')
    } finally {
      setSessionEnChargement(null)
    }
  }

  return (
    <section className="page page-wide">
      <span className="page-eyebrow">Historique</span>
      <h1>Devis générés précédemment</h1>
      <p className="page-lead">Retrouvez un devis déjà généré, pour le revoir ou le réexporter en PDF.</p>

      {erreur && <p style={{ color: 'var(--color-state-error)', fontSize: '0.875rem' }}>{erreur}</p>}

      {sessions && sessions.length === 0 && (
        <p className="page-lead">Aucun devis généré pour l'instant — passe par le parcours upload → diagnostic.</p>
      )}

      {sessions && sessions.length > 0 && (
        <div className="card">
          <table className="devis-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Problème</th>
                <th>Nb produits</th>
                <th>Total</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((session) => (
                <tr key={session.session_id}>
                  <td>{new Date(session.date).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })}</td>
                  <td>{session.probleme.replace(/_/g, ' ')}</td>
                  <td>{session.nombre_lignes}</td>
                  <td className="text-numeric">{session.total.toFixed(2)} €</td>
                  <td>
                    <button
                      type="button"
                      className="btn-link"
                      disabled={sessionEnChargement === session.session_id}
                      onClick={() => revoir(session.session_id)}
                    >
                      {sessionEnChargement === session.session_id ? 'Chargement…' : 'Revoir →'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default HistoriquePage
