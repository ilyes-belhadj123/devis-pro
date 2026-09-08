import type { DevisEntretienApi, DiagnosticEntretienApi } from '../api'

export const mockDiagnosticEntretien: DiagnosticEntretienApi = {
  lieu: 'exterieur',
  type_espace_cle: 'mixte',
  type_espace_label: 'Pelouse + haie de thuyas (exemple)',
  observations_visuelles: '',
  categorie: 'tonte',
  confiance: 0.6,
  taches_suggerees: ['Tonte de pelouse (~120 m²)', 'Taille de haie (~18 ml)', 'Désherbage des massifs'],
  estimation_surface: { valeur: 120, unite: 'm²', a_confirmer: true },
  questions_clarification: [],
  suggestions_clarification: [],
  degrade: true,
  session_id: null,
}

const ligneTonte = {
  designation: 'Tonte pelouse standard',
  categorie: 'tonte',
  unite: 'm2',
  prix_unitaire: 0.35,
  quantite: 120,
  sous_total: 42,
}
const ligneEvacuation = {
  designation: "Ramassage et evacuation de l'herbe coupee",
  categorie: 'evacuation',
  unite: 'm2',
  prix_unitaire: 0.15,
  quantite: 120,
  sous_total: 18,
}
const ligneEngrais = {
  designation: 'Engrais gazon organique',
  categorie: 'fertilisation',
  unite: 'sac 20kg',
  prix_unitaire: 34,
  quantite: 1,
  sous_total: 34,
}

export const mockDevisEntretien: DevisEntretienApi = {
  compte_id: 'demo',
  categorie: 'tonte',
  formules: [
    { niveau: 'eco', label: 'Éco', description: 'Prestations essentielles', lignes: [ligneTonte], total: 42 },
    {
      niveau: 'standard',
      label: 'Standard',
      description: 'Recommandé — essentiel + finitions',
      lignes: [ligneTonte, ligneEvacuation],
      total: 60,
    },
    {
      niveau: 'premium',
      label: 'Premium',
      description: 'Confort complet + options renforcées',
      lignes: [ligneTonte, ligneEvacuation, ligneEngrais],
      total: 94,
    },
  ],
  ajustements_appris: [],
}
