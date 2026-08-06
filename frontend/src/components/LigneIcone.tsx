type LigneIconeProps = {
  categorie: string
  couleur: string
}

const CHEMINS: Record<string, string> = {
  peinture: 'M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z',
  plomberie:
    'M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z',
  fixation: 'M9 5a3 3 0 1 0 6 0 3 3 0 1 0 -6 0M12 8v14M5 12H2a10 10 0 0 0 20 0h-3',
  electricite: 'M13 2 3 14h7v8l10-12h-7z',
  jardin: 'M12 2c4 4 6 8 6 11a6 6 0 1 1-12 0c0-3 2-7 6-11z',
}

function LigneIcone({ categorie, couleur }: LigneIconeProps) {
  const chemin = CHEMINS[categorie.toLowerCase()] ?? CHEMINS.fixation

  return (
    <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke={couleur} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d={chemin} />
    </svg>
  )
}

export default LigneIcone
