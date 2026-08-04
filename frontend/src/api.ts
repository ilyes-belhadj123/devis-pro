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

export type DiagnosticApi = {
  probleme_cle: string
  probleme_label: string
  categorie: string
  confiance: number
  questions_clarification: string[]
  degrade: boolean
  session_id?: string | null
}

export async function analyserPhoto(fichier: File): Promise<DiagnosticApi> {
  const formData = new FormData()
  formData.append('photo', fichier)

  const response = await fetch(`${API_URL}/diagnostic/analyser`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error(`Erreur ${response.status} lors de l'analyse de la photo`)
  }

  return response.json()
}

export async function affinerDiagnostic(
  diagnostic: DiagnosticApi,
  reponse: string,
): Promise<DiagnosticApi> {
  const response = await fetch(`${API_URL}/diagnostic/affiner`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: diagnostic.session_id ?? null,
      probleme_cle: diagnostic.probleme_cle,
      reponse,
    }),
  })

  if (!response.ok) {
    throw new Error(`Erreur ${response.status} lors de l'affinage du diagnostic`)
  }

  return response.json()
}

export async function getStatutCleOpenRouter(): Promise<{ configuree: boolean }> {
  const response = await fetch(`${API_URL}/parametres/openrouter`)
  if (!response.ok) {
    throw new Error(`Erreur ${response.status}`)
  }
  return response.json()
}

export async function definirCleOpenRouter(apiKey: string): Promise<{ configuree: boolean }> {
  const response = await fetch(`${API_URL}/parametres/openrouter`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey }),
  })
  if (!response.ok) {
    throw new Error(`Erreur ${response.status}`)
  }
  return response.json()
}
