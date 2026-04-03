/**
 * Handbook — Full-screen destination intelligence overlay.
 * Ported from pr_05's handbook feature.
 */
import { useState, useEffect } from 'react'
import { getHandbook } from '../api/client'

export default function Handbook({ city, onClose }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false

    const fetchData = async () => {
      try {
        const res = await getHandbook(city)
        if (!cancelled) {
          setData(res)
          setLoading(false)
        }
      } catch (e) {
        if (!cancelled) {
          setError(e.message)
          setLoading(false)
        }
      }
    }
    fetchData()
    return () => { cancelled = true }
  }, [city])

  return (
    <div className="ts-handbook-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="ts-handbook-panel">
        <button className="ts-handbook-close" onClick={onClose}>×</button>

        {loading && (
          <div style={{ textAlign: 'center', padding: '2rem 0' }}>
            <div className="ts-loading-icon" style={{ margin: '0 auto 1rem' }}></div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', color: 'var(--text)' }}>
              Building your {city} handbook…
            </div>
          </div>
        )}

        {error && (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-dim)' }}>
            Handbook unavailable — backend may be offline.<br />
            <a href={`https://www.google.com/search?q=${encodeURIComponent(city + ' travel guide India')}`}
              target="_blank" rel="noreferrer"
              style={{ color: 'var(--gold)', marginTop: '1rem', display: 'inline-block' }}>
              Search on Google instead →
            </a>
          </div>
        )}

        {data && (
          <>
            {/* Header */}
            <div style={{ marginBottom: '1.5rem' }}>
              <div className="ts-hb-label">{data.state || ''}</div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: 700, color: 'var(--text)', lineHeight: 1.1 }}>
                {data.city}
              </div>
              {data.tagline && (
                <div style={{ fontSize: 14, color: 'var(--text-dim)', marginTop: 6, fontStyle: 'italic' }}>
                  {data.tagline}
                </div>
              )}
            </div>

            {/* Safety + AQI */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: '1.25rem' }}>
              <div className="ts-hb-stat-card" style={{ borderColor: 'rgba(76,175,130,0.25)', background: 'rgba(76,175,130,0.1)' }}>
                <div className="ts-hb-label" style={{ color: '#4CAF82' }}>Safety</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 600, color: '#4CAF82' }}>
                  {data.safety_score}/10
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 4 }}>
                  {data.safety_note || ''}
                </div>
              </div>
              <div className="ts-hb-stat-card" style={{ borderColor: 'rgba(232,168,56,0.2)', background: 'rgba(232,168,56,0.08)' }}>
                <div className="ts-hb-label">AQI — {data.aqi?.season || 'Current'}</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--gold)' }}>
                  {data.aqi?.value || 'N/A'}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 4 }}>
                  {data.aqi?.advisory || ''}
                </div>
              </div>
            </div>

            {/* Budget */}
            {data.budget_per_day && (
              <div style={{ marginBottom: '1.25rem' }}>
                <div className="ts-hb-label">Daily budget per person</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginTop: 8 }}>
                  {Object.entries(data.budget_per_day).map(([style, range]) => (
                    <div key={style} className="ts-hb-budget-item">
                      <div style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 4 }}>
                        {style}
                      </div>
                      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--gold)' }}>{range}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Connectivity */}
            {data.connectivity && (
              <div className="ts-hb-section">
                <div className="ts-hb-label">How to reach</div>
                <div style={{ fontSize: 13, color: 'var(--text-dim)', lineHeight: 1.6, marginTop: 6 }}>
                  {typeof data.connectivity === 'object'
                    ? Object.entries(data.connectivity).map(([k, v]) => (
                        <div key={k} style={{ marginBottom: 6 }}>
                          <span style={{ color: 'var(--gold)', fontSize: 11, textTransform: 'uppercase', letterSpacing: '.08em' }}>{k}</span>
                          <br />
                          {v}
                        </div>
                      ))
                    : data.connectivity
                  }
                </div>
              </div>
            )}

            {/* Food */}
            {data.must_try_food?.length > 0 && (
              <div className="ts-hb-section">
                <div className="ts-hb-label">Food & dining</div>
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 6 }}>Must try</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {data.must_try_food.map(f => (
                      <span key={f} className="ts-hb-food-chip">{f}</span>
                    ))}
                  </div>
                </div>
                {data.fine_dining?.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 4 }}>Fine dining</div>
                    {data.fine_dining.map(r => (
                      <div key={r} style={{ fontSize: 13, color: 'var(--text)', padding: '3px 0' }}>• {r}</div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Hidden tips */}
            {data.hidden_tips?.length > 0 && (
              <div className="ts-hb-section">
                <div className="ts-hb-label">Hidden tips</div>
                {data.hidden_tips.map(tip => (
                  <div key={tip} style={{ display: 'flex', gap: 8, marginBottom: 6, alignItems: 'flex-start', marginTop: 8 }}>
                    <span style={{ color: 'var(--gold)', flexShrink: 0 }}>→</span>
                    <span style={{ fontSize: 13, color: 'var(--text-dim)', lineHeight: 1.5 }}>{tip}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Top experiences */}
            {data.top_experiences?.length > 0 && (
              <div className="ts-hb-section">
                <div className="ts-hb-label">Top experiences</div>
                {data.top_experiences.map(exp => (
                  <div key={exp.name} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.04)', marginTop: 8
                  }}>
                    <span style={{ fontSize: 13, color: 'var(--text)' }}>{exp.name}</span>
                    <div style={{ textAlign: 'right' }}>
                      <span style={{ fontSize: 12, color: 'var(--gold)', display: 'block' }}>{exp.cost || ''}</span>
                      <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>{exp.duration || ''}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Day trips */}
            {data.nearby_day_trips?.length > 0 && (
              <div className="ts-hb-section">
                <div className="ts-hb-label">Nearby day trips</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
                  {data.nearby_day_trips.map(t => (
                    <span key={t} className="ts-hb-trip-chip">{t}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Avoid */}
            {data.avoid && (
              <div className="ts-hb-avoid">
                <div className="ts-hb-label" style={{ color: '#E05C5C' }}>Watch out</div>
                <div style={{ fontSize: 13, color: 'var(--text-dim)', marginTop: 4 }}>{data.avoid}</div>
              </div>
            )}

            {/* Best time */}
            <div style={{ marginTop: '1.25rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border)' }}>
              <div className="ts-hb-label">Best time to visit</div>
              <div style={{ fontSize: 13, color: 'var(--text-dim)', marginTop: 4 }}>{data.best_time || 'N/A'}</div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
