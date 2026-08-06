import { useRef, useState, type DragEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyserPhoto } from '../api'
import { mockDiagnostic } from '../mocks/mockData'
import { compresserImage } from '../utils/compresserImage'
import './UploadPage.css'

const MAX_PHOTOS = 6

type Photo = { file: File; url: string }

function UploadPage() {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const cameraInputRef = useRef<HTMLInputElement>(null)
  const [photos, setPhotos] = useState<Photo[]>([])
  const [note, setNote] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isPreparing, setIsPreparing] = useState(false)

  const ajouterFichiers = async (fichiers: FileList | null) => {
    if (!fichiers || fichiers.length === 0) return
    const placesRestantes = MAX_PHOTOS - photos.length
    if (placesRestantes <= 0) return
    const aTraiter = Array.from(fichiers).slice(0, placesRestantes)

    setIsPreparing(true)
    try {
      const nouvellesPhotos = await Promise.all(
        aTraiter.map(async (fichier) => {
          const fichierPret = await compresserImage(fichier)
          return { file: fichierPret, url: URL.createObjectURL(fichierPret) }
        }),
      )
      setPhotos((actuelles) => [...actuelles, ...nouvellesPhotos])
    } finally {
      setIsPreparing(false)
    }
  }

  const retirerPhoto = (index: number) => {
    setPhotos((actuelles) => actuelles.filter((_, i) => i !== index))
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
    ajouterFichiers(event.dataTransfer.files)
  }

  const ouvrirSelecteur = () => {
    if (photos.length === 0) inputRef.current?.click()
  }

  const analyser = async () => {
    if (photos.length === 0) return
    setIsAnalyzing(true)
    const photoUrls = photos.map((photo) => photo.url)
    try {
      const diagnostic = await analyserPhoto(photos.map((photo) => photo.file), note)
      navigate('/diagnostic', { state: { photoUrls, diagnostic } })
    } catch (err) {
      console.error('Analyse photo indisponible, bascule en mode dégradé :', err)
      navigate('/diagnostic', { state: { photoUrls, diagnostic: { ...mockDiagnostic, degrade: true } } })
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
        className={`dropzone ${isDragging ? 'dropzone-active' : ''} ${photos.length > 0 ? 'dropzone-filled' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={ouvrirSelecteur}
        onKeyDown={(e) => {
          if ((e.key === 'Enter' || e.key === ' ') && photos.length === 0) {
            e.preventDefault()
            ouvrirSelecteur()
          }
        }}
        role="button"
        tabIndex={0}
      >
        {photos.length > 0 ? (
          <div className="photo-grid">
            {photos.map((photo, index) => (
              <div className="photo-thumb" key={photo.url}>
                <img src={photo.url} alt={`Photo du projet ${index + 1}`} />
                <button
                  type="button"
                  className="photo-thumb-remove"
                  aria-label="Retirer cette photo"
                  onClick={(e) => {
                    e.stopPropagation()
                    retirerPhoto(index)
                  }}
                >
                  ×
                </button>
              </div>
            ))}
            {photos.length < MAX_PHOTOS && (
              <button
                type="button"
                className="photo-thumb photo-thumb-add"
                onClick={(e) => {
                  e.stopPropagation()
                  inputRef.current?.click()
                }}
              >
                <span>+</span>
                Ajouter
              </button>
            )}
          </div>
        ) : (
          <>
            <span className="dropzone-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="#1a1712" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2M12 3v13M7 8l5-5 5 5" />
              </svg>
            </span>
            <div>
              <p className="dropzone-title">Déposez une ou plusieurs photos, ou prenez-en une</p>
              <p className="dropzone-subtitle">
                JPG · PNG · HEIC — plusieurs angles aident l'IA à mieux estimer votre projet
              </p>
            </div>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/heic"
          multiple
          hidden
          onChange={(e) => {
            ajouterFichiers(e.target.files)
            e.target.value = ''
          }}
        />
      </div>

      {photos.length > 0 && (
        <div className="note-field">
          <label htmlFor="note-diagnostic">Une précision à ajouter ? (facultatif)</label>
          <textarea
            id="note-diagnostic"
            placeholder="Ex : la fuite apparaît seulement quand on ouvre l'eau chaude, ça fait 2 semaines que ça coule…"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={2}
          />
        </div>
      )}

      <div className="btn-row">
        <button
          type="button"
          className="btn btn-primary"
          disabled={photos.length === 0 || isAnalyzing || isPreparing}
          onClick={analyser}
        >
          {isPreparing
            ? 'Préparation…'
            : isAnalyzing
              ? 'Analyse en cours…'
              : photos.length > 1
                ? `Analyser les ${photos.length} photos`
                : 'Analyser la photo'}
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
          onChange={(e) => {
            ajouterFichiers(e.target.files)
            e.target.value = ''
          }}
        />
      </div>
    </section>
  )
}

export default UploadPage
