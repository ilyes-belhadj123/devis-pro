import { NavLink, Route, Routes } from 'react-router-dom'
import './App.css'
import Logo from './components/Logo'
import UploadPage from './pages/UploadPage'
import DiagnosticPage from './pages/DiagnosticPage'
import DevisPage from './pages/DevisPage'
import ParametresPage from './pages/ParametresPage'
import DashboardPage from './pages/DashboardPage'

const steps = [
  { to: '/', label: '1. Photo' },
  { to: '/diagnostic', label: '2. Diagnostic' },
  { to: '/devis', label: '3. Devis' },
]

function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <Logo />
        <nav className="app-nav">
          {steps.map((step) => (
            <NavLink key={step.to} to={step.to} end={step.to === '/'}>
              {step.label}
            </NavLink>
          ))}
          <NavLink to="/dashboard" className="app-nav-tool" title="Dashboard (interne)">
            📊
          </NavLink>
          <NavLink to="/parametres" className="app-nav-tool" title="Paramètres">
            ⚙
          </NavLink>
        </nav>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/diagnostic" element={<DiagnosticPage />} />
          <Route path="/devis" element={<DevisPage />} />
          <Route path="/parametres" element={<ParametresPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
        </Routes>
      </main>

      <footer className="app-footer">
        <span>SnapDevis — prototype de démonstration</span>
      </footer>
    </div>
  )
}

export default App
