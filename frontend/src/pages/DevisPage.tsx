import { useState } from 'react'
import { mockDevis, type LigneDevis } from '../mocks/mockData'

function DevisPage() {
  const [lignes, setLignes] = useState<LigneDevis[]>(mockDevis)

  const total = lignes.reduce((somme, ligne) => somme + ligne.quantite * ligne.prixUnitaire, 0)

  const modifierQuantite = (id: string, quantite: number) => {
    setLignes((precedent) =>
      precedent.map((ligne) => (ligne.id === id ? { ...ligne, quantite: Math.max(0, quantite) } : ligne)),
    )
  }

  const supprimerLigne = (id: string) => {
    setLignes((precedent) => precedent.filter((ligne) => ligne.id !== id))
  }

  return (
    <section className="page page-devis">
      <h1>Votre devis</h1>

      <table className="devis-table">
        <thead>
          <tr>
            <th>Produit</th>
            <th>Catégorie</th>
            <th>Quantité</th>
            <th>Prix unitaire</th>
            <th>Sous-total</th>
            <th></th>
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
                  value={ligne.quantite}
                  onChange={(e) => modifierQuantite(ligne.id, Number(e.target.value))}
                />
                {' '}{ligne.unite}
              </td>
              <td>{ligne.prixUnitaire.toFixed(2)} €</td>
              <td>{(ligne.quantite * ligne.prixUnitaire).toFixed(2)} €</td>
              <td>
                <button type="button" onClick={() => supprimerLigne(ligne.id)}>
                  Supprimer
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="devis-total">Total : {total.toFixed(2)} €</p>

      <button type="button">Exporter en PDF</button>
    </section>
  )
}

export default DevisPage
