/**
 * Results — AI destination recommendations with soul panel.
 * Ported from pr_05's results section.
 */
import { useState, useEffect, useRef } from 'react'

// Soul panel text maps (from pr_05)
const MOOD_LINE = {
  'Adventure': 'a craving for the unknown and raw challenge',
  'Relaxation': 'a deep need to slow down, breathe, and just be',
  'Cultural': 'a hunger for depth, meaning, and living heritage',
  'Party & Fun': 'a hunger for energy, people, and great stories',
  'Romantic': 'a desire for intimate and beautiful shared moments',
  'Wellness & Detox': 'a call to heal, restore, and come back to yourself',
  'Surprise me': 'an open, curious spirit ready for anything',
}
const PACE_LINE = {
  'Fast & packed': 'you want every single hour to count',
  'Balanced': 'you move at your own unhurried rhythm',
  'Slow & easy': 'you believe travel is about being, not rushing',
  'Immersive': 'you go deep — not wide',
}
const WHO_LINE = {
  'Solo escape': 'travelling alone means freedom without compromise',
  'Couple': 'this journey is about shared memory-making',
  'Friends': 'the best stories need the right people beside you',
  'Family': 'every moment here is a chance to connect deeply',
  'With pets': 'your best travel companion comes with four paws',
  'Group / Team': 'shared experiences build the strongest bonds',
}

const STYLE_META = {
  Backpacker: { emoji: '🎒', colour: '#4CAF82' },
  Comfortable: { emoji: '💼', colour: '#E8A838' },
  Luxury: { emoji: '👑', colour: '#C8A0E8' },
}

