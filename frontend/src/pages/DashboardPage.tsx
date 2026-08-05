import { useEffect, useState } from 'react'
import { getStatistiques, type StatistiquesApi } from '../api'
import Alert from '../components/Alert'
import './DashboardPage.css'

function DashboardPage() {
  const [stats, setStats] = useState<StatistiquesApi | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)

  useEffect(() => {
    getStatistiques()
      .then(setStats)
      .catch((err) => setErreur(err instanceof Error ? err.message : 'Impossible de charger les statistiques.'))
  }, [])

  return (
    <section className="page page-wide">
      <span className="page-eyebrow">Interne — argumentaire commercial</span>
      <h1>Impact panier moyen</h1>
      <p className="page-lead">
        Delta entre le produit principal que le client serait venu chercher seul, et le devis complet généré par
        SnapDevis, agrégé sur l'ensemble des devis générés en démo.
      </p>

      {erreur && <Alert type="error">{erreur}</Alert>}

      {stats && stats.nombre_sessions === 0 && (
        <p className="page-lead">
          Aucun devis généré pour l'instant — passe par le parcours upload → diagnostic → devis pour commencer à
          alimenter ces statistiques.
        </p>
      )}

      {stats && stats.nombre_sessions > 0 && (
        <>
          <div className="stat-row">
            <div className="stat-tile stat-tile-muted">
              <span className="stat-label">Panier moyen — produit principal seul</span>
              <span className="stat-value stat-value-muted">{stats.panier_moyen_produit_principal.toFixed(2)} €</span>
            </div>
            <div className="stat-tile stat-tile-accent">
              <span className="stat-label">Panier moyen — devis complet SnapDevis</span>
              <span className="stat-value stat-value-accent">{stats.panier_moyen_devis_complet.toFixed(2)} €</span>
            </div>
            <div className="stat-tile stat-tile-success">
              <span className="stat-label">Delta généré par SnapDevis</span>
              <span className="stat-value stat-value-success">
                +{stats.delta_moyen.toFixed(2)} € <span className="stat-delta-pct">(+{stats.delta_pourcentage.toFixed(0)}%)</span>
              </span>
            </div>
          </div>

          <p className="page-lead" style={{ fontSize: '0.8125rem' }}>
            Basé sur {stats.nombre_sessions} devis générés.
          </p>

          <div className="card">
            <h2 className="dashboard-section-title">Répartition par type de problème</h2>
            <div className="table-scroll">
              <table className="devis-table">
                <thead>
                  <tr>
                    <th>Problème</th>
                    <th>Nombre de devis</th>
                    <th>Panier moyen</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.repartition_par_probleme.map((ligne) => (
                    <tr key={ligne.probleme}>
                      <td>{ligne.probleme.replace(/_/g, ' ')}</td>
                      <td>{ligne.nombre}</td>
                      <td className="text-numeric">{ligne.panier_moyen.toFixed(2)} €</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="table-scroll-hint">← Faites glisser pour voir tout le tableau →</p>
          </div>
        </>
      )}
    </section>
  )
}

export default DashboardPage
