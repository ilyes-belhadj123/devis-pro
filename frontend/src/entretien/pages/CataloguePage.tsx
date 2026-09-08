import { useCallback, useEffect, useRef, useState } from 'react'
import Alert from '../../components/Alert'
import {
  getCatalogueEntretien,
  getCompteDemo,
  importerCatalogueEntretien,
  telechargerTemplateCatalogue,
  type ProduitEntretienApi,
} from '../api'

function CataloguePage() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [compteId, setCompteId] = useState<string | null>(null)
  const [compteNom, setCompteNom] = useState('')
  const [produits, setProduits] = useState<ProduitEntretienApi[]>([])
  const [chargement, setChargement] = useState(true)
  const [importEnCours, setImportEnCours] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)

  const chargerCatalogue = useCallback(async (id: string) => {
    const catalogue = await getCatalogueEntretien(id)
    setProduits(catalogue)
  }, [])

  useEffect(() => {
    getCompteDemo()
      .then(async (compte) => {
        setCompteId(compte.id)
        setCompteNom(compte.nom)
        await chargerCatalogue(compte.id)
      })
      .catch((err) => setErreur(err instanceof Error ? err.message : 'Impossible de charger le compte.'))
      .finally(() => setChargement(false))
  }, [chargerCatalogue])

  const telechargerTemplate = async () => {
    try {
      const blob = await telechargerTemplateCatalogue()
      const url = URL.createObjectURL(blob)
      const lien = document.createElement('a')
      lien.href = url
      lien.download = 'modele-catalogue-entretien.csv'
      lien.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setErreur(err instanceof Error ? err.message : 'Impossible de télécharger le modèle.')
    }
  }

  const importerFichier = async (fichier: File | undefined) => {
    if (!fichier || !compteId) return
    setImportEnCours(true)
    setErreur(null)
    try {
      const nouveauCatalogue = await importerCatalogueEntretien(compteId, fichier)
      setProduits(nouveauCatalogue)
    } catch (err) {
      setErreur(err instanceof Error ? err.message : "Erreur lors de l'import du catalogue.")
    } finally {
      setImportEnCours(false)
    }
  }

  return (
    <section className="page page-wide">
      <span className="page-eyebrow">Entretien — compte {compteNom || '…'}</span>
      <h1>Votre grille tarifaire</h1>
      <p className="page-lead">
        Importez votre propre catalogue (désignation, unité, prix, catégorie) plutôt que d'utiliser un catalogue
        générique — il remplace entièrement le catalogue actuel de votre compte.
      </p>

      {erreur && <Alert type="error">{erreur}</Alert>}

      <div className="btn-row">
        <button type="button" className="btn btn-secondary" onClick={telechargerTemplate}>
          Télécharger le modèle CSV
        </button>
        <button
          type="button"
          className="btn btn-primary"
          disabled={importEnCours || !compteId}
          onClick={() => inputRef.current?.click()}
        >
          {importEnCours ? 'Import en cours…' : 'Importer un catalogue CSV'}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          hidden
          onChange={(e) => {
            importerFichier(e.target.files?.[0])
            e.target.value = ''
          }}
        />
      </div>

      {chargement ? (
        <p className="page-lead">Chargement du catalogue…</p>
      ) : produits.length === 0 ? (
        <p className="page-lead">Aucun produit dans ce catalogue pour l'instant.</p>
      ) : (
        <div className="card">
          <h2>{produits.length} prestations</h2>
          <div className="table-scroll">
            <table className="devis-table">
              <thead>
                <tr>
                  <th>Désignation</th>
                  <th>Catégorie</th>
                  <th>Unité</th>
                  <th>Prix</th>
                </tr>
              </thead>
              <tbody>
                {produits.map((produit, index) => (
                  <tr key={`${produit.designation}-${index}`}>
                    <td>{produit.designation}</td>
                    <td>{produit.categorie}</td>
                    <td>{produit.unite}</td>
                    <td className="text-numeric">{produit.prix.toFixed(2)} €</td>
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

export default CataloguePage
