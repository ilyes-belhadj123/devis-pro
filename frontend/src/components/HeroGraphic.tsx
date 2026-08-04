import './HeroGraphic.css'

function HeroGraphic() {
  return (
    <div className="hero-graphic">
      <svg viewBox="0 0 320 320" className="hero-graphic-svg" aria-hidden="true">
        <circle cx="160" cy="160" r="130" fill="var(--color-accent-copper-soft)" />
        <circle
          cx="160"
          cy="160"
          r="104"
          fill="none"
          stroke="var(--color-accent-tech)"
          strokeWidth="2"
          strokeDasharray="6 10"
          className="hero-graphic-ring"
        />
        <g transform="translate(112, 118)">
          <rect x="0" y="14" width="96" height="66" rx="10" fill="#fff" stroke="var(--color-text-primary)" strokeWidth="3" />
          <rect x="30" y="0" width="36" height="18" rx="4" fill="#fff" stroke="var(--color-text-primary)" strokeWidth="3" />
          <circle cx="48" cy="48" r="22" fill="var(--color-bg-surface-sunken)" stroke="var(--color-text-primary)" strokeWidth="3" />
          <circle cx="48" cy="48" r="9" fill="var(--color-accent-tech)" />
        </g>
        <g transform="translate(48, 60)" className="hero-graphic-float-1">
          <rect x="0" y="0" width="34" height="34" rx="8" fill="var(--color-accent-copper)" />
          <path d="M8 17 L26 17 M17 8 L17 26" stroke="#fff" strokeWidth="3" strokeLinecap="round" />
        </g>
        <g transform="translate(228, 76)" className="hero-graphic-float-2">
          <circle cx="18" cy="18" r="18" fill="var(--color-accent-tech)" />
          <path d="M10 18 L16 24 L27 11" stroke="#fff" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        </g>
        <g transform="translate(220, 210)" className="hero-graphic-float-3">
          <rect x="0" y="0" width="46" height="30" rx="6" fill="#fff" stroke="var(--color-accent-copper)" strokeWidth="3" />
          <text x="23" y="21" textAnchor="middle" fontSize="14" fontFamily="var(--font-body)" fontWeight="700" fill="var(--color-accent-copper)">
            €
          </text>
        </g>
      </svg>
    </div>
  )
}

export default HeroGraphic
