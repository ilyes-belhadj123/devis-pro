import { NavLink, Route, Routes } from 'react-router-dom'
import './App.css'
import UploadPage from './pages/UploadPage'
import DiagnosticPage from './pages/DiagnosticPage'
import DevisPage from './pages/DevisPage'

function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-logo">SnapDevis</span>
        <nav className="app-nav">
          <NavLink to="/" end>
            Upload
          </NavLink>
          <NavLink to="/diagnostic">Diagnostic</NavLink>
          <NavLink to="/devis">Devis</NavLink>
        </nav>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/diagnostic" element={<DiagnosticPage />} />
          <Route path="/devis" element={<DevisPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
