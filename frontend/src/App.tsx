import { NavLink, Route, Routes, useLocation } from 'react-router-dom'
import './App.css'
import Logo from './components/Logo'
import UploadPage from './pages/UploadPage'
import DiagnosticPage from './pages/DiagnosticPage'
import DevisPage from './pages/DevisPage'
import ParametresPage from './pages/ParametresPage'
import DashboardPage from './pages/DashboardPage'
import HistoriquePage from './pages/HistoriquePage'

const steps = [
  { to: '/', numero: 1, label: 'Envoi' },
  { to: '/diagnostic', numero: 2, label: 'Diagnostic' },
  { to: '/devis', numero: 3, label: 'Devis' },
]

function Stepper() {
  const location = useLocation()
  const indexActif = steps.findIndex((step) => step.to === location.pathname)

  return (
    <nav className="app-nav">
      {steps.map((step, index) => (
        <span key={step.to} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          {index > 0 && <span className="app-nav-line" />}
          <NavLink to={step.to} end={step.to === '/'} className={`app-nav-step ${index <= indexActif ? 'active' : ''}`}>
            <span className="app-nav-step-dot">{step.numero}</span>
            <span className="app-nav-step-label">{step.label}</span>
          </NavLink>
        </span>
      ))}

      <span className="app-nav-tools">
        <NavLink to="/historique" className="app-nav-tool" title="Historique des devis">
          📜
        </NavLink>
        <NavLink to="/dashboard" className="app-nav-tool" title="Dashboard (interne)">
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
  return (
    <div className="app-shell">
      <header className="app-header">
        <Logo />
        <Stepper />
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/diagnostic" element={<DiagnosticPage />} />
          <Route path="/devis" element={<DevisPage />} />
          <Route path="/parametres" element={<ParametresPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/historique" element={<HistoriquePage />} />
        </Routes>
      </main>

      <footer className="app-footer">
        <span>SnapDevis — prototype de démonstration</span>
      </footer>
    </div>
  )
}

export default App
