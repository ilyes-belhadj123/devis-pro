import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import Alert from '../../components/Alert'
import { accepterDevisPublic, getDevisPublic, type DevisValidationApi } from '../api'
import Confetti from '../components/Confetti'
import { useCompteur } from '../../utils/useCompteur'

function MontantAnime({ valeur }: { valeur: number }) {
  return <>{useCompteur(valeur).toFixed(2)} €</>
}

function EntretienDevisClientPage() {
  const { id } = useParams<{ id: string }>()

  const [devis, setDevis] = useState<DevisValidationApi | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [erreur, setErreur] = useState<string | null>(null)
  const [niveauChoisi, setNiveauChoisi] = useState('standard')
  const [accepteCoche, setAccepteCoche] = useState(false)
  const [isAcceptationEnCours, setIsAcceptationEnCours] = useState(false)
  const [montrerConfetti, setMontrerConfetti] = useState(false)

  useEffect(() => {
    if (!id) return
    getDevisPublic(id)
      .then((resultat) => {
        setDevis(resultat)
        setNiveauChoisi(resultat.formule_choisie ?? resultat.formules.find((f) => f.niveau === 'standard')?.niveau ?? resultat.formules[0]?.niveau ?? 'standard')
      })
      .catch((err) => setErreur(err instanceof Error ? err.message : "Ce devis n'est pas disponible."))
      .finally(() => setIsLoading(false))
  }, [id])

  const accepter = async () => {
    if (!devis || !accepteCoche) return
    setIsAcceptationEnCours(true)
    setErreur(null)
    try {
      const resultat = await accepterDevisPublic(devis.id, niveauChoisi)
      setDevis(resultat)
      setMontrerConfetti(true)
      setTimeout(() => setMontrerConfetti(false), 3500)
    } catch (err) {
      setErreur(err instanceof Error ? err.message : "Impossible d'accepter ce devis pour le moment.")
    } finally {
      setIsAcceptationEnCours(false)
    }
  }

  if (isLoading) {
    return (
      <section className="page page-wide">
        <p className="page-lead">Chargement du devis…</p>
      </section>
    )
  }

  if (!devis) {
    return (
      <section className="page">
        <span className="page-eyebrow">Devis SnapDevis Entretien</span>
        <h1>Devis introuvable</h1>
        <Alert type="error">{erreur ?? "Ce lien n'est plus valide ou ce devis n'a pas encore été envoyé."}</Alert>
      </section>
    )
  }

  if (devis.statut === 'accepte') {
    const formuleAcceptee = devis.formules.find((f) => f.niveau === devis.formule_choisie)
    return (
      <section className="page page-wide">
        {montrerConfetti && <Confetti />}
        <span className="page-eyebrow">Devis SnapDevis Entretien</span>
        <h1>Merci, votre devis est confirmé !</h1>
        <Alert type="success">
          Vous avez accepté la formule « {formuleAcceptee?.label ?? devis.formule_choisie} » —{' '}
          {formuleAcceptee ? <MontantAnime valeur={formuleAcceptee.total} /> : `${devis.formule_choisie}`}. L'artisan
          a été notifié et vous recontactera pour planifier l'intervention.
        </Alert>
      </section>
    )
  }

  return (
    <section className="page page-wide">
      <span className="page-eyebrow">Devis SnapDevis Entretien — {devis.categorie}</span>
      <h1>Choisissez votre formule</h1>
      <p className="page-lead">Sélectionnez la formule qui vous convient, puis acceptez le devis en ligne.</p>

      {erreur && <Alert type="error">{erreur}</Alert>}

      <div className="stat-row">
        {devis.formules.map((formule) => (
          <button
            key={formule.niveau}
            type="button"
            className={`stat-tile ${formule.niveau === niveauChoisi ? 'stat-tile-accent' : ''}`}
            style={{ textAlign: 'left', cursor: 'pointer', width: '100%' }}
            onClick={() => setNiveauChoisi(formule.niveau)}
          >
            <span className="stat-label">{formule.label}</span>
            <span className={`stat-value ${formule.niveau === niveauChoisi ? 'stat-value-accent' : ''}`}>
              <MontantAnime valeur={formule.total} />
            </span>
            <span className="page-lead" style={{ fontSize: '0.78125rem' }}>
              {formule.description}
            </span>
          </button>
        ))}
      </div>

      {devis.formules
        .filter((formule) => formule.niveau === niveauChoisi)
        .map((formule) => (
          <div className="card" key={formule.niveau}>
            <h2>Détail — {formule.label}</h2>
            <ul>
              {formule.lignes.map((ligne) => (
                <li key={ligne.designation}>
                  {ligne.designation} — {ligne.quantite} {ligne.unite} × {ligne.prix_unitaire.toFixed(2)} € ={' '}
                  {ligne.sous_total.toFixed(2)} €
                </li>
              ))}
            </ul>
          </div>
        ))}

      <label className="reference-check">
        <input type="checkbox" checked={accepteCoche} onChange={(e) => setAccepteCoche(e.target.checked)} />
        J'accepte ce devis pour la formule sélectionnée
      </label>

      <div className="btn-row">
        <button type="button" className="btn btn-primary" disabled={!accepteCoche || isAcceptationEnCours} onClick={accepter}>
          {isAcceptationEnCours ? 'Confirmation…' : 'Accepter le devis'}
        </button>
      </div>
    </section>
  )
}

export default EntretienDevisClientPage
