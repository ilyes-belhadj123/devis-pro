import { useRef, useState, type DragEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import HeroGraphic from '../components/HeroGraphic'
import './UploadPage.css'

function UploadPage() {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [photoUrl, setPhotoUrl] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleFile = (file: File | undefined) => {
    if (!file) return
    setPhotoUrl(URL.createObjectURL(file))
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
    handleFile(event.dataTransfer.files[0])
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
            disabled={!photoUrl}
            onClick={() => navigate('/diagnostic', { state: { photoUrl } })}
          >
            Analyser la photo →
          </button>
        </div>

        <HeroGraphic />
      </div>
    </section>
  )
}

export default UploadPage
