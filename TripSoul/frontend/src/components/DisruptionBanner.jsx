export default function DisruptionBanner({ disruption }) {
  if (!disruption?.disruption) return null

  const d = disruption.disruption
  const icons = { weather: '🌧️', closure: '🚫', delay: '🕐', congestion: '🚗' }

  return (
    <div className="disruption-banner animate-in">
      <div className="disruption-icon">{icons[d.type] || '⚠️'}</div>
      <div style={{ flex: 1 }}>
        <div className="disruption-text">
          <strong>Auto-adapted:</strong> {d.description}
        </div>
        <div className="disruption-meta">
          {disruption.reasoning}
        </div>
        {disruption.changes_made?.length > 0 && (
          <div style={{ marginTop: 6, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {disruption.changes_made.map((c, i) => (
              <span key={i} className="tag tag-emerald" style={{ fontSize: 10 }}>✓ {c}</span>
            ))}
          </div>
        )}
      </div>
      <span className="tag tag-red" style={{ flexShrink: 0 }}>
        {d.severity}
      </span>
    </div>
  )
}
