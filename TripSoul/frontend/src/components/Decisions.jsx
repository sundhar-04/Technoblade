import { simulateDisruption } from '../api/client'

export default function Decisions({ decisions, itinerary, onSimulate }) {
  const handleSimulate = async (type) => {
    try {
      const data = await simulateDisruption({
        disruption_type: type,
        severity: 'high',
        city: itinerary?.city || 'nyc',
      })
      onSimulate(data)
    } catch (e) {
      console.error('Simulation error:', e)
    }
  }

  return (
    <div className="animate-in">
      <div className="section-label">Decision Intelligence</div>
      <h2 className="section-title" style={{ marginBottom: '0.5rem' }}>
        Why these choices were made
      </h2>
      <p style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: '1.5rem' }}>
        Every decision is explained. The system adapts without your request.
      </p>

      {/* Simulation controls */}
      <div className="card" style={{ marginBottom: '1.5rem', borderColor: 'var(--gold-border)' }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--gold)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '0.75rem' }}>
          Simulate Disruption
        </div>
        <p style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: '1rem' }}>
          Trigger a simulated disruption to see how the system automatically adapts.
          {!itinerary && ' Generate an itinerary first for full adaptation demo.'}
        </p>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button className="btn btn-danger" onClick={() => handleSimulate('weather')}>
            🌧️ Simulate Rain
          </button>
          <button className="btn btn-danger" onClick={() => handleSimulate('closure')}>
            🚫 Simulate Closure
          </button>
          <button className="btn btn-danger" onClick={() => handleSimulate('delay')}>
            🕐 Simulate Delay
          </button>
        </div>
      </div>

      {/* Decision log */}
      {decisions.length > 0 ? (
        <div className="card">
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--gold)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '1rem' }}>
            Decision Log ({decisions.length})
          </div>
          {decisions.map((d, i) => (
            <div key={i} className="decision-entry animate-in" style={{ animationDelay: `${i * 0.05}s` }}>
              <div className={`decision-icon ${d.type}`}>
                {d.type === 'auto' ? '⚡' : d.type === 'warning' ? '⚠️' : '💡'}
              </div>
              <div className="decision-content">
                <div className="decision-title">{d.title}</div>
                <div className="decision-reason">{d.reason}</div>
                {d.changes?.length > 0 && (
                  <div style={{ marginTop: 6 }}>
                    {d.changes.map((c, ci) => (
                      <div key={ci} style={{ fontSize: 11, color: 'var(--emerald)', padding: '2px 0' }}>
                        → {c}
                      </div>
                    ))}
                  </div>
                )}
                <div className="decision-time">{d.time}</div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">⚡</div>
          <div className="empty-state-title">No decisions yet</div>
          <p>Generate an itinerary or simulate a disruption to see the decision intelligence at work.</p>
        </div>
      )}
    </div>
  )
}
