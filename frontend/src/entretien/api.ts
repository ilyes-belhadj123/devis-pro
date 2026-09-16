const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8010'

async function lireDetailErreur(response: Response): Promise<string | null> {
  try {
    const corps = await response.json()
    return typeof corps?.detail === 'string' ? corps.detail : null
  } catch {
    return null
  }
}

async function lancerErreur(response: Response, messageParDefaut: string): Promise<never> {
  const detail = await lireDetailErreur(response)
  throw new Error(detail ?? messageParDefaut)
}

export type CompteArtisanApi = {
  id: string
  nom: string
  cree_le: string
}

export type ProduitEntretienApi = {
  designation: string
  unite: string
  prix: number
  categorie: string
}

export async function getCompteDemo(): Promise<CompteArtisanApi> {
  const response = await fetch(`${API_URL}/entretien/comptes/moi`)
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors du chargement du compte`)
  }
  return response.json()
}

export async function getCatalogueEntretien(compteId: string): Promise<ProduitEntretienApi[]> {
  const response = await fetch(`${API_URL}/entretien/catalogue?compte_id=${encodeURIComponent(compteId)}`)
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors du chargement du catalogue`)
  }
  return response.json()
}

export async function telechargerTemplateCatalogue(): Promise<Blob> {
  const response = await fetch(`${API_URL}/entretien/catalogue/template`)
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors du téléchargement du modèle`)
  }
  return response.blob()
}

export async function importerCatalogueEntretien(compteId: string, fichier: File): Promise<ProduitEntretienApi[]> {
  const formData = new FormData()
  formData.append('fichier', fichier)

  const response = await fetch(`${API_URL}/entretien/catalogue/import?compte_id=${encodeURIComponent(compteId)}`, {
    method: 'POST',
    body: formData,
  })
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors de l'import du catalogue`)
  }
  return response.json()
}

export type EstimationSurfaceApi = { valeur: number; unite: string; a_confirmer: boolean } | null

export type ZoneDetecteeApi = {
  photo_index: number
  x: number
  y: number
  largeur: number
  hauteur: number
  label?: string
}

export type DiagnosticEntretienApi = {
  lieu: string
  type_espace_cle: string
  type_espace_label: string
  observations_visuelles?: string
  categorie: string
  confiance: number
  taches_suggerees: string[]
  estimation_surface?: EstimationSurfaceApi
  questions_clarification: string[]
  suggestions_clarification?: string[][]
  zones_detectees?: ZoneDetecteeApi[]
  degrade: boolean
  session_id?: string | null
}

export async function analyserPhotoEntretien(fichiers: File[], note?: string): Promise<DiagnosticEntretienApi> {
  const formData = new FormData()
  fichiers.forEach((fichier) => formData.append('photos', fichier))
  if (note && note.trim()) {
    formData.append('note', note.trim())
  }

  const response = await fetch(`${API_URL}/entretien/diagnostic/analyser`, {
    method: 'POST',
    body: formData,
  })
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors de l'analyse de la photo`)
  }
  return response.json()
}

export async function affinerDiagnosticEntretien(
  diagnostic: DiagnosticEntretienApi,
  reponse: string,
): Promise<DiagnosticEntretienApi> {
  const formData = new FormData()
  formData.append('lieu', diagnostic.lieu)
  formData.append('type_espace_cle', diagnostic.type_espace_cle)
  formData.append('categorie', diagnostic.categorie)
  formData.append('reponse', reponse)
  if (diagnostic.session_id) {
    formData.append('session_id', diagnostic.session_id)
  }

  const response = await fetch(`${API_URL}/entretien/diagnostic/affiner`, {
    method: 'POST',
    body: formData,
  })
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors de l'affinage du diagnostic`)
  }
  return response.json()
}

export type LigneDevisEntretienApi = {
  designation: string
  categorie: string
  unite: string
  prix_unitaire: number
  quantite: number
  sous_total: number
}

export type FormuleDevisApi = {
  niveau: string
  label: string
  description: string
  lignes: LigneDevisEntretienApi[]
  total: number
}

export type DevisEntretienApi = {
  compte_id: string
  categorie: string
  formules: FormuleDevisApi[]
  ajustements_appris: string[]
}

export async function genererDevisEntretien(params: {
  compteId: string
  lieu: string
  categorie: string
  tachesSuggerees: string[]
  estimationSurface?: { valeur: number; unite: string } | null
}): Promise<DevisEntretienApi> {
  const response = await fetch(`${API_URL}/entretien/devis/generer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      compte_id: params.compteId,
      lieu: params.lieu,
      categorie: params.categorie,
      taches_suggerees: params.tachesSuggerees,
      estimation_surface: params.estimationSurface ?? null,
    }),
  })
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors de la génération du devis`)
  }
  return response.json()
}

export type ContratRecurrentApi = {
  frequence: string
  frequence_label: string
  duree_mois: number
  interventions_an: number
  prix_intervention_ponctuel: number
  prix_intervention_contrat: number
  prix_annuel: number
  prix_mensuel: number
  economie_pourcentage: number
}

