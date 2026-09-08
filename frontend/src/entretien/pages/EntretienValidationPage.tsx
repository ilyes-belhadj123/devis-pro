import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Alert from '../../components/Alert'
import {
  envoyerDevisValidation,
  exporterDevisValidationFacturation,
  exporterDevisValidationPdf,
  getDevisValidation,
  modifierDevisValidation,
  validerDevisValidation,
  type DevisValidationApi,
  type FormuleDevisApi,
} from '../api'

function telechargerBlob(blob: Blob, nomFichier: string) {
  const url = URL.createObjectURL(blob)
  const lien = document.createElement('a')
  lien.href = url
  lien.download = nomFichier
  document.body.appendChild(lien)
  lien.click()
  lien.remove()
  URL.revokeObjectURL(url)
}

function EntretienValidationPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [devis, setDevis] = useState<DevisValidationApi | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSauvegardeEnCours, setIsSauvegardeEnCours] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)
  const [niveauExport, setNiveauExport] = useState('standard')
  const [isExportEnCours, setIsExportEnCours] = useState(false)

  useEffect(() => {
    if (!id) return
    getDevisValidation(id)
      .then(setDevis)
      .catch((err) => setErreur(err instanceof Error ? err.message : 'Impossible de charger ce devis.'))
      .finally(() => setIsLoading(false))
  }, [id])

  const modifierLigne = (
    niveau: string,
    designationOriginale: string,
    champ: 'designation' | 'prix_unitaire' | 'quantite',
    valeur: string,
  ) => {
    setDevis((precedent) => {
      if (!precedent) return precedent
      const formules: FormuleDevisApi[] = precedent.formules.map((formule) => {
        if (formule.niveau !== niveau) return formule
        const lignes = formule.lignes.map((ligne) => {
          if (ligne.designation !== designationOriginale) return ligne
          const miseAJour =
            champ === 'designation'
              ? { ...ligne, designation: valeur }
              : champ === 'prix_unitaire'
                ? { ...ligne, prix_unitaire: Math.max(0, Number(valeur) || 0) }
                : { ...ligne, quantite: Math.max(0, Number(valeur) || 0) }
          return { ...miseAJour, sous_total: Math.round(miseAJour.prix_unitaire * miseAJour.quantite * 100) / 100 }
        })
        const total = Math.round(lignes.reduce((somme, ligne) => somme + ligne.sous_total, 0) * 100) / 100
        return { ...formule, lignes, total }
      })
      return { ...precedent, formules }
    })
  }

  const supprimerLigne = (niveau: string, designation: string) => {
    setDevis((precedent) => {
      if (!precedent) return precedent
      const formules = precedent.formules.map((formule) => {
        if (formule.niveau !== niveau) return formule
        const lignes = formule.lignes.filter((ligne) => ligne.designation !== designation)
        const total = Math.round(lignes.reduce((somme, ligne) => somme + ligne.sous_total, 0) * 100) / 100
        return { ...formule, lignes, total }
      })
      return { ...precedent, formules }
    })
  }

  const validerLeDevis = async () => {
    if (!devis) return
    setIsSauvegardeEnCours(true)
    setErreur(null)
    try {
      await modifierDevisValidation(devis.id, devis.formules)
      const devisValide = await validerDevisValidation(devis.id)
      setDevis(devisValide)
    } catch (err) {
      setErreur(err instanceof Error ? err.message : 'Impossible de valider ce devis pour le moment.')
    } finally {
      setIsSauvegardeEnCours(false)
    }
  }

  const envoyerAuClient = async () => {
    if (!devis) return
    setIsSauvegardeEnCours(true)
    setErreur(null)
    try {
      const devisEnvoye = await envoyerDevisValidation(devis.id)
      setDevis(devisEnvoye)
    } catch (err) {
      setErreur(err instanceof Error ? err.message : "Impossible d'envoyer ce devis pour le moment.")
    } finally {
      setIsSauvegardeEnCours(false)
    }
  }

  const exporterPdf = async () => {
    if (!devis) return
    setIsExportEnCours(true)
    setErreur(null)
    try {
      const blob = await exporterDevisValidationPdf(devis.id, niveauExport)
      telechargerBlob(blob, `devis-entretien-${devis.id}.pdf`)
    } catch (err) {
      setErreur(err instanceof Error ? err.message : "Impossible d'exporter ce devis en PDF pour le moment.")
    } finally {
      setIsExportEnCours(false)
    }
  }

  const exporterFacturation = async (format: 'csv' | 'json') => {
    if (!devis) return
    setIsExportEnCours(true)
    setErreur(null)
    try {
      const blob = await exporterDevisValidationFacturation(devis.id, niveauExport, format)
      telechargerBlob(blob, `devis-entretien-${devis.id}.${format}`)
    } catch (err) {
      setErreur(err instanceof Error ? err.message : "Impossible d'exporter ce devis pour le moment.")
    } finally {
      setIsExportEnCours(false)
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
      <section className="page page-wide">
        {erreur && <Alert type="error">{erreur}</Alert>}
        <button type="button" className="btn btn-secondary" onClick={() => navigate('/entretien/validation')}>
          ← Retour à la file de validation
        </button>
      </section>
    )
  }

  const modifiable = devis.statut === 'en_attente_validation'
  const lienClient = `${window.location.origin}/entretien/devis-client/${devis.id}`

  return (
    <section className="page page-wide">
      <span className="page-eyebrow">Validation artisan</span>
      <h1>Devis — {devis.categorie}</h1>

      {erreur && <Alert type="error">{erreur}</Alert>}

      {devis.statut === 'accepte' && (
        <Alert type="success">
          ✓ Accepté par le client — formule « {devis.formule_choisie} » le{' '}
          {devis.accepte_le && new Date(devis.accepte_le).toLocaleString('fr-FR')}
        </Alert>
      )}

      {devis.statut === 'envoye' && (
        <Alert type="info">
          Envoyé au client, en attente d'acceptation. Lien unique : <code>{lienClient}</code>
        </Alert>
      )}

      {devis.formules.map((formule) => (
        <div className="card" key={formule.niveau}>
          <h2>
            {formule.label} — {formule.total.toFixed(2)} €
          </h2>
          <p className="page-lead" style={{ fontSize: '0.8125rem' }}>
            {formule.description}
          </p>

          {formule.lignes.length === 0 ? (
            <p className="page-lead">Aucune ligne.</p>
          ) : (
            <>
            <div className="table-scroll">
              <table className="devis-table">
                <thead>
                  <tr>
                    <th style={{ whiteSpace: 'nowrap' }}>Désignation</th>
                    <th style={{ whiteSpace: 'nowrap' }}>Prix unitaire</th>
                    <th style={{ whiteSpace: 'nowrap' }}>Quantité</th>
                    <th style={{ whiteSpace: 'nowrap' }}>Sous-total</th>
                    {modifiable && <th></th>}
                  </tr>
                </thead>
                <tbody>
                  {formule.lignes.map((ligne) => (
                    <tr key={ligne.designation}>
                      <td>
                        {modifiable ? (
                          <input
                            type="text"
                            value={ligne.designation}
                            onChange={(e) => modifierLigne(formule.niveau, ligne.designation, 'designation', e.target.value)}
                            style={{ width: '100%', minWidth: '160px', padding: '6px 8px', border: '1.5px solid var(--color-border-strong)', borderRadius: 'var(--radius-sm)' }}
                          />
                        ) : (
                          ligne.designation
                        )}
                      </td>
                      <td>
                        {modifiable ? (
                          <input
                            type="number"
                            min={0}
                            step={0.01}
                            value={ligne.prix_unitaire}
                            onChange={(e) => modifierLigne(formule.niveau, ligne.designation, 'prix_unitaire', e.target.value)}
                            style={{ width: '90px', padding: '6px 8px', border: '1.5px solid var(--color-border-strong)', borderRadius: 'var(--radius-sm)' }}
                          />
                        ) : (
                          `${ligne.prix_unitaire.toFixed(2)} €`
                        )}
                      </td>
                      <td>
                        {modifiable ? (
                          <input
                            type="number"
                            min={0}
                            step={0.5}
                            value={ligne.quantite}
                            onChange={(e) => modifierLigne(formule.niveau, ligne.designation, 'quantite', e.target.value)}
                            style={{ width: '80px', padding: '6px 8px', border: '1.5px solid var(--color-border-strong)', borderRadius: 'var(--radius-sm)' }}
                          />
                        ) : (
                          ligne.quantite
                        )}
                      </td>
                      <td className="text-numeric">{ligne.sous_total.toFixed(2)} €</td>
                      {modifiable && (
                        <td>
                          <button type="button" className="btn-link" onClick={() => supprimerLigne(formule.niveau, ligne.designation)}>
                            Supprimer
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="table-scroll-hint">← Faites glisser pour voir tout le tableau →</p>
            </>
          )}
        </div>
      ))}

      {devis.statut !== 'en_attente_validation' && (
        <div className="card">
          <h2>Exporter ce devis</h2>
          <div className="note-field">
            <label>Formule à exporter</label>
            <div className="btn-row">
              {devis.formules.map((formule) => (
                <button
                  key={formule.niveau}
                  type="button"
                  className={`btn ${niveauExport === formule.niveau ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setNiveauExport(formule.niveau)}
                >
                  {formule.label}
                </button>
              ))}
            </div>
          </div>
          <div className="btn-row" style={{ marginTop: 'var(--space-4)' }}>
            <button type="button" className="btn btn-secondary" disabled={isExportEnCours} onClick={exporterPdf}>
              Exporter en PDF
            </button>
            <button type="button" className="btn btn-secondary" disabled={isExportEnCours} onClick={() => exporterFacturation('csv')}>
              Exporter vers mon logiciel de facturation (CSV)
            </button>
            <button type="button" className="btn btn-secondary" disabled={isExportEnCours} onClick={() => exporterFacturation('json')}>
              Exporter (JSON)
            </button>
          </div>
        </div>
      )}

      <div className="btn-row">
        {devis.statut === 'en_attente_validation' && (
          <button type="button" className="btn btn-primary" disabled={isSauvegardeEnCours} onClick={validerLeDevis}>
            {isSauvegardeEnCours ? 'Validation…' : 'Valider ce devis'}
          </button>
        )}
        {devis.statut === 'valide' && (
          <button type="button" className="btn btn-primary" disabled={isSauvegardeEnCours} onClick={envoyerAuClient}>
            {isSauvegardeEnCours ? 'Envoi…' : 'Envoyer au client'}
          </button>
        )}
        <button type="button" className="btn btn-secondary" onClick={() => navigate('/entretien/validation')}>
          ← Retour à la file de validation
        </button>
      </div>
    </section>
  )
}

export default EntretienValidationPage
