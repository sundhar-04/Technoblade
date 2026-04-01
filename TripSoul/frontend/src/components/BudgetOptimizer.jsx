import { useState } from 'react'
import { optimizeBudget } from '../api/client'

export default function BudgetOptimizer({ itinerary, onOptimized }) {
  const [budget, setBudget] = useState(itinerary?.budget || 500)
  const [weightBudget, setWeightBudget] = useState(0.5)
  const [weightEnjoyment, setWeightEnjoyment] = useState(0.5)
  const [weightIntensity, setWeightIntensity] = useState(0.5)
  const [tradeOffs, setTradeOffs] = useState([])
  const [paretoNotes, setParetoNotes] = useState('')
  const [loading, setLoading] = useState(false)

  const handleOptimize = async () => {
    setLoading(true)
    try {
      const data = await optimizeBudget({
        city: itinerary?.city || 'nyc',
        budget,
        duration: itinerary?.duration || 3,
        interests: ['culture', 'food'],
        weight_budget: weightBudget,
        weight_enjoyment: weightEnjoyment,
        weight_intensity: weightIntensity,
      })
      setTradeOffs(data.trade_offs || [])
      setParetoNotes(data.pareto_notes || '')
      onOptimized(data)
    } catch (e) {
      console.error('Optimization error:', e)
    }
    setLoading(false)
  }

  return (
    <div className="animate-in">
      <div className="section-label">Budget Optimizer</div>
      <h2 className="section-title" style={{ marginBottom: '1.5rem' }}>
        Optimize your trip
      </h2>

      <div className="optimizer-layout">
        <div className="optimizer-controls">
          <div className="card">
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--gold)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '1rem' }}>
              Control Panel
            </div>

            <div className="input-group" style={{ marginBottom: '1.25rem' }}>
              <label className="input-label">Total Budget (USD)</label>
              <input
                className="input" type="number" min={50} max={10000}
                value={budget} onChange={e => setBudget(Number(e.target.value))}
              />
            </div>

            <div className="slider-group" style={{ marginBottom: '1.25rem' }}>
              <div className="slider-header">
                <span className="slider-label">💰 Budget Priority</span>
                <span className="slider-value">{(weightBudget * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range" min={0} max={1} step={0.05}
                value={weightBudget}
                onChange={e => { setWeightBudget(parseFloat(e.target.value)); handleOptimize() }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-faint)' }}>
                <span>Spend freely</span><span>Save money</span>
              </div>
            </div>

            <div className="slider-group" style={{ marginBottom: '1.25rem' }}>
              <div className="slider-header">
                <span className="slider-label">🎉 Enjoyment Priority</span>
                <span className="slider-value">{(weightEnjoyment * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range" min={0} max={1} step={0.05}
                value={weightEnjoyment}
                onChange={e => { setWeightEnjoyment(parseFloat(e.target.value)); handleOptimize() }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-faint)' }}>
                <span>Any activity</span><span>Best rated only</span>
              </div>
            </div>

            <div className="slider-group" style={{ marginBottom: '1.25rem' }}>
              <div className="slider-header">
                <span className="slider-label">⚡ Travel Intensity</span>
                <span className="slider-value">{(weightIntensity * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range" min={0} max={1} step={0.05}
                value={weightIntensity}
                onChange={e => { setWeightIntensity(parseFloat(e.target.value)); handleOptimize() }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-faint)' }}>
                <span>Relaxed</span><span>Packed</span>
              </div>
            </div>

            <button className="btn btn-primary" style={{ width: '100%' }} onClick={handleOptimize} disabled={loading}>
              {loading ? 'Optimizing...' : '⚙️ Re-optimize'}
            </button>
          </div>
        </div>

        <div>
          {paretoNotes && (
            <div className="card" style={{ marginBottom: '1rem', borderColor: 'var(--gold-border)' }}>
              <div style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.6 }}>
                💡 <strong>Optimization insight:</strong> {paretoNotes}
              </div>
            </div>
          )}

          {tradeOffs.length > 0 && (
            <div className="tradeoff-grid" style={{ marginBottom: '1.5rem' }}>
              {tradeOffs.map((t, i) => (
                <div key={i} className="tradeoff-card animate-in" style={{ animationDelay: `${i * 0.05}s` }}>
                  <div className="tradeoff-value">
                    {typeof t.value === 'number' && t.value > 10 ? t.value.toFixed(0) : t.value}
                  </div>
                  <div className="tradeoff-label">{t.label}</div>
                </div>
              ))}
            </div>
          )}

          {!itinerary && (
            <div className="empty-state">
              <div className="empty-state-icon">💰</div>
              <div className="empty-state-title">Generate an itinerary first</div>
              <p>Use the Planner tab to create an itinerary, then optimize it here.</p>
            </div>
          )}

          {itinerary?.days?.map(day => (
            <div key={day.day} className="card" style={{ marginBottom: '0.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontWeight: 600 }}>{day.date_label}</span>
                <span className="tag tag-gold">${day.total_cost.toFixed(0)}</span>
              </div>
              {day.slots.map((slot, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 13, color: 'var(--text-dim)' }}>
                  <span>{slot.activity.name}</span>
                  <span style={{ color: slot.activity.cost > 0 ? 'var(--gold)' : 'var(--emerald)' }}>
                    {slot.activity.cost > 0 ? `$${slot.activity.cost}` : 'Free'}
                  </span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