// Typewriter component
function Typewriter({ text, highlight }) {
  const [displayed, setDisplayed] = useState('')
  const [done, setDone] = useState(false)

  useEffect(() => {
    setDisplayed('')
    setDone(false)
    let i = 0
    const id = setInterval(() => {
      i++
      if (i <= text.length) {
        setDisplayed(text.substring(0, i))
      } else {
        setDone(true)
        clearInterval(id)
      }
    }, i < 30 ? 50 : 20)
    return () => clearInterval(id)
  }, [text])

  const renderText = (t) => {
    if (!highlight) return t
    const regex = new RegExp(`\\b${highlight.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'g')
    const parts = t.split(regex)
    const result = []
    parts.forEach((part, i) => {
      result.push(part)
      if (i < parts.length - 1) {
        result.push(<span key={i} className="ts-hl">{highlight}</span>)
      }
    })
    return result
  }

  return (
    <div className="ts-soul-explanation">
      {renderText(displayed)}
      {!done && <span className="ts-typing-cursor"></span>}
    </div>
  )
}

export default function Results({ answers, recommendations, onRestart, onRefine, onPlanTrip, onOpenHandbook }) {
  const style = (answers.style || ['Comfortable'])[0]
  const mood = (answers.mood || [])[0] || ''
  const who = (answers.who || [])[0] || ''
  const pace = (answers.pace || [])[0] || ''
  const sc = (answers.scenery || [])[0] || ''
  const notes = answers.notes || ''

  // Trait chips
  const traits = []
  if (mood) traits.push(mood + ' seeker')
  if (who) traits.push(who)
  if (pace) traits.push(pace + ' pace')
  if (sc) traits.push(sc + ' lover')

  // Soul explanation
  const topDest = recommendations[0]
  const destName = topDest ? (topDest.name || '') : 'your destination'
  const ml = MOOD_LINE[mood] || 'a sense of wanderlust'
  const pl = PACE_LINE[pace] || 'travelling your way'
  const wl = who ? `As someone where ${WHO_LINE[who] || 'on this journey'}, ` : ''
  const sl = sc ? `Your draw to ${sc.toLowerCase()} seals it — ` : ''
  const soulText = `You came in with ${ml}, and ${pl}. ${sl}${destName} offers exactly what you're looking for. ${wl}this is a trip that will stay with you.`

  const meta = STYLE_META[style] || STYLE_META['Comfortable']

  return (
    <section className="ts-results-screen">
      <div className="ts-results-header">
        <div className="ts-results-eyebrow">Your perfect matches</div>

        {/* Style banner */}
        <div className="ts-style-banner" style={{
          background: 'rgba(255,255,255,0.04)',
          border: `1px solid ${meta.colour}44`,
          color: meta.colour
        }}>
          {meta.emoji} Itinerary crafted for a <strong style={{ marginLeft: 4 }}>{style}</strong>&nbsp;experience
        </div>

        <h2 className="ts-results-title">
          Here's where your <em>soul wants to go</em>
        </h2>
        <p className="ts-results-sub">Based on your mood and travel style</p>

        {/* Notes banner */}
        {notes && notes.trim() && (
          <div className="ts-notes-banner">
            <span style={{ fontSize: '1rem' }}>📝</span>
            <span>
              <strong style={{ color: 'var(--gold)', fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', display: 'block', marginBottom: 3 }}>
                We noted
              </strong>
              {notes}
            </span>
          </div>
        )}
      </div>

      {/* Soul panel */}
      <div className="ts-soul-panel">
        <div className="ts-soul-panel-header">
          <div className="ts-soul-icon">🧠</div>
          <div>
            <div className="ts-soul-panel-label">Why these places fit you</div>
            <div className="ts-soul-panel-sub">TripSoul's read on your travel personality</div>
          </div>
        </div>
        <Typewriter text={soulText} highlight={destName} />
        <div className="ts-soul-traits">
          {traits.map(t => (
            <div key={t} className="ts-soul-trait">
              <div className="ts-trait-dot"></div>{t}
            </div>
          ))}
        </div>
      </div>

      {/* Destination cards */}
      <div className="ts-results-grid">
        {recommendations.map((dest, i) => (
          <div key={dest.name} className={`ts-dest-card ${i === 0 ? 'top-pick' : ''}`}>
            <div className="ts-dest-card-img">
              {dest.img
                ? <div className="ts-dest-card-img-bg" style={{ backgroundImage: `url('${dest.img}')` }} />
                : <div className="ts-dest-card-img-placeholder">{dest.icon || '🗺️'}</div>
              }
              {i === 0 && <div className="ts-dest-card-badge">Top pick</div>}
            </div>
            <div className="ts-dest-card-body">
              <div className="ts-dest-card-state">{dest.state || ''}</div>
              <div className="ts-dest-card-name">{dest.name}</div>
              <div className="ts-dest-card-reason">{dest.reason}</div>
              {dest.itinerary_hint && (
                <div className="ts-dest-itinerary-hint">
                  <div className="ts-dest-itinerary-label">✨ AI Plan — {style}</div>
                  <div className="ts-dest-itinerary-text">{dest.itinerary_hint}</div>
                </div>
              )}
              <div className="ts-dest-card-tags">
                {(dest.tags || []).map(t => (
                  <span key={t} className="ts-dest-tag">{t}</span>
                ))}
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="ts-dest-card-explore" onClick={() => onOpenHandbook(dest.name)}>
                  {i === 0 ? `Explore ${dest.name}` : 'Explore'}
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path d="M1 6h10M7 2l4 4-4 4" stroke="currentColor" strokeWidth="1.4"
                      strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="ts-results-actions">
        <button className="ts-btn-outline" onClick={onRestart}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2 7a5 5 0 1 0 1.5-3.5L1 1" stroke="currentColor" strokeWidth="1.4"
              strokeLinecap="round" strokeLinejoin="round" />
            <path d="M1 1v3h3" stroke="currentColor" strokeWidth="1.4"
              strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Start over
        </button>
        <button className="ts-btn-outline" onClick={onRefine}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M1 4h12M3 7h8M5 10h4" stroke="currentColor" strokeWidth="1.4"
              strokeLinecap="round" />
          </svg>
          Different suggestions
        </button>
        <button className="ts-btn-primary" style={{ fontSize: 14, padding: '12px 24px' }}
          onClick={onPlanTrip}>
          Plan this trip
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2 7h10M8 3l4 4-4 4" stroke="currentColor" strokeWidth="1.4"
              strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>
    </section>
  )
}
