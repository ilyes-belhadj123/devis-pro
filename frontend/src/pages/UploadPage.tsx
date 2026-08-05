import { useRef, useState, type DragEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyserPhoto } from '../api'
import { mockDiagnostic } from '../mocks/mockData'
import { compresserImage } from '../utils/compresserImage'
import HeroGraphic from '../components/HeroGraphic'
import './UploadPage.css'

function UploadPage() {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [photoFile, setPhotoFile] = useState<File | null>(null)
  const [photoUrl, setPhotoUrl] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isPreparing, setIsPreparing] = useState(false)

  const handleFile = async (file: File | undefined) => {
    if (!file) return
    setIsPreparing(true)
    try {
      const fichierPret = await compresserImage(file)
      setPhotoFile(fichierPret)
      setPhotoUrl(URL.createObjectURL(fichierPret))
    } finally {
      setIsPreparing(false)
    }
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
    handleFile(event.dataTransfer.files[0])
  }

  const analyser = async () => {
    if (!photoFile) return
    setIsAnalyzing(true)
    try {
      const diagnostic = await analyserPhoto(photoFile)
      navigate('/diagnostic', { state: { photoUrl, diagnostic } })
    } catch (err) {
      console.error('Analyse photo indisponible, bascule en mode dégradé :', err)
      navigate('/diagnostic', { state: { photoUrl, diagnostic: { ...mockDiagnostic, degrade: true } } })
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <section className="page page-wide">
      <div className="hero-split">
        <div className="hero-text-col">
          <span className="page-eyebrow">Étape 1 sur 3</span>
          <h1>Prenez une photo de votre projet</h1>
          <p className="page-lead">
            Un mur fissuré, un robinet qui fuit, une étagère à fixer ? Envoyez une photo, SnapDevis identifie tout ce
            qu'il vous faut pour le réparer — matériel, outils, et prix.
          </p>

          <div
            className={`dropzone ${isDragging ? 'dropzone-active' : ''} ${photoUrl ? 'dropzone-filled' : ''}`}
            onDragOver={(e) => {
              e.preventDefault()
              setIsDragging(true)
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                inputRef.current?.click()
              }
            }}
            role="button"
            tabIndex={0}
          >
            {photoUrl ? (
              <img src={photoUrl} alt="Photo du projet" className="dropzone-preview" />
            ) : (
              <div className="dropzone-empty">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path
                    d="M4 8h3l1.5-2h7L17 8h3a1 1 0 011 1v9a1 1 0 01-1 1H4a1 1 0 01-1-1V9a1 1 0 011-1z"
                    stroke="var(--color-accent-copper)"
                    strokeWidth="1.6"
                    strokeLinejoin="round"
                  />
                  <circle cx="12" cy="13" r="3.4" stroke="var(--color-accent-copper)" strokeWidth="1.6" />
                </svg>
                <p>Glissez une photo ici, ou cliquez pour en choisir une</p>
                <span className="page-lead" style={{ fontSize: '0.8125rem' }}>
                  JPG, PNG, HEIC
                </span>
              </div>
            )}
            <input
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png,image/heic"
              hidden
              onChange={(e) => handleFile(e.target.files?.[0])}
            />
          </div>

          <button
            type="button"
            className="btn btn-primary"
            disabled={!photoFile || isAnalyzing || isPreparing}
            onClick={analyser}
          >
            {isPreparing ? 'Préparation de la photo…' : isAnalyzing ? 'Analyse en cours…' : 'Analyser la photo →'}
          </button>
        </div>

        <HeroGraphic />
      </div>
    </section>
  )
}

export default UploadPage
