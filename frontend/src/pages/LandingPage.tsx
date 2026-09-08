import { useNavigate } from 'react-router-dom'
import './LandingPage.css'

function LandingPage() {
  const navigate = useNavigate()

  return (
    <section className="page page-wide">
      <div className="landing-intro">
        <span className="page-eyebrow">
          <span className="page-eyebrow-ping" />
          SnapDevis
        </span>

        <h1>
          Une photo.
          <br />
          <span className="text-gradient">Un devis chiffré.</span>
        </h1>

        <p className="page-lead">Choisissez votre activité pour démarrer.</p>
      </div>

      <div className="landing-cards">
        <button type="button" className="card landing-card landing-card-chantier" onClick={() => navigate('/bricolage')}>
          <div>
            <span className="landing-card-badge">🚧 Chantier & rénovation</span>
          </div>
          <div className="icon-badge">🧰</div>
          <h2 style={{ marginTop: 'var(--space-4)', marginBottom: 'var(--space-2)' }}>Bricolage</h2>
          <p className="page-lead" style={{ maxWidth: 'none' }}>
            Réparation, montage, peinture, plomberie... diagnostic photo pour enseignes de bricolage et artisans du
            bâtiment.
          </p>
        </button>

        <button type="button" className="card landing-card landing-card-bio" onClick={() => navigate('/entretien')}>
          <div>
            <span className="landing-card-badge">🌱 Espaces verts & bio</span>
          </div>
          <div className="icon-badge">🌿</div>
          <h2 style={{ marginTop: 'var(--space-4)', marginBottom: 'var(--space-2)' }}>Entretien</h2>
          <p className="page-lead" style={{ maxWidth: 'none' }}>
            Espaces verts, intérieur et extérieur — devis et contrats récurrents pour un entretien durable et
            éco-responsable.
          </p>
          <span className="landing-card-bio-leaf">🍃</span>
        </button>
      </div>
    </section>
  )
}

export default LandingPage
