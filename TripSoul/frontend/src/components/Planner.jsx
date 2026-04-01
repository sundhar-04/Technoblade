import { useState } from 'react'
import { generateItinerary } from '../api/client'

const CITIES = [
  { key: 'nyc', label: 'New York City', icon: '🗽' },
  { key: 'tokyo', label: 'Tokyo', icon: '⛩️' },
  { key: 'paris', label: 'Paris', icon: '🗼' },
]

const INTERESTS = ['culture', 'food', 'adventure', 'nightlife', 'nature', 'shopping', 'history']
const PACES = ['packed', 'balanced', 'relaxed']
const MOODS = ['relaxed', 'energetic', 'romantic', 'family']
const PARTY_SIZES = ['solo', 'couple', 'family', 'group']
const DIETARY = ['any', 'vegetarian', 'vegan', 'halal']

export default function Planner({ onGenerated, itinerary, weather }) {
  const [step, setStep] = useState(1)
  const [city, setCity] = useState('nyc')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [budget, setBudget] = useState(500)
  const [partySize, setPartySize] = useState('couple')
  const [mood, setMood] = useState('relaxed')
  const [dietary, setDietary] = useState('any')
  const [interests, setInterests] = useState(['culture', 'food'])
  const [pace, setPace] = useState('balanced')
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const toggleInterest = (i) => {
    setInterests(prev =>
      prev.includes(i) ? prev.filter(x => x !== i) : [...prev, i]
    )
  }

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)
    
    // Calculate simple duration from dates if selected, else default 3
    let durationSec = 3
    if (startDate && endDate) {
        const diff = new Date(endDate) - new Date(startDate)
        durationSec = Math.max(1, Math.ceil(diff / (1000 * 60 * 60 * 24)))
    }

    try {
      const data = await generateItinerary({ 
          city, budget, duration: durationSec, 
          start_date: startDate, end_date: endDate,
          party_size: partySize, mood, dietary_preference: dietary,
          interests, pace 
      })
      onGenerated(data)
      setStep(5) // Results view
    } catch (e) {
      setError(e.message)
    }
    setLoading(false)
  }
  
  const resetPlanner = () => {
      onGenerated(null)
      setStep(1)
  }

  const renderWizardStep = () => {
      if (step === 1) {
          return (
              <div className="animate-in">
                  <div className="input-group">
                      <label className="input-label">Where are we going?</label>
                      <select className="select" value={city} onChange={e => setCity(e.target.value)}>
                        {CITIES.map(c => (
                          <option key={c.key} value={c.key}>{c.icon} {c.label}</option>
                        ))}
                      </select>
                  </div>
                  <div style={{ display: 'flex', gap: 16 }}>
                      <div className="input-group" style={{ flex: 1 }}>
                          <label className="input-label">Start Date</label>
                          <input className="input" type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
                      </div>
                      <div className="input-group" style={{ flex: 1 }}>
                          <label className="input-label">End Date</label>
                          <input className="input" type="date" value={endDate} onChange={e => setEndDate(e.target.value)} />
                      </div>
                  </div>
              </div>
          )
      }
      
      if (step === 2) {
          return (
              <div className="animate-in">
                  <div className="input-group">
                      <label className="input-label">Who is travelling?</label>
                      <div className="interest-pills">
                        {PARTY_SIZES.map(p => (
                          <button key={p} className={`interest-pill ${partySize === p ? 'active' : ''}`} onClick={() => setPartySize(p)}>
                            {p.charAt(0).toUpperCase() + p.slice(1)}
                          </button>
                        ))}
                      </div>
                  </div>
                  <div className="input-group" style={{ marginTop: '1.5rem' }}>
                      <label className="input-label">Total Trip Budget (USD)</label>
                      <input className="input" type="number" min={50} max={20000} value={budget} onChange={e => setBudget(Number(e.target.value))} />
                  </div>
              </div>
          )
      }
      
      if (step === 3) {
          return (
              <div className="animate-in">
                  <div className="input-group">
                      <label className="input-label">What's the mood?</label>
                      <div className="interest-pills">
                        {MOODS.map(m => (
                          <button key={m} className={`interest-pill ${mood === m ? 'active' : ''}`} onClick={() => setMood(m)}>
                            {m.charAt(0).toUpperCase() + m.slice(1)}
                          </button>
                        ))}
                      </div>
                  </div>
                  <div className="input-group" style={{ marginTop: '1.5rem' }}>
                      <label className="input-label">Dietary Preferences</label>
                      <div className="interest-pills">
                        {DIETARY.map(d => (
                          <button key={d} className={`interest-pill ${dietary === d ? 'active' : ''}`} onClick={() => setDietary(d)}>
                            {d.charAt(0).toUpperCase() + d.slice(1)}
                          </button>
                        ))}
                      </div>
                  </div>
              </div>
          )
      }
      
      if (step === 4) {
          return (
              <div className="animate-in">
                  <div className="input-group">
                      <label className="input-label">Travel Pace</label>
                      <div className="interest-pills">
                        {PACES.map(p => (
                          <button key={p} className={`interest-pill ${pace === p ? 'active' : ''}`} onClick={() => setPace(p)}>
                            {p.charAt(0).toUpperCase() + p.slice(1)}
                          </button>
                        ))}
                      </div>
                  </div>
                  <div className="input-group" style={{ marginTop: '1.5rem' }}>
                      <label className="input-label">Key Interests</label>
                      <div className="interest-pills" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr' }}>
                        {INTERESTS.map(i => (
                          <button key={i} className={`interest-pill ${interests.includes(i) ? 'active' : ''}`} onClick={() => toggleInterest(i)} style={{ justifyContent: 'center' }}>
                            {i.charAt(0).toUpperCase() + i.slice(1)}
                          </button>
                        ))}
                      </div>
                  </div>
              </div>
          )
      }
      return null
  }

  return (
    <div className="animate-in">
      {!itinerary ? (
          <>
              <div className="section-label">AI Planner Wizard</div>
              <h1 className="section-title" style={{ marginBottom: '0.5rem' }}>
                  Design your journey
              </h1>
              
              <div style={{ display: 'flex', gap: 8, marginBottom: '2rem' }}>
                  {[1, 2, 3, 4].map(s => (
                      <div key={s} style={{ height: 4, flex: 1, borderRadius: 2, background: step >= s ? 'var(--gold)' : 'var(--surface)' }} />
                  ))}
              </div>

              <div className="planner-form" style={{ minHeight: 300, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                  {renderWizardStep()}
              </div>

              <div className="planner-actions" style={{ marginTop: '2rem', display: 'flex', justifyContent: 'space-between' }}>
                  <button className="btn btn-secondary" disabled={step === 1 || loading} onClick={() => setStep(s => s - 1)}>
                      Back
                  </button>
                  
                  {step < 4 ? (
                      <button className="btn btn-primary" onClick={() => setStep(s => s + 1)}>
                          Continue
                      </button>
                  ) : (
                      <button className="btn btn-primary" onClick={handleGenerate} disabled={loading}>
                        {loading ? (
                          <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Computing...</>
                        ) : (
                          <>🧠 Generate Trip</>
                        )}
                      </button>
                  )}
              </div>
          </>
      ) : (
          <div className="animate-in">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                  <div>
                      <span className="section-label" style={{ marginBottom: 4 }}>
                        Generated Itinerary — {itinerary.city.toUpperCase()}
                      </span>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                          <span className={`confidence ${itinerary.overall_confidence > 0.8 ? 'confidence-high' : itinerary.overall_confidence > 0.6 ? 'confidence-med' : 'confidence-low'}`}>
                              <span className="confidence-bar">
                                <span className="confidence-fill" style={{ width: `${itinerary.overall_confidence * 100}%` }} />
                              </span>
                              {(itinerary.overall_confidence * 100).toFixed(0)}%
                          </span>
                          {weather && (
                            <span className="tag tag-gold">
                              {weather.description} · {weather.temp_c}°C
                            </span>
                          )}
                      </div>
                  </div>
                  <button className="btn btn-secondary" onClick={resetPlanner} style={{ padding: '6px 12px', fontSize: 13 }}>
                      Re-plan
                  </button>
              </div>

              <div className="card" style={{ marginBottom: '1rem', padding: '1rem 1.25rem' }}>
                <div style={{ fontSize: 13, color: 'var(--text-dim)', lineHeight: 1.6 }}>
                  💡 {itinerary.reasoning}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 10, marginBottom: '1.5rem' }}>
                <div className="tradeoff-card">
                  <div className="tradeoff-value">{itinerary.duration}d</div>
                  <div className="tradeoff-label">Duration</div>
                </div>
                <div className="tradeoff-card">
                  <div className="tradeoff-value">${itinerary.budget_used?.toFixed(0)}</div>
                  <div className="tradeoff-label">of ${itinerary.budget} budget</div>
                </div>
                <div className="tradeoff-card">
                  <div className="tradeoff-value">{itinerary.days?.reduce((a, d) => a + d.slots.length, 0)}</div>
                  <div className="tradeoff-label">Activities</div>
                </div>
                <div className="tradeoff-card">
                  <div className="tradeoff-value">{itinerary.days?.reduce((a, d) => a + d.total_travel_minutes, 0)}m</div>
                  <div className="tradeoff-label">Travel time</div>
                </div>
              </div>

              {itinerary.days?.map(day => (
                <div key={day.day} className="card animate-in" style={{ marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <span style={{ fontFamily: 'var(--font-display)', fontSize: '1.1rem', fontWeight: 600 }}>
                      {day.date_label}
                    </span>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <span className="tag tag-gold">${day.total_cost.toFixed(0)}</span>
                      <span className="tag tag-emerald">{day.slots.length} activities</span>
                    </div>
                  </div>

                  {day.slots.map((slot, i) => (
                    <div key={i} style={{ display: 'flex', gap: 12, padding: '0.75rem 0', borderBottom: i < day.slots.length - 1 ? '1px solid var(--border)' : 'none' }}>
                      <div style={{ width: 52, flexShrink: 0, textAlign: 'right' }}>
                        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--gold)' }}>{slot.start_time}</div>
                        <div style={{ fontSize: 10, color: 'var(--text-faint)' }}>{slot.end_time}</div>
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 500, marginBottom: 2 }}>
                            {slot.activity.name}
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 4 }}>{slot.activity.description}</div>
                        
                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center', marginTop: 6, marginBottom: 6 }}>
                          <span className="tag tag-gold" style={{ fontSize: 10 }}>{slot.activity.category}</span>
                          {slot.activity.cost > 0 && <span className="tag tag-emerald" style={{ fontSize: 10 }}>${slot.activity.cost}</span>}
                          
                          {/* Availability Badge */}
                          {slot.availability_status === 'Available' && (
                              <span style={{ fontSize: 10, color: '#4CC9A0', background: 'rgba(76, 201, 160, 0.1)', padding: '2px 6px', borderRadius: 4 }}>✅ Confirmed</span>
                          )}
                          {slot.availability_status === 'Limited' && (
                              <span style={{ fontSize: 10, color: '#E8A838', background: 'rgba(232, 168, 56, 0.1)', padding: '2px 6px', borderRadius: 4 }}>⚠️ Limited Supply</span>
                          )}
                          
                          {slot.surge_multiplier > 1.0 && (
                              <span style={{ fontSize: 10, color: '#FF6B6B', border: '1px solid #FF6B6B', padding: '1px 4px', borderRadius: 4 }}>↑ Surge Pricing (x{slot.surge_multiplier})</span>
                          )}
                          
                          <span className={`confidence ${slot.activity.confidence_score > 0.8 ? 'confidence-high' : 'confidence-med'}`}>
                            <span className="confidence-bar" style={{ width: 30 }}>
                              <span className="confidence-fill" style={{ width: `${slot.activity.confidence_score * 100}%` }} />
                            </span>
                            {(slot.activity.confidence_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        {slot.activity.reason && (
                          <div style={{ fontSize: 11, color: 'var(--text-faint)', marginTop: 4, fontStyle: 'italic' }}>
                            {slot.activity.reason}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ))}
          </div>
      )}

      {error && (
        <div className="disruption-banner" style={{ marginTop: '1rem' }}>
          <div className="disruption-icon">⚠️</div>
          <div>
            <div className="disruption-text">Configuration Error</div>
            <div className="disruption-meta">{error}</div>
          </div>
        </div>
      )}
    </div>
  )
}
