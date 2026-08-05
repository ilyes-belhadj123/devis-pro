import { useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { exporterDevisPdf, trouverAlternative, type DevisApi } from '../api'
import Alert from '../components/Alert'
import { mockDevis, type LigneDevis } from '../mocks/mockData'
import { iconePourCategorie } from '../utils/iconesCategorie'
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

  return (
    <section className="page">
      <div className="devis-actions">
        <span className="page-eyebrow">Étape 3 sur 3</span>
        <button type="button" className="btn btn-primary" disabled={isExporting} onClick={exporterPdf}>
          {isExporting ? 'Génération du PDF…' : 'Exporter en PDF'}
        </button>
      </div>

      {erreurExport && <Alert type="error">{erreurExport}</Alert>}

      {!estDonneesReelles && (
        <Alert type="info">
          Devis d'exemple (accès direct à l'écran) — passez par le parcours complet pour un devis généré à partir du
          catalogue.
        </Alert>
      )}

      <div className="card devis-sheet">
        <header className="devis-sheet-header">
          <div>
            <span className="logo-print">Snap·Devis</span>
            <p className="page-lead" style={{ fontSize: '0.8125rem', marginTop: 4 }}>
              Devis généré le {dateDuJour}
            </p>
          </div>
          <span className="badge">Session #A1B2C3</span>
        </header>

        <ul className="devis-liste">
          {lignes.map((ligne) => (
            <li className="devis-item" key={ligne.id}>
              <span className="devis-item-icon">{iconePourCategorie(ligne.categorie)}</span>

              <div className="devis-item-corps">
                <span className="devis-item-nom">{ligne.nom}</span>
                <span className="devis-item-categorie">{ligne.categorie}</span>
                <div className="devis-item-actions">
                  <button
                    type="button"
                    className="btn-link"
                    disabled={ligneEnRecherche === ligne.id}
                    onClick={() => proposerAlternative(ligne)}
                  >
                    {ligneEnRecherche === ligne.id ? 'Recherche…' : 'Alternative moins chère'}
                  </button>
                  <button type="button" className="btn-ghost" onClick={() => supprimerLigne(ligne.id)}>
                    Supprimer
                  </button>
                </div>
              </div>

              <div className="devis-item-qty">
                <button
                  type="button"
                  className="qty-btn"
                  aria-label="Diminuer la quantité"
                  disabled={ligne.quantite <= 0}
                  onClick={() => modifierQuantite(ligne.id, ligne.quantite - 1)}
                >
                  −
                </button>
                <span className="qty-value">{ligne.quantite}</span>
                <button
                  type="button"
                  className="qty-btn"
                  aria-label="Augmenter la quantité"
                  onClick={() => modifierQuantite(ligne.id, ligne.quantite + 1)}
                >
                  +
                </button>
              </div>

              <div className="devis-item-prix">
                <span className="devis-item-prix-unitaire">
                  {ligne.prixUnitaire.toFixed(2)} € / {ligne.unite}
                </span>
                <span className="devis-item-sous-total text-numeric">
                  {(ligne.quantite * ligne.prixUnitaire).toFixed(2)} €
                </span>
              </div>
            </li>
          ))}
        </ul>

        <div className="devis-total-row">
          <span>Total estimé</span>
          <span className="text-numeric devis-total-amount">{total.toFixed(2)} €</span>
        </div>

        {messageAlternative && <Alert type="info">{messageAlternative}</Alert>}
      </div>
    </section>
  )
}

export default DevisPage
