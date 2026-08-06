import { useRef, useState, type DragEvent, type MouseEvent as ReactMouseEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyserPhoto } from '../api'
import { mockDiagnostic } from '../mocks/mockData'
import { compresserImage } from '../utils/compresserImage'
import { eclaircirImage } from '../utils/eclaircirImage'
import { evaluerQualitePhoto, type QualitePhoto } from '../utils/evaluerQualitePhoto'
import { recadrerZoom } from '../utils/recadrerZoom'
import { useDicteeVocale } from '../utils/useDicteeVocale'
import './UploadPage.css'

const MAX_PHOTOS = 6

type Point = { x: number; y: number }
type Photo = { file: File; url: string; points: Point[]; qualite?: QualitePhoto }

function UploadPage() {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const cameraInputRef = useRef<HTMLInputElement>(null)
  const [photos, setPhotos] = useState<Photo[]>([])
  const [note, setNote] = useState('')
  const [objetReference, setObjetReference] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isPreparing, setIsPreparing] = useState(false)
  const [eclaircissementEnCours, setEclaircissementEnCours] = useState<number | null>(null)

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
          return { file: fichierPret, url: URL.createObjectURL(fichierPret), points: [], qualite }
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

  const marquerPoint = (index: number, event: ReactMouseEvent<HTMLImageElement>) => {
    const rect = event.currentTarget.getBoundingClientRect()
    const point = {
      x: (event.clientX - rect.left) / rect.width,
      y: (event.clientY - rect.top) / rect.height,
    }
    setPhotos((actuelles) =>
      actuelles.map((photo, i) => (i === index ? { ...photo, points: [...photo.points, point] } : photo)),
    )
  }

  const retirerPoint = (index: number, pointIndex: number) => {
    setPhotos((actuelles) =>
      actuelles.map((photo, i) =>
        i === index ? { ...photo, points: photo.points.filter((_, pi) => pi !== pointIndex) } : photo,
      ),
    )
  }

  const eclaircirPhoto = async (index: number) => {
    const photo = photos[index]
    if (!photo) return
    setEclaircissementEnCours(index)
    try {
      const fichierEclairci = await eclaircirImage(photo.file)
      const qualite = await evaluerQualitePhoto(fichierEclairci)
      const url = URL.createObjectURL(fichierEclairci)
      setPhotos((actuelles) =>
        actuelles.map((p, i) => (i === index ? { ...p, file: fichierEclairci, url, qualite } : p)),
      )
    } finally {
      setEclaircissementEnCours(null)
    }
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

  const { ecoute, disponible: dicteeDisponible, basculer: basculerDictee } = useDicteeVocale((texte) => {
    setNote((actuelle) => (actuelle.trim() ? `${actuelle.trim()} ${texte}` : texte))
  })

  const analyser = async () => {
    if (photos.length === 0) return
    setIsAnalyzing(true)
    const photoUrls = photos.map((photo) => photo.url)
    const points = photos.flatMap((photo, index) =>
      photo.points.map((point) => ({ index, x: point.x, y: point.y })),
    )
    const noteAvecRepere = objetReference
      ? `${note.trim()}${note.trim() ? ' ' : ''}Un objet de taille connue (pièce de monnaie, carte bancaire, règle...) est visible sur au moins une des photos : utilise-le comme repère d'échelle prioritaire pour tes estimations de dimensions.`
      : note
    try {
      const zooms = (
        await Promise.all(
          photos.flatMap((photo) => photo.points.map((point) => recadrerZoom(photo.file, point))),
        )
      ).filter((fichier): fichier is File => fichier !== null)

      const diagnostic = await analyserPhoto(
        [...photos.map((photo) => photo.file), ...zooms],
        noteAvecRepere,
        points,
      )
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
                <img
                  src={photo.url}
                  alt={`Photo du projet ${index + 1}`}
                  onClick={(e) => {
                    e.stopPropagation()
                    marquerPoint(index, e)
                  }}
                />
                {photo.qualite?.sombre && (
                  <button
                    type="button"
                    className="photo-thumb-warning photo-thumb-warning-fix"
                    disabled={eclaircissementEnCours === index}
                    title={
                      photo.qualite?.floue
                        ? 'Photo sombre (et un peu floue) — cliquez pour éclaircir automatiquement'
                        : 'Photo sombre — cliquez pour éclaircir automatiquement'
                    }
                    onClick={(e) => {
                      e.stopPropagation()
                      eclaircirPhoto(index)
                    }}
                  >
                    {eclaircissementEnCours === index ? '…' : '⚠'}
                  </button>
                )}
                {!photo.qualite?.sombre && photo.qualite?.floue && (
                  <span className="photo-thumb-warning" title="Photo floue — envisagez de la remplacer">
                    ⚠
                  </span>
                )}
                {photo.points.map((point, pointIndex) => (
                  <button
                    key={pointIndex}
                    type="button"
                    className="photo-thumb-point"
                    style={{ left: `${point.x * 100}%`, top: `${point.y * 100}%` }}
                    aria-label="Retirer le repère"
                    title="Retirer le repère"
                    onClick={(e) => {
                      e.stopPropagation()
                      retirerPoint(index, pointIndex)
                    }}
                  />
                ))}
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
        <p className="point-hint">
          Touchez une photo pour indiquer un ou plusieurs emplacements précis du problème (facultatif) — un zoom
          automatique de chaque zone sera envoyé en plus à l'IA
        </p>
      )}

      {photosAvecSouci.length > 0 && (
        <p className="quality-warning">
          ⚠ {photosAvecSouci.length > 1 ? `${photosAvecSouci.length} photos semblent` : '1 photo semble'} floue(s) ou
          sombre(s) — cliquez sur l'icône d'une photo sombre pour l'éclaircir automatiquement, ou remplacez une
          photo floue.
        </p>
      )}

      {photos.length > 0 && (
        <div className="note-field">
          <div className="note-field-header">
            <label htmlFor="note-diagnostic">Une précision à ajouter ? (facultatif)</label>
            {dicteeDisponible && (
              <button
                type="button"
                className={`mic-button ${ecoute ? 'active' : ''}`}
                onClick={basculerDictee}
                aria-label={ecoute ? 'Arrêter la dictée' : 'Dicter la précision'}
                title={ecoute ? 'Arrêter la dictée' : 'Dicter la précision'}
              >
                🎤
              </button>
            )}
          </div>
          <textarea
            id="note-diagnostic"
            placeholder="Ex : la fuite apparaît seulement quand on ouvre l'eau chaude, ça fait 2 semaines que ça coule…"
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
            Un objet de taille connue est visible sur une photo (pièce de monnaie, carte, règle…)
          </label>
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
