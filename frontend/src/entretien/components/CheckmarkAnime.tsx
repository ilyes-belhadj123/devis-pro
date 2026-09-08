import './CheckmarkAnime.css'

function CheckmarkAnime() {
  return (
    <svg width="72" height="72" viewBox="0 0 72 72" fill="none" className="checkmark-anime">
      <circle cx="36" cy="36" r="33" stroke="var(--color-state-success)" strokeWidth="3" className="checkmark-anime-circle" />
      <path
        d="M22 37l10 10 18-20"
        stroke="var(--color-state-success)"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="checkmark-anime-check"
      />
    </svg>
  )
}

export default CheckmarkAnime
