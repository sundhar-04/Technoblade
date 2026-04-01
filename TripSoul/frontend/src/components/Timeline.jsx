import { useState } from 'react'

export default function Timeline({ itinerary }) {
  const [activeDay, setActiveDay] = useState(0)

  if (!itinerary?.days?.length) {
    return (
      <div className="animate-in">
        <div className="section-label">Timeline</div>
        <h2 className="section-title" style={{ marginBottom: '1rem' }}>Day-by-day schedule</h2>
        <div className="empty-state">
          <div className="empty-state-icon">📅</div>
          <div className="empty-state-title">No itinerary yet</div>
          <p>Generate an itinerary first to see the timeline view.</p>
        </div>
      </div>
    )
  }

  const day = itinerary.days[activeDay]
  const categoryColors = {
    culture: '#E8A838',
    food: '#4CC9A0',
    adventure: '#5B8DEF',
    nightlife: '#A78BFA',
    nature: '#4CC9A0',
    shopping: '#F59E0B',
    history: '#E05C5C',
  }

  return (
    <div className="animate-in">
      <div className="section-label">Timeline</div>
      <h2 className="section-title" style={{ marginBottom: '1rem' }}>
        Day-by-day schedule
      </h2>

      <div className="day-tabs">
        {itinerary.days.map((d, i) => (
          <button
            key={i}
            className={`day-tab ${i === activeDay ? 'active' : ''}`}
            onClick={() => setActiveDay(i)}
          >
            Day {d.day} · ${d.total_cost.toFixed(0)}
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: '1.5rem' }}>
        <div className="tradeoff-card">
          <div className="tradeoff-value">{day.slots.length}</div>
          <div className="tradeoff-label">Activities</div>
        </div>
        <div className="tradeoff-card">
          <div className="tradeoff-value">${day.total_cost.toFixed(0)}</div>
          <div className="tradeoff-label">Day cost</div>
        </div>
        <div className="tradeoff-card">
          <div className="tradeoff-value">{day.total_travel_minutes}m</div>
          <div className="tradeoff-label">Travel time</div>
        </div>
      </div>

      <div className="timeline">
        {day.slots.map((slot, i) => (
          <div key={i}>
            {slot.travel_time_minutes > 0 && (
              <div className="timeline-item" style={{ paddingBottom: '0.5rem' }}>
                <div className="timeline-dot travel" />
                <div className="timeline-travel">
                  🚶 {slot.travel_time_minutes} min · {slot.travel_distance_km} km
                </div>
              </div>
            )}
            <div className="timeline-item">
              <div
                className="timeline-dot"
                style={{ background: categoryColors[slot.activity.category] || 'var(--gold)' }}
              />
              <div className="timeline-time">{slot.start_time} — {slot.end_time}</div>
              <div className="timeline-activity">{slot.activity.name}</div>
              <div className="timeline-desc">{slot.activity.description}</div>
              <div style={{ display: 'flex', gap: 6, marginTop: 6, flexWrap: 'wrap' }}>
                <span className="tag" style={{
                  background: `${categoryColors[slot.activity.category] || 'var(--gold)'}20`,
                  color: categoryColors[slot.activity.category] || 'var(--gold)',
                  border: `1px solid ${categoryColors[slot.activity.category] || 'var(--gold)'}40`,
                }}>
                  {slot.activity.category}
                </span>
                {slot.activity.cost > 0 && (
                  <span className="tag tag-gold">${slot.activity.cost}</span>
                )}
                {slot.activity.cost === 0 && (
                  <span className="tag tag-emerald">Free</span>
                )}
                <span className={`confidence ${slot.activity.confidence_score > 0.8 ? 'confidence-high' : 'confidence-med'}`}>
                  <span className="confidence-bar" style={{ width: 30 }}>
                    <span className="confidence-fill" style={{ width: `${slot.activity.confidence_score * 100}%` }} />
                  </span>
                  {(slot.activity.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
              {slot.activity.reason && (
                <div style={{ fontSize: 11, color: 'var(--text-faint)', marginTop: 6, fontStyle: 'italic' }}>
                  {slot.activity.reason}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
