import { Link, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import './App.css'
import Logo from './components/Logo'
import LandingPage from './pages/LandingPage'
import UploadPage from './pages/UploadPage'
import DiagnosticPage from './pages/DiagnosticPage'
import DevisPage from './pages/DevisPage'
import ParametresPage from './pages/ParametresPage'
import DashboardPage from './pages/DashboardPage'
import HistoriquePage from './pages/HistoriquePage'
import CataloguePage from './entretien/pages/CataloguePage'
import EntretienUploadPage from './entretien/pages/EntretienUploadPage'
import EntretienDiagnosticPage from './entretien/pages/EntretienDiagnosticPage'
import EntretienDevisPage from './entretien/pages/EntretienDevisPage'
import EntretienValidationPage from './entretien/pages/EntretienValidationPage'
import EntretienValidationQueuePage from './entretien/pages/EntretienValidationQueuePage'
import EntretienDevisClientPage from './entretien/pages/EntretienDevisClientPage'
import './entretien/theme-entretien.css'

const steps = [
  { to: '/bricolage', numero: 1, label: 'Envoi' },
  { to: '/diagnostic', numero: 2, label: 'Diagnostic' },
  { to: '/devis', numero: 3, label: 'Devis' },
]

const entretienSteps = [
  { to: '/entretien', numero: 1, label: 'Envoi' },
  { to: '/entretien/diagnostic', numero: 2, label: 'Diagnostic' },
  { to: '/entretien/devis', numero: 3, label: 'Devis' },
  { to: '/entretien/validation', numero: 4, label: 'Validation' },
]

function Stepper() {
  const location = useLocation()
  const surAccueil = location.pathname === '/'
  const enEntretien = location.pathname.startsWith('/entretien')
  const etapes = enEntretien ? entretienSteps : steps

  if (surAccueil) return null

  const indexActif = etapes.findIndex((step) => step.to === location.pathname)

  return (
    <nav className="app-nav">
      {etapes.map((step, index) => (
        <span key={step.to} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          {index > 0 && <span className="app-nav-line" />}
          <NavLink
            to={step.to}
            end={step.to === '/bricolage' || step.to === '/entretien'}
            className={`app-nav-step ${index <= indexActif ? 'active' : ''}`}
          >
            <span className="app-nav-step-dot">{step.numero}</span>
            <span className="app-nav-step-label">{step.label}</span>
          </NavLink>
        </span>
      ))}

      <span className="app-nav-tools">
        {enEntretien ? (
          <>
            <NavLink to="/entretien/catalogue" className="app-nav-tool" title="Ma grille tarifaire">
              📋
            </NavLink>
            <NavLink to="/bricolage" className="app-nav-tool" title="Retour à SnapDevis Bricolage">
              🧰
            </NavLink>
          </>
        ) : (
          <NavLink to="/entretien" className="app-nav-tool" title="SnapDevis Entretien (nouveau module)">
            🌿
          </NavLink>
        )}
        <NavLink to="/historique" className="app-nav-tool" title="Historique des devis">
          📜
        </NavLink>
        <NavLink to="/dashboard" className="app-nav-tool app-nav-tool-internal" title="Dashboard (interne)">
          📊
        </NavLink>
        <NavLink to="/parametres" className="app-nav-tool" title="Paramètres">
          ⚙
        </NavLink>
      </span>
    </nav>
  )
}

function App() {
  const location = useLocation()
  const enEntretien = location.pathname.startsWith('/entretien')

  return (
    <div className={`app-shell ${enEntretien ? 'theme-entretien' : ''}`}>
      <header className="app-header">
        <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
          <Logo />
        </Link>
        <Stepper />
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/bricolage" element={<UploadPage />} />
          <Route path="/diagnostic" element={<DiagnosticPage />} />
          <Route path="/devis" element={<DevisPage />} />
          <Route path="/parametres" element={<ParametresPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/historique" element={<HistoriquePage />} />

          <Route path="/entretien" element={<EntretienUploadPage />} />
          <Route path="/entretien/diagnostic" element={<EntretienDiagnosticPage />} />
          <Route path="/entretien/devis" element={<EntretienDevisPage />} />
          <Route path="/entretien/validation" element={<EntretienValidationQueuePage />} />
          <Route path="/entretien/validation/:id" element={<EntretienValidationPage />} />
          <Route path="/entretien/devis-client/:id" element={<EntretienDevisClientPage />} />
          <Route path="/entretien/catalogue" element={<CataloguePage />} />
        </Routes>
      </main>

      <footer className="app-footer">
        <span>SnapDevis — prototype de démonstration</span>
      </footer>
    </div>
  )
}

export default App
