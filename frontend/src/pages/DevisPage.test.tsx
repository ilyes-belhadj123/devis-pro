import { describe, expect, it } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import DevisPage from './DevisPage'

describe('DevisPage', () => {
  it('affiche le total initial calcule a partir des lignes (acces direct, donnees mock)', () => {
    render(
      <MemoryRouter>
        <DevisPage />
      </MemoryRouter>,
    )
    expect(screen.getByText('28.60 €')).toBeInTheDocument()
  })

  it('recalcule le total quand on modifie une quantite', () => {
    render(
      <MemoryRouter>
        <DevisPage />
      </MemoryRouter>,
    )
    const premiereQuantite = screen.getAllByRole('spinbutton')[0]
    fireEvent.change(premiereQuantite, { target: { value: '3' } })

    expect(screen.getByText('46.40 €')).toBeInTheDocument()
  })

  it('supprime une ligne du devis et met a jour le total', () => {
    render(
      <MemoryRouter>
        <DevisPage />
      </MemoryRouter>,
    )
    const boutonsSupprimer = screen.getAllByText('Supprimer')
    fireEvent.click(boutonsSupprimer[0])

    // Total sans la 1ere ligne (enduit 8.90) : 4.50 + 12.00 + 3.20
    expect(screen.getByText('19.70 €')).toBeInTheDocument()
  })
})
