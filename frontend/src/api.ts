const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8010'

export type LigneDevisApi = {
  reference: string
  nom: string
  categorie: string
  unite: string
  prix_unitaire: number
  quantite: number
  sous_total: number
}

export type GroupeCategorieApi = {
  categorie: string
  sous_total: number
}

export type DevisApi = {
  probleme: string
  lignes: LigneDevisApi[]
  groupes: GroupeCategorieApi[]
  total: number
}

export async function genererDevis(probleme: string): Promise<DevisApi> {
  const response = await fetch(`${API_URL}/devis/generer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ probleme }),
  })

  if (!response.ok) {
    throw new Error(`Erreur ${response.status} lors de la génération du devis`)
  }

  return response.json()
}
