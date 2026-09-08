import { useRef, useState, type DragEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { compresserImage } from '../../utils/compresserImage'
import { evaluerQualitePhoto, type QualitePhoto } from '../../utils/evaluerQualitePhoto'
import { analyserPhotoEntretien } from '../api'
import { mockDiagnosticEntretien } from '../mocks/mockData'

const MAX_PHOTOS = 6

type Photo = { file: File; url: string; qualite?: QualitePhoto }
type Frequence = 'ponctuel' | 'recurrent'

function EntretienUploadPage() {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const cameraInputRef = useRef<HTMLInputElement>(null)
  const [photos, setPhotos] = useState<Photo[]>([])
  const [note, setNote] = useState('')
  const [objetReference, setObjetReference] = useState(false)
  const [longueurReference, setLongueurReference] = useState('')
  const [frequence, setFrequence] = useState<Frequence>('ponctuel')
  const [isDragging, setIsDragging] = useState(false)
  const [isPreparing, setIsPreparing] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

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
          const qualite = await evaluerQualitePhoto(fichier)
          return { file: fichierPret, url: URL.createObjectURL(fichierPret), qualite }
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

  const photosAvecSouci = photos.filter((photo) => photo.qualite?.floue || photo.qualite?.sombre)

  const analyser = async () => {
    if (photos.length === 0) return
    setIsAnalyzing(true)
    const photoUrls = photos.map((photo) => photo.url)

    let noteComplete = note.trim()
    if (objetReference) {
      noteComplete += `${noteComplete ? ' ' : ''}Un objet de taille connue (bouteille, mètre pliant, brouette...) est visible sur au moins une des photos : utilise-le comme repère d'échelle prioritaire pour tes estimations.`
    }
    if (longueurReference.trim()) {
      noteComplete += `${noteComplete ? ' ' : ''}Un côté visible de l'espace mesure environ ${longueurReference.trim()} mètres : utilise cette longueur comme repère d'échelle.`
    }
    noteComplete += `${noteComplete ? ' ' : ''}Fréquence souhaitée par le client : ${
      frequence === 'recurrent' ? "contrat d'entretien récurrent" : 'intervention ponctuelle'
    }.`

    try {
      const diagnostic = await analyserPhotoEntretien(
        photos.map((photo) => photo.file),
        noteComplete,
      )
      navigate('/entretien/diagnostic', { state: { photoUrls, diagnostic } })
    } catch (err) {
      console.error('Analyse photo entretien indisponible, bascule en mode dégradé :', err)
      navigate('/entretien/diagnostic', {
        state: { photoUrls, diagnostic: { ...mockDiagnosticEntretien, degrade: true } },
      })
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <section className="page">
      <span className="page-eyebrow">
        <span className="page-eyebrow-ping" />
        SnapDevis Entretien — diagnostic par IA vision
      </span>

      <h1>
        Photographiez l'espace à entretenir.
        <br />
        <span className="text-gradient">Générez un devis d'entretien.</span>
      </h1>

      <p className="page-lead">
        Pelouse, haie, massif, hall, local, parties communes... intérieur ou extérieur, prenez en photo l'espace à
        entretenir. SnapDevis identifie les tâches nécessaires et estime les surfaces en quelques secondes.
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
                <img src={photo.url} alt={`Photo de l'espace ${index + 1}`} />
                {photo.qualite?.sombre && (
                  <span className="photo-thumb-warning" title="Photo sombre — envisagez de la remplacer">
                    ⚠
                  </span>
                )}
                {!photo.qualite?.sombre && photo.qualite?.floue && (
                  <span className="photo-thumb-warning" title="Photo floue — envisagez de la remplacer">
                    ⚠
                  </span>
                )}
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
                JPG · PNG · HEIC — plusieurs angles aident l'IA à mieux estimer l'espace
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

      {photosAvecSouci.length > 0 && (
        <p className="quality-warning">
          ⚠ {photosAvecSouci.length > 1 ? `${photosAvecSouci.length} photos semblent` : '1 photo semble'} floue(s)
          ou sombre(s) — remplacez-la si possible pour une meilleure estimation.
        </p>
      )}

      {photos.length > 0 && (
        <details className="precisions-panel" open>
          <summary>Précisions (facultatif) — améliore la fiabilité de l'estimation de surface</summary>
          <div className="precisions-content">
            <div className="note-field">
              <label htmlFor="note-diagnostic-entretien">Une précision à ajouter ?</label>
              <textarea
                id="note-diagnostic-entretien"
                placeholder="Ex : la haie fait environ 15 mètres de long, la pelouse est en pente…"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                rows={2}
              />
              <label className="reference-check">
                <input
                  type="checkbox"
                  checked={objetReference}
                  onChange={(e) => setObjetReference(e.target.checked)}
                />
                Un objet de taille connue est visible sur une photo (bouteille, mètre pliant, brouette…)
              </label>
              <label className="reference-check">
                <span>Longueur approx. d'un côté visible :</span>
                <input
                  type="number"
                  min={0}
                  step={0.5}
                  placeholder="en mètres"
                  value={longueurReference}
                  onChange={(e) => setLongueurReference(e.target.value)}
                  style={{
                    width: '90px',
                    padding: '4px 8px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1.5px solid var(--color-border-strong)',
                  }}
                />
              </label>
            </div>

            <div className="note-field">
              <label>Fréquence souhaitée</label>
              <div className="btn-row">
                <button
                  type="button"
                  className={`btn ${frequence === 'ponctuel' ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setFrequence('ponctuel')}
                >
                  Intervention ponctuelle
                </button>
                <button
                  type="button"
                  className={`btn ${frequence === 'recurrent' ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setFrequence('recurrent')}
                >
                  Contrat récurrent
                </button>
              </div>
            </div>
          </div>
        </details>
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

export default EntretienUploadPage
