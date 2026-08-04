import type { DiagnosticApi } from '../api'

export const mockDiagnostic: DiagnosticApi = {
  probleme_cle: 'mur_fissure_interieur',
  probleme_label: 'Mur fissuré intérieur',
  categorie: 'peinture',
  confiance: 0.92,
  questions_clarification: ['Le mur est-il intérieur ou extérieur ?'],
  degrade: false,
  session_id: null,
}

export type LigneDevis = {
  id: string
  nom: string
  quantite: number
  prixUnitaire: number
  unite: string
  categorie: string
}

export const mockDevis: LigneDevis[] = [
  { id: '1', nom: 'Enduit de rebouchage 1kg', quantite: 1, prixUnitaire: 8.9, unite: 'pot', categorie: 'Peinture' },
  { id: '2', nom: 'Spatule inox 10cm', quantite: 1, prixUnitaire: 4.5, unite: 'unité', categorie: 'Fixation' },
  { id: '3', nom: 'Ponceuse manuelle', quantite: 1, prixUnitaire: 12.0, unite: 'unité', categorie: 'Fixation' },
  { id: '4', nom: 'Gants de protection', quantite: 1, prixUnitaire: 3.2, unite: 'paire', categorie: 'Fixation' },
]
