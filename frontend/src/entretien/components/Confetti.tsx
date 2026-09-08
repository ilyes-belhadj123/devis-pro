import { useState } from 'react'
import './Confetti.css'

const COULEURS = ['#FF6A3D', '#FFB238', '#1F8A72', '#8BC98A', '#4C9A5B']

function Confetti() {
  const [pieces] = useState(() =>
    Array.from({ length: 70 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      delay: Math.random() * 0.5,
      duree: 2.4 + Math.random() * 1.4,
      couleur: COULEURS[i % COULEURS.length],
      taille: 6 + Math.random() * 6,
    })),
  )

  return (
    <div className="confetti-layer" aria-hidden="true">
      {pieces.map((piece) => (
        <span
          key={piece.id}
          className="confetti-piece"
          style={{
            left: `${piece.left}%`,
            backgroundColor: piece.couleur,
            width: piece.taille,
            height: piece.taille * 0.4,
            animationDelay: `${piece.delay}s`,
            animationDuration: `${piece.duree}s`,
          }}
        />
      ))}
    </div>
  )
}

export default Confetti
