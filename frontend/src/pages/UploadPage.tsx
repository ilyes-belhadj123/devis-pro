import { useNavigate } from 'react-router-dom'

function UploadPage() {
  const navigate = useNavigate()

  return (
    <section className="page page-upload">
      <h1>Prenez une photo de votre projet</h1>
      <p>Un mur fissuré, un robinet qui fuit, une étagère à fixer ? Envoyez une photo pour commencer.</p>

      <div className="dropzone">
        <p>Glissez une photo ici, ou cliquez pour choisir un fichier (jpg, png, heic)</p>
      </div>

      <button type="button" onClick={() => navigate('/diagnostic')}>
        Simuler l'envoi de la photo
      </button>
    </section>
  )
}

export default UploadPage
