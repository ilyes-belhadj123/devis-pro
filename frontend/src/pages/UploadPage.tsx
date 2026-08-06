import { useRef, useState, type DragEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyserPhoto } from '../api'
import { mockDiagnostic } from '../mocks/mockData'
import { compresserImage } from '../utils/compresserImage'
import './UploadPage.css'

function UploadPage() {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const cameraInputRef = useRef<HTMLInputElement>(null)
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
    <section className="page">
      <span className="page-eyebrow">
        <span className="page-eyebrow-ping" />
        Diagnostic par IA vision
      </span>

      <h1>
        Un problème.
        <br />
        Une photo.
        <br />
        <span className="text-gradient">Un devis chiffré.</span>
      </h1>

      <p className="page-lead">
        Prenez en photo ce qui doit être réparé, monté ou repeint. SnapDevis identifie ce qu'il vous faut et chiffre
        votre projet en moins de 30 secondes.
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
          <>
            <span className="dropzone-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="#1a1712" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2M12 3v13M7 8l5-5 5 5" />
              </svg>
            </span>
            <div>
              <p className="dropzone-title">Déposez une photo, ou prenez-en une</p>
              <p className="dropzone-subtitle">JPG · PNG · HEIC — 1 photo suffit pour commencer</p>
            </div>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/heic"
          hidden
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>

      <div className="btn-row">
        <button type="button" className="btn btn-primary" disabled={!photoFile || isAnalyzing || isPreparing} onClick={analyser}>
          {isPreparing ? 'Préparation…' : isAnalyzing ? 'Analyse en cours…' : 'Analyser la photo'}
        </button>
        <button type="button" className="btn btn-secondary" onClick={() => cameraInputRef.current?.click()}>
          Ouvrir l'appareil photo
        </button>
        <input
          ref={cameraInputRef}
          type="file"
          accept="image/jpeg,image/png,image/heic"
          capture="environment"
          hidden
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>
    </section>
  )
}

export default UploadPage