export async function genererContratRecurrent(
  lignes: LigneDevisEntretienApi[],
  frequence: string,
  dureeMois: number,
): Promise<ContratRecurrentApi> {
  const response = await fetch(`${API_URL}/entretien/devis/contrat-recurrent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      lignes: lignes.map((ligne) => ({
        designation: ligne.designation,
        categorie: ligne.categorie,
        unite: ligne.unite,
        prix_unitaire: ligne.prix_unitaire,
        quantite: ligne.quantite,
      })),
      frequence,
      duree_mois: dureeMois,
    }),
  })
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors du calcul du contrat récurrent`)
  }
  return response.json()
}

export type FournisseurComparateurApi = {
  nom: string
  prix: number
  moins_cher: boolean
  delai_livraison: string
  note: number
  nombre_avis: number
}

export type ComparateurEntretienApi = {
  designation: string
  fournisseurs: FournisseurComparateurApi[]
}

export async function comparerFournisseursEntretien(
  designation: string,
  prixActuel: number,
): Promise<ComparateurEntretienApi> {
  const response = await fetch(`${API_URL}/entretien/devis/comparateur`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ designation, prix_actuel: prixActuel }),
  })
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors de la comparaison des prix`)
  }
  return response.json()
}

function formulesPourApi(formules: FormuleDevisApi[]) {
  return formules.map((formule) => ({
    niveau: formule.niveau,
    label: formule.label,
    description: formule.description,
    lignes: formule.lignes.map((ligne) => ({
      designation: ligne.designation,
      categorie: ligne.categorie,
      unite: ligne.unite,
      prix_unitaire: ligne.prix_unitaire,
      quantite: ligne.quantite,
    })),
  }))
}

export type DevisValidationApi = {
  id: string
  compte_id: string
  categorie: string
  statut: string
  formules: FormuleDevisApi[]
  formule_choisie?: string | null
  cree_le: string
  valide_le?: string | null
  envoye_le?: string | null
  accepte_le?: string | null
}

export type DevisValidationResumeApi = {
  id: string
  categorie: string
  statut: string
  total_standard: number
  cree_le: string
}

export async function creerDevisValidation(
  compteId: string,
  categorie: string,
  formules: FormuleDevisApi[],
): Promise<DevisValidationApi> {
  const response = await fetch(`${API_URL}/entretien/validation/devis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ compte_id: compteId, categorie, formules: formulesPourApi(formules) }),
  })
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors de la création du devis à valider`)
  }
  return response.json()
}

export async function listerDevisValidation(compteId: string): Promise<DevisValidationResumeApi[]> {
  const response = await fetch(`${API_URL}/entretien/validation/devis?compte_id=${encodeURIComponent(compteId)}`)
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors du chargement de la file de validation`)
  }
  return response.json()
}

export async function getDevisValidation(id: string): Promise<DevisValidationApi> {
  const response = await fetch(`${API_URL}/entretien/validation/devis/${id}`)
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors du chargement du devis`)
  }
  return response.json()
}

export async function modifierDevisValidation(id: string, formules: FormuleDevisApi[]): Promise<DevisValidationApi> {
  const response = await fetch(`${API_URL}/entretien/validation/devis/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ formules: formulesPourApi(formules) }),
  })
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors de la modification du devis`)
  }
  return response.json()
}

export async function validerDevisValidation(id: string): Promise<DevisValidationApi> {
  const response = await fetch(`${API_URL}/entretien/validation/devis/${id}/valider`, { method: 'POST' })
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors de la validation du devis`)
  }
  return response.json()
}

export async function envoyerDevisValidation(id: string): Promise<DevisValidationApi> {
  const response = await fetch(`${API_URL}/entretien/validation/devis/${id}/envoyer`, { method: 'POST' })
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors de l'envoi du devis`)
  }
  return response.json()
}

export async function getDevisPublic(id: string): Promise<DevisValidationApi> {
  const response = await fetch(`${API_URL}/entretien/validation/devis/${id}/public`)
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors du chargement du devis`)
  }
  return response.json()
}

export async function accepterDevisPublic(id: string, niveauChoisi: string): Promise<DevisValidationApi> {
  const response = await fetch(`${API_URL}/entretien/validation/devis/${id}/accepter`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ niveau_choisi: niveauChoisi }),
  })
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors de l'acceptation du devis`)
  }
  return response.json()
}

export async function exporterDevisValidationPdf(id: string, niveau: string): Promise<Blob> {
  const response = await fetch(`${API_URL}/entretien/validation/devis/${id}/pdf?niveau=${encodeURIComponent(niveau)}`)
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors de l'export PDF`)
  }
  return response.blob()
}

export async function exporterDevisValidationFacturation(
  id: string,
  niveau: string,
  format: 'csv' | 'json',
): Promise<Blob> {
  const response = await fetch(
    `${API_URL}/entretien/validation/devis/${id}/export?niveau=${encodeURIComponent(niveau)}&format=${format}`,
  )
  if (!response.ok) {
    await lancerErreur(response, `Erreur ${response.status} lors de l'export facturation`)
  }
  return response.blob()
}
