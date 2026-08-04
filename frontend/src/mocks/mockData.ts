export const mockDiagnostic = {
  cle: 'mur_fissure_interieur',
  categorie: 'Peinture',
  probleme: 'Mur fissuré intérieur',
  confiance: 0.92,
  questionsClarification: ['Le mur est-il intérieur ou extérieur ?'],
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
