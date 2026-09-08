import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import Alert from '../../components/Alert'
import {
  creerDevisValidation,
  genererContratRecurrent,
  genererDevisEntretien,
  getCompteDemo,
  type ContratRecurrentApi,
  type DevisEntretienApi,
  type DiagnosticEntretienApi,
} from '../api'
import { mockDevisEntretien, mockDiagnosticEntretien } from '../mocks/mockData'

const EMOJI_CATEGORIE: Record<string, string> = {
  tonte: '🌱',
  taille: '✂️',
  desherbage: '🌿',
  plantation: '🌳',
  evacuation: '🗑️',
  fertilisation: '💧',
  paillage: '🪵',
  traitement: '🧪',
  divers: '🔧',
}

const FREQUENCES = [
  { valeur: 'mensuelle', label: 'Mensuelle' },
  { valeur: 'bimensuelle', label: 'Bimensuelle' },
  { valeur: 'saisonniere', label: 'Saisonnière' },
] as const

function EntretienDevisPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as { diagnostic?: DiagnosticEntretienApi } | null
  const diagnostic = state?.diagnostic ?? mockDiagnosticEntretien

  const [devis, setDevis] = useState<DevisEntretienApi | null>(null)
  const [compteId, setCompteId] = useState('demo')
  const [formuleActive, setFormuleActive] = useState('standard')
  const [isLoading, setIsLoading] = useState(true)
  const [erreur, setErreur] = useState<string | null>(null)
  const [estDonneesReelles, setEstDonneesReelles] = useState(false)
  const [isEnvoiEnCours, setIsEnvoiEnCours] = useState(false)

  const [mode, setMode] = useState<'ponctuel' | 'recurrent'>('ponctuel')
  const [frequence, setFrequence] = useState<(typeof FREQUENCES)[number]['valeur']>('mensuelle')
  const [dureeMois, setDureeMois] = useState(12)
  const [contrat, setContrat] = useState<ContratRecurrentApi | null>(null)
  const [isCalculatingContrat, setIsCalculatingContrat] = useState(false)

  useEffect(() => {
    let annule = false
    const charger = async () => {
      setIsLoading(true)
      setErreur(null)
      try {
        const compte = await getCompteDemo()
        if (!annule) setCompteId(compte.id)
        const resultat = await genererDevisEntretien({
          compteId: compte.id,
          lieu: diagnostic.lieu,
          categorie: diagnostic.categorie,
          tachesSuggerees: diagnostic.taches_suggerees,
          estimationSurface: diagnostic.estimation_surface
            ? { valeur: diagnostic.estimation_surface.valeur, unite: diagnostic.estimation_surface.unite }
            : null,
        })
        if (annule) return
        setDevis(resultat)
        setEstDonneesReelles(true)
        setFormuleActive(resultat.formules.find((f) => f.niveau === 'standard')?.niveau ?? resultat.formules[0]?.niveau ?? 'standard')
      } catch (err) {
        if (annule) return
        console.error('Génération du devis entretien indisponible, bascule sur un exemple :', err)
        setDevis(mockDevisEntretien)
        setEstDonneesReelles(false)
        setErreur(err instanceof Error ? err.message : null)
      } finally {
        if (!annule) setIsLoading(false)
      }
    }
    charger()
    return () => {
      annule = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const formule = devis?.formules.find((f) => f.niveau === formuleActive) ?? null

  const modifierQuantite = (designation: string, delta: number) => {
    setDevis((precedent) => {
      if (!precedent) return precedent
      return {
        ...precedent,
        formules: precedent.formules.map((f) => {
          if (f.niveau !== formuleActive) return f
          const lignes = f.lignes
            .map((ligne) =>
              ligne.designation === designation
                ? { ...ligne, quantite: Math.max(0, Math.round((ligne.quantite + delta) * 100) / 100) }
                : ligne,
            )
            .map((ligne) => ({ ...ligne, sous_total: Math.round(ligne.prix_unitaire * ligne.quantite * 100) / 100 }))
          const total = Math.round(lignes.reduce((somme, ligne) => somme + ligne.sous_total, 0) * 100) / 100
          return { ...f, lignes, total }
        }),
      }
    })
  }

  const supprimerLigne = (designation: string) => {
    setDevis((precedent) => {
      if (!precedent) return precedent
      return {
        ...precedent,
        formules: precedent.formules.map((f) => {
          if (f.niveau !== formuleActive) return f
          const lignes = f.lignes.filter((ligne) => ligne.designation !== designation)
          const total = Math.round(lignes.reduce((somme, ligne) => somme + ligne.sous_total, 0) * 100) / 100
          return { ...f, lignes, total }
        }),
      }
    })
  }

  useEffect(() => {
    if (mode !== 'recurrent' || !formule || formule.lignes.length === 0) {
      setContrat(null)
      return
    }
    let annule = false
    setIsCalculatingContrat(true)
    genererContratRecurrent(formule.lignes, frequence, dureeMois)
      .then((resultat) => {
        if (!annule) setContrat(resultat)
      })
      .catch((err) => {
        if (!annule) setErreur(err instanceof Error ? err.message : 'Impossible de calculer le contrat récurrent.')
      })
      .finally(() => {
        if (!annule) setIsCalculatingContrat(false)
      })
    return () => {
      annule = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, frequence, dureeMois, formule?.total, formuleActive])

  const continuer = async () => {
    if (!devis) return
    setIsEnvoiEnCours(true)
    setErreur(null)
    try {
      const devisValidation = await creerDevisValidation(compteId, devis.categorie, devis.formules)
      navigate(`/entretien/validation/${devisValidation.id}`)
    } catch (err) {
      setErreur(err instanceof Error ? err.message : "Impossible d'envoyer ce devis en validation pour le moment.")
    } finally {
      setIsEnvoiEnCours(false)
    }
  }

  if (isLoading) {
    return (
      <section className="page page-wide">
        <p className="page-lead">Génération du devis…</p>
      </section>
    )
  }

  return (
    <section className="page page-wide">
      <span className="page-eyebrow">
        <span className="page-eyebrow-ping" />
        Devis — {diagnostic.type_espace_label}
      </span>
      <h1>Choisissez une formule</h1>

      {!estDonneesReelles && (
        <Alert type="info">
          Devis d'exemple — catalogue ou service indisponible pour le moment{erreur ? ` (${erreur})` : ''}.
        </Alert>
      )}

      {estDonneesReelles && devis && devis.ajustements_appris.length > 0 && (
        <Alert type="success">
          Quantités/prix affinés à partir de vos corrections précédentes pour :{' '}
          {devis.ajustements_appris.join(', ')}.
        </Alert>
      )}

      <div className="stat-row">
        {devis?.formules.map((f) => (
          <button
            key={f.niveau}
            type="button"
            className={`stat-tile ${f.niveau === formuleActive ? 'stat-tile-accent' : ''}`}
            style={{ textAlign: 'left', cursor: 'pointer', width: '100%' }}
            onClick={() => setFormuleActive(f.niveau)}
          >
            <span className="stat-label">{f.label}</span>
            <span className={`stat-value ${f.niveau === formuleActive ? 'stat-value-accent' : ''}`}>
              {f.total.toFixed(2)} €
            </span>
            <span className="page-lead" style={{ fontSize: '0.78125rem' }}>
              {f.description}
            </span>
          </button>
        ))}
      </div>

      {formule && (
        <div className="quote-wrap">
          <div className="quote">
            <div className="quote-inner">
              <div className="quote-head">
                <div className="qh-brand">
                  <span className="qh-dot" />
                  <span className="qh-txt">Formule {formule.label}</span>
                </div>
              </div>

              {formule.lignes.length === 0 ? (
                <p className="page-lead">Aucune ligne dans cette formule.</p>
              ) : (
                formule.lignes.map((ligne) => (
                  <div className="li" key={ligne.designation}>
                    <div className="li-icon" style={{ background: 'var(--color-accent-tech-soft)', fontSize: '1rem' }}>
                      {EMOJI_CATEGORIE[ligne.categorie] ?? '🔧'}
                    </div>
                    <div className="li-mid">
                      <p className="li-name">{ligne.designation}</p>
                      <p className="li-cat">{ligne.categorie}</p>
                      <div className="li-actions">
                        <button
                          type="button"
                          className="li-action li-action-danger"
                          onClick={() => supprimerLigne(ligne.designation)}
                        >
                          Supprimer
                        </button>
                      </div>
                    </div>
                    <div className="li-right">
                      <div className="li-qty">
                        <button
                          type="button"
                          aria-label="Diminuer la quantité"
                          onClick={() => modifierQuantite(ligne.designation, -1)}
                        >
                          −
                        </button>
                        <span className="text-mono">{ligne.quantite}</span>
                        <button
                          type="button"
                          aria-label="Augmenter la quantité"
                          onClick={() => modifierQuantite(ligne.designation, 1)}
                        >
                          +
                        </button>
                      </div>
                      <div className="li-price text-mono">{ligne.sous_total.toFixed(2)} €</div>
                    </div>
                  </div>
                ))
              )}

              <div className="quote-total">
                <span className="tt-label">Total {mode === 'ponctuel' ? 'ponctuel' : 'par intervention'}</span>
                <span className="tt-val text-gradient">{formule.total.toFixed(2)} €</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <h2>Mode de facturation</h2>
        <div className="btn-row">
          <button
            type="button"
            className={`btn ${mode === 'ponctuel' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setMode('ponctuel')}
          >
            Devis ponctuel
          </button>
          <button
            type="button"
            className={`btn ${mode === 'recurrent' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setMode('recurrent')}
          >
            Contrat récurrent
          </button>
        </div>

        {mode === 'recurrent' && (
          <div className="note-field" style={{ marginTop: 'var(--space-4)' }}>
            <label>Fréquence de passage</label>
            <div className="btn-row">
              {FREQUENCES.map((option) => (
                <button
                  key={option.valeur}
                  type="button"
                  className={`btn ${frequence === option.valeur ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setFrequence(option.valeur)}
                >
                  {option.label}
                </button>
              ))}
            </div>

            <label style={{ marginTop: 'var(--space-3)' }}>Durée d'engagement (mois)</label>
            <input
              type="number"
              min={1}
              value={dureeMois}
              onChange={(e) => setDureeMois(Math.max(1, Number(e.target.value) || 1))}
              style={{
                width: '90px',
                padding: '8px 12px',
                borderRadius: 'var(--radius-sm)',
                border: '1.5px solid var(--color-border-strong)',
              }}
            />

            {isCalculatingContrat && <p className="page-lead">Calcul du contrat…</p>}

            {contrat && !isCalculatingContrat && (
              <div className="stat-row" style={{ marginTop: 'var(--space-4)' }}>
                <div className="stat-tile">
                  <span className="stat-label">Prix par passage (contrat)</span>
                  <span className="stat-value">{contrat.prix_intervention_contrat.toFixed(2)} €</span>
                  <span className="page-lead" style={{ fontSize: '0.75rem' }}>
                    au lieu de {contrat.prix_intervention_ponctuel.toFixed(2)} € en ponctuel (-
                    {contrat.economie_pourcentage}%)
                  </span>
                </div>
                <div className="stat-tile stat-tile-accent">
                  <span className="stat-label">Prix mensuel</span>
                  <span className="stat-value stat-value-accent">{contrat.prix_mensuel.toFixed(2)} €</span>
                  <span className="page-lead" style={{ fontSize: '0.75rem' }}>
                    {contrat.interventions_an} passages/an
                  </span>
                </div>
                <div className="stat-tile">
                  <span className="stat-label">Prix annuel</span>
                  <span className="stat-value">{contrat.prix_annuel.toFixed(2)} €</span>
                  <span className="page-lead" style={{ fontSize: '0.75rem' }}>
                    engagement {contrat.duree_mois} mois
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {erreur && estDonneesReelles && <Alert type="error">{erreur}</Alert>}

      <div className="btn-row">
        <button
          type="button"
          className="btn btn-primary"
          disabled={!formule || formule.lignes.length === 0 || isEnvoiEnCours}
          onClick={continuer}
        >
          {isEnvoiEnCours ? 'Envoi en validation…' : 'Envoyer en validation artisan →'}
        </button>
      </div>
    </section>
  )
}

export default EntretienDevisPage
