import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Alert from '../../components/Alert'
import { getCompteDemo, listerDevisValidation, type DevisValidationResumeApi } from '../api'

const LABELS_STATUT: Record<string, string> = {
  en_attente_validation: 'En attente de validation',
  valide: 'Validé — prêt à envoyer',
  envoye: 'Envoyé au client',
  accepte: '✓ Accepté par le client',
}

function EntretienValidationQueuePage() {
  const navigate = useNavigate()
  const [devisListe, setDevisListe] = useState<DevisValidationResumeApi[] | null>(null)
  const [erreur, setErreur] = useState<string | null>(null)

  useEffect(() => {
    getCompteDemo()
      .then((compte) => listerDevisValidation(compte.id))
      .then(setDevisListe)
      .catch((err) => setErreur(err instanceof Error ? err.message : 'Impossible de charger la file de validation.'))
  }, [])

  return (
    <section className="page page-wide">
      <span className="page-eyebrow">Validation artisan</span>
      <h1>Devis à valider</h1>
      <p className="page-lead">
        Chaque devis généré passe par cette file avant de pouvoir être envoyé au client final — un devis ne peut
        être envoyé qu'une fois validé.
      </p>

      {erreur && <Alert type="error">{erreur}</Alert>}

      {devisListe && devisListe.length === 0 && (
        <p className="page-lead">
          Aucun devis en attente — générez-en un depuis le parcours upload → diagnostic → devis.
        </p>
      )}

      {devisListe && devisListe.length > 0 && (
        <div className="card">
          <div className="table-scroll">
            <table className="devis-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Catégorie</th>
                  <th>Total (standard)</th>
                  <th>Statut</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {devisListe.map((devis) => (
                  <tr key={devis.id}>
                    <td>
                      {new Date(devis.cree_le).toLocaleDateString('fr-FR', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric',
                      })}
                    </td>
                    <td>{devis.categorie}</td>
                    <td className="text-numeric">{devis.total_standard.toFixed(2)} €</td>
                    <td>
                      <span className="badge">{LABELS_STATUT[devis.statut] ?? devis.statut}</span>
                    </td>
                    <td>
                      <button type="button" className="btn-link" onClick={() => navigate(`/entretien/validation/${devis.id}`)}>
                        Ouvrir →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="table-scroll-hint">← Faites glisser pour voir tout le tableau →</p>
        </div>
      )}
    </section>
  )
}

export default EntretienValidationQueuePage
