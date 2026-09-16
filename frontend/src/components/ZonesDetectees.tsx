import './ZonesDetectees.css'

export type ZoneDetecteeApi = {
  photo_index: number
  x: number
  y: number
  largeur: number
  hauteur: number
  label?: string
}

type ZonesDetecteesProps = {
  zones: ZoneDetecteeApi[]
  photoIndex?: number
}

function ZonesDetectees({ zones, photoIndex = 0 }: ZonesDetecteesProps) {
  const zonesVisibles = zones.filter((zone) => zone.photo_index === photoIndex)
  if (zonesVisibles.length === 0) return null

  return (
    <>
      {zonesVisibles.map((zone, index) => (
        <div
          key={index}
          className="zone-detectee"
          style={{
            left: `${zone.x * 100}%`,
            top: `${zone.y * 100}%`,
            width: `${zone.largeur * 100}%`,
            height: `${zone.hauteur * 100}%`,
          }}
        >
          {zone.label && <span className="zone-detectee-label">{zone.label}</span>}
        </div>
      ))}
    </>
  )
}

export default ZonesDetectees
