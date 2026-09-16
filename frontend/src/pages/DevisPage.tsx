import { useEffect, useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import {
  comparerFournisseurs,
  exporterDevisPdf,
  proposerEntreprisesReparation,
  trouverAlternative,
  type DevisApi,
  type EntrepriseReparationApi,
  type FournisseurComparateurApi,
} from '../api'
import Alert from '../components/Alert'
import ChatbotDevis from '../components/ChatbotDevis'
import LigneIcone from '../components/LigneIcone'
import { mockDevis, type LigneDevis } from '../mocks/mockData'
import './DevisPage.css'

const dateDuJour = new Date().toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric' })

function depuisDevisApi(devis: DevisApi): LigneDevis[] {
  return devis.lignes.map((ligne) => ({
    id: ligne.reference,
    nom: ligne.nom,
    quantite: ligne.quantite,
    prixUnitaire: ligne.prix_unitaire,
    unite: ligne.unite,
    categorie: ligne.categorie,
  }))
}

function DevisPage() {
  const location = useLocation()
  const devisApi = (location.state as { devis?: DevisApi } | null)?.devis
  const estDonneesReelles = Boolean(devisApi)

  const [lignes, setLignes] = useState<LigneDevis[]>(devisApi ? depuisDevisApi(devisApi) : mockDevis)
  const [isExporting, setIsExporting] = useState(false)
  const [erreurExport, setErreurExport] = useState<string | null>(null)
  const [ligneEnRecherche, setLigneEnRecherche] = useState<string | null>(null)
  const [messageAlternative, setMessageAlternative] = useState<string | null>(null)
  const [comparateurOuvert, setComparateurOuvert] = useState<string | null>(null)
  const [comparateurs, setComparateurs] = useState<Record<string, FournisseurComparateurApi[]>>({})
  const [comparateurEnCours, setComparateurEnCours] = useState<string | null>(null)
  const [erreurComparateur, setErreurComparateur] = useState<string | null>(null)
  const [entreprises, setEntreprises] = useState<EntrepriseReparationApi[]>([])
  const [isChargementEntreprises, setIsChargementEntreprises] = useState(false)
  const [souhaiteProfessionnel, setSouhaiteProfessionnel] = useState<boolean | null>(null)

  const categoriePrincipale = lignes[0]?.categorie

  useEffect(() => {
    if (!categoriePrincipale || souhaiteProfessionnel !== true) return
    let annule = false
    setIsChargementEntreprises(true)
    proposerEntreprisesReparation(categoriePrincipale)
      .then((resultat) => {
        if (!annule) setEntreprises(resultat.entreprises)
      })
      .catch(() => {
        if (!annule) setEntreprises([])
      })
      .finally(() => {
        if (!annule) setIsChargementEntreprises(false)
      })
    return () => {
      annule = true
    }
  }, [categoriePrincipale, souhaiteProfessionnel])

  const total = useMemo(
    () => lignes.reduce((somme, ligne) => somme + ligne.quantite * ligne.prixUnitaire, 0),
    [lignes],
  )

  const exporterPdf = async () => {
    setIsExporting(true)
    setErreurExport(null)
    try {
      const blob = await exporterDevisPdf(lignes)
      const url = URL.createObjectURL(blob)
      const lien = document.createElement('a')
      lien.href = url
      lien.download = 'devis-snapdevis.pdf'
      document.body.appendChild(lien)
      lien.click()
      lien.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      setErreurExport(err instanceof Error ? err.message : "Impossible de générer le PDF pour le moment.")
    } finally {
      setIsExporting(false)
    }
  }

  const modifierQuantite = (id: string, quantite: number) => {
    setLignes((precedent) =>
      precedent.map((ligne) => (ligne.id === id ? { ...ligne, quantite: Math.max(0, quantite) } : ligne)),
    )
  }

  const supprimerLigne = (id: string) => {
    setLignes((precedent) => precedent.filter((ligne) => ligne.id !== id))
  }

  const proposerAlternative = async (ligne: LigneDevis) => {
    setLigneEnRecherche(ligne.id)
    setMessageAlternative(null)
    try {
      const resultat = await trouverAlternative(ligne.id, ligne.categorie, ligne.prixUnitaire)
      if (!resultat.trouve || !resultat.reference) {
        setMessageAlternative(`Aucune alternative moins chère disponible pour « ${ligne.nom} ».`)
        return
      }
      setLignes((precedent) =>
        precedent.map((l) =>
          l.id === ligne.id
            ? {
                ...l,
                id: resultat.reference as string,
                nom: resultat.nom as string,
                prixUnitaire: resultat.prix as number,
                unite: resultat.unite as string,
              }
            : l,
        ),
      )
    } catch (err) {
      setMessageAlternative(err instanceof Error ? err.message : "Impossible de proposer une alternative pour le moment.")
    } finally {
      setLigneEnRecherche(null)
    }
  }

  const basculerComparateur = async (ligne: LigneDevis) => {
    if (comparateurOuvert === ligne.id) {
      setComparateurOuvert(null)
      return
    }
    setComparateurOuvert(ligne.id)
    if (comparateurs[ligne.id]) return

    setComparateurEnCours(ligne.id)
    setErreurComparateur(null)
    try {
      const resultat = await comparerFournisseurs(ligne.id, ligne.nom, ligne.prixUnitaire)
      setComparateurs((precedent) => ({ ...precedent, [ligne.id]: resultat.fournisseurs }))
    } catch (err) {
      setErreurComparateur(err instanceof Error ? err.message : 'Impossible de comparer les prix pour le moment.')
    } finally {
      setComparateurEnCours(null)
    }
  }

  const appliquerPrixFournisseur = (ligneId: string, prix: number) => {
    setLignes((precedent) => precedent.map((ligne) => (ligne.id === ligneId ? { ...ligne, prixUnitaire: prix } : ligne)))
    setComparateurOuvert(null)
  }

  return (
    <section className="page">
      <span className="page-eyebrow">
        <span className="page-eyebrow-ping" />
        Étape 3 sur 3
      </span>

      {erreurExport && <Alert type="error">{erreurExport}</Alert>}

      {!estDonneesReelles && (
        <Alert type="info">
          Devis d'exemple (accès direct à l'écran) — passez par le parcours complet pour un devis généré à partir du
          catalogue.
        </Alert>
      )}

      <div className="quote-wrap">
        <div className="quote">
          <div className="quote-inner">
            <div className="quote-head">
              <div className="qh-brand">
                <span className="qh-dot" />
                <span className="qh-txt">Devis SnapDevis</span>
              </div>
              <div className="qh-meta text-mono">
                Généré le {dateDuJour}
                <br />
                Session #A1B2C3
              </div>
            </div>

            {lignes.map((ligne, index) => {
              const surTeal = index % 2 === 0
              const couleur = surTeal ? 'var(--color-accent-tech)' : 'var(--color-accent-copper)'
              return (
                <div key={ligne.id}>
                  <div className="li">
                    <div className="li-icon" style={{ background: surTeal ? 'var(--color-accent-tech-soft)' : 'var(--color-accent-copper-soft)' }}>
                      <LigneIcone categorie={ligne.categorie} couleur={couleur} />
                    </div>
                    <div className="li-mid">
                      <p className="li-name">{ligne.nom}</p>
                      <p className="li-cat">{ligne.categorie}</p>
                      <div className="li-actions">
                        <button
                          type="button"
                          className="li-action"
                          disabled={ligneEnRecherche === ligne.id}
                          onClick={() => proposerAlternative(ligne)}
                        >
                          {ligneEnRecherche === ligne.id ? 'Recherche…' : 'Alternative moins chère'}
                        </button>
                        <button type="button" className="li-action" onClick={() => basculerComparateur(ligne)}>
                          {comparateurOuvert === ligne.id ? 'Fermer le comparatif' : 'Comparer les prix'}
                        </button>
                        <button type="button" className="li-action li-action-danger" onClick={() => supprimerLigne(ligne.id)}>
                          Supprimer
                        </button>
                      </div>
                    </div>
                    <div className="li-right">
                      <div className="li-qty">
                        <button type="button" aria-label="Diminuer la quantité" onClick={() => modifierQuantite(ligne.id, ligne.quantite - 1)}>
                          −
                        </button>
                        <span className="text-mono">{ligne.quantite}</span>
                        <button type="button" aria-label="Augmenter la quantité" onClick={() => modifierQuantite(ligne.id, ligne.quantite + 1)}>
                          +
                        </button>
                      </div>
                      <div className="li-price text-mono">{(ligne.quantite * ligne.prixUnitaire).toFixed(2)} €</div>
                    </div>
                  </div>

                  {comparateurOuvert === ligne.id && (
                    <div className="comparateur-panel">
                      {comparateurEnCours === ligne.id && (
                        <p className="page-lead" style={{ fontSize: '0.75rem' }}>
                          Comparaison des fournisseurs…
                        </p>
                      )}
                      {erreurComparateur && !comparateurs[ligne.id] && comparateurEnCours !== ligne.id && (
                        <Alert type="error">{erreurComparateur}</Alert>
                      )}
                      {comparateurs[ligne.id]?.map((fournisseur) => (
                        <div
                          className={`comparateur-row ${fournisseur.moins_cher ? 'comparateur-row-moins-cher' : ''}`}
                          key={fournisseur.nom}
                        >
                          <div className="comparateur-row-info">
                            <span>
                              {fournisseur.nom}
                              {fournisseur.moins_cher ? ' · le moins cher' : ''}
                            </span>
                            <span className="comparateur-row-meta">
                              ★ {fournisseur.note.toFixed(1)} ({fournisseur.nombre_avis} avis) · {fournisseur.delai_livraison}
                            </span>
                          </div>
                          <span className="text-numeric">{fournisseur.prix.toFixed(2)} €</span>
                          <button
                            type="button"
                            className="li-action"
                            onClick={() => appliquerPrixFournisseur(ligne.id, fournisseur.prix)}
                          >
                            Utiliser ce prix
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}

            <div className="quote-total">
              <span className="tt-label">Total estimé</span>
              <span className="tt-val text-gradient">{total.toFixed(2)} €</span>
            </div>

            {messageAlternative && <Alert type="info">{messageAlternative}</Alert>}

            <div className="quote-actions">
              <button type="button" className="btn btn-primary" disabled={isExporting} onClick={exporterPdf}>
                {isExporting ? 'Génération du PDF…' : 'Exporter en PDF'}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <h2>Besoin d'un professionnel pour réaliser les travaux ?</h2>
        <p className="page-lead" style={{ maxWidth: 'none' }}>
          Si vous préférez ne pas réaliser les travaux vous-même, on peut vous suggérer des entreprises proches de
          chez vous.
        </p>
        <div className="btn-row" style={{ marginTop: 'var(--space-4)' }}>
          <button
            type="button"
            className={`btn ${souhaiteProfessionnel === true ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setSouhaiteProfessionnel(true)}
          >
            Oui, montrez-moi des professionnels
          </button>
          <button
            type="button"
            className={`btn ${souhaiteProfessionnel === false ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setSouhaiteProfessionnel(false)}
          >
            Non merci
          </button>
        </div>

        {souhaiteProfessionnel === true &&
          (isChargementEntreprises ? (
            <p className="page-lead" style={{ marginTop: 'var(--space-4)' }}>
              Recherche d'entreprises…
            </p>
          ) : (
            <div className="stat-row" style={{ marginTop: 'var(--space-4)' }}>
              {entreprises.map((entreprise) => {
                const sujet = encodeURIComponent(`Demande de devis — ${entreprise.specialite}`)
                const corps = encodeURIComponent(
                  `Bonjour,\n\nJe vous contacte suite à un diagnostic réalisé avec SnapDevis pour une intervention de type « ${entreprise.specialite} » (devis estimé à ${total.toFixed(2)} €).\n\nSeriez-vous disponible pour réaliser cette intervention ? Pourriez-vous me proposer un rendez-vous ?\n\nMerci d'avance,`,
                )
                const lienMailto = `mailto:${entreprise.email}?subject=${sujet}&body=${corps}`
                return (
                  <a
                    className="stat-tile"
                    key={entreprise.nom}
                    href={lienMailto}
                    style={{ textDecoration: 'none', color: 'inherit', display: 'flex' }}
                  >
                    <span className="stat-label">{entreprise.nom}</span>
                    <span className="stat-value" style={{ fontSize: '1.125rem' }}>
                      ★ {entreprise.note.toFixed(1)} ({entreprise.nombre_avis} avis)
                    </span>
                    <span className="page-lead" style={{ fontSize: '0.78125rem' }}>
                      {entreprise.specialite} · à {entreprise.distance_km.toFixed(1)} km · {entreprise.delai_intervention}
                    </span>
                    <span className="li-action" style={{ marginTop: 'var(--space-2)' }}>
                      ✉ Contacter par email
                    </span>
                  </a>
                )
              })}
            </div>
          ))}
      </div>

      <ChatbotDevis lignes={lignes} total={total} />
    </section>
  )
}

export default DevisPage
