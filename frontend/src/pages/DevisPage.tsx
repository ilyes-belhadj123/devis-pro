import { useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import type { DevisApi } from '../api'
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

  const total = useMemo(
    () => lignes.reduce((somme, ligne) => somme + ligne.quantite * ligne.prixUnitaire, 0),
    [lignes],
  )

  const modifierQuantite = (id: string, quantite: number) => {
    setLignes((precedent) =>
      precedent.map((ligne) => (ligne.id === id ? { ...ligne, quantite: Math.max(0, quantite) } : ligne)),
    )
  }

  const supprimerLigne = (id: string) => {
    setLignes((precedent) => precedent.filter((ligne) => ligne.id !== id))
  }

  const proposerAlternative = (id: string) => {
    setLignes((precedent) =>
      precedent.map((ligne) =>
        ligne.id === id
          ? { ...ligne, nom: `${ligne.nom.replace(/ \(alternative\)$/, '')} (alternative)`, prixUnitaire: Math.round(ligne.prixUnitaire * 0.8 * 100) / 100 }
          : ligne,
      ),
    )
  }

  return (
    <section className="page">
      <div className="devis-actions no-print">
        <span className="page-eyebrow">Étape 3 sur 3</span>
        <button type="button" className="btn btn-primary" onClick={() => window.print()}>
          Exporter en PDF
        </button>
      </div>

      {!estDonneesReelles && (
        <p className="no-print" style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
          Devis d'exemple (accès direct à l'écran) — passez par le parcours complet pour un devis généré à partir du
          catalogue.
        </p>
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

        <table className="devis-table">
          <thead>
            <tr>
              <th>Produit</th>
              <th>Catégorie</th>
              <th>Qté</th>
              <th>Prix unit.</th>
              <th>Sous-total</th>
              <th className="no-print"></th>
            </tr>
          </thead>
          <tbody>
            {lignes.map((ligne) => (
              <tr key={ligne.id}>
                <td>{ligne.nom}</td>
                <td>{ligne.categorie}</td>
                <td>
                  <input
                    type="number"
                    min={0}
                    className="qty-input no-print"
                    value={ligne.quantite}
                    onChange={(e) => modifierQuantite(ligne.id, Number(e.target.value))}
                  />
                  <span className="print-only">{ligne.quantite}</span> {ligne.unite}
                </td>
                <td className="text-numeric">{ligne.prixUnitaire.toFixed(2)} €</td>
                <td className="text-numeric">{(ligne.quantite * ligne.prixUnitaire).toFixed(2)} €</td>
                <td className="no-print devis-row-actions">
                  <button type="button" className="btn-link" onClick={() => proposerAlternative(ligne.id)}>
                    Alternative moins chère
                  </button>
                  <button type="button" className="btn-ghost" onClick={() => supprimerLigne(ligne.id)}>
                    Supprimer
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="devis-total-row">
          <span>Total estimé</span>
          <span className="text-numeric devis-total-amount">{total.toFixed(2)} €</span>
        </div>
      </div>
    </section>
  )
}

export default DevisPage
