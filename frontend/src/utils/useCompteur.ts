import { useEffect, useRef, useState } from 'react'

/**
 * Anime une valeur numerique de sa valeur precedente vers sa nouvelle valeur (ease-out),
 * plutot que de l'afficher brute. Premier rendu : anime depuis 0 (effet "compteur" qui
 * grimpe) ; mises a jour suivantes : anime depuis la derniere valeur affichee.
 */
export function useCompteur(valeurCible: number, dureeMs = 700): number {
  const [valeurAffichee, setValeurAffichee] = useState(0)
  const valeurDepart = useRef(0)
  const frameRef = useRef<number>()

  useEffect(() => {
    const depart = valeurDepart.current
    const arrivee = valeurCible
    if (depart === arrivee) return undefined

    const debut = performance.now()

    const animer = (maintenant: number) => {
      const progres = Math.min(1, (maintenant - debut) / dureeMs)
      const progresAdouci = 1 - (1 - progres) ** 3
      setValeurAffichee(depart + (arrivee - depart) * progresAdouci)
      if (progres < 1) {
        frameRef.current = requestAnimationFrame(animer)
      } else {
        valeurDepart.current = arrivee
      }
    }

    frameRef.current = requestAnimationFrame(animer)
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current)
    }
  }, [valeurCible, dureeMs])

  return valeurAffichee
}
