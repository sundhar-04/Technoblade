/**
 * Quiz — 10-question preference wizard.
 * Ported from pr_05's script.js quiz flow into React.
 */
import { useState } from 'react'

const QUESTIONS = [
  {
    id: 'mood', label: 'Travel mood',
    question: "What's your travel mood right now?",
    hint: 'Pick one or more — you can want adventure and culture at once.',
    type: 'cards', cols: 'cols-3', multi: true,
    options: [
      { icon: '🧭', title: 'Adventure', desc: 'Thrill, challenge, the unknown' },
      { icon: '🧖', title: 'Relaxation', desc: 'Unwind, reset, breathe' },
      { icon: '🔎', title: 'Cultural', desc: 'History, heritage, spiritual' },
      { icon: '🎉', title: 'Party & Fun', desc: 'Energy, nightlife, people' },
      { icon: '💒', title: 'Romantic', desc: 'Intimate, scenic, special' },
      { icon: '🧘', title: 'Wellness & Detox', desc: 'Yoga, spa, slow healing' },
      { icon: '🎲', title: 'Surprise me', desc: 'Open to anything' },
    ]
  },
  {
    id: 'who', label: 'Travel type',
    question: 'Who are you travelling with?',
    hint: 'This shapes the entire experience.',
    type: 'pills',
    options: [
      { icon: '🧍', title: 'Solo escape' },
      { icon: '💑', title: 'Couple' },
      { icon: '👫', title: 'Friends' },
      { icon: '👨‍👩‍👦', title: 'Family' },
      { icon: '🐕', title: 'With pets' },
      { icon: '🏕', title: 'Group / Team' },
    ]
  },
  {
    id: 'pace', label: 'Travel pace',
    question: "What's your ideal travel pace?",
    hint: 'How fast do you want to move?',
    type: 'cards', cols: 'cols-2',
    options: [
      { icon: '⚡', title: 'Fast & packed', desc: 'See everything, no rest' },
      { icon: '⚖️', title: 'Balanced', desc: 'Mix of activity and rest' },
      { icon: '🌿', title: 'Slow & easy', desc: 'Take your time, soak it in' },
      { icon: '🎭', title: 'Immersive', desc: 'Deep culture, long stays' },
    ]
  },
  {
    id: 'style', label: 'Travel style',
    question: 'How do you like to travel?',
    hint: 'This shapes your itinerary — not just cost.',
    type: 'cards', cols: 'cols-3',
    options: [
      { icon: '🎒', title: 'Backpacker', desc: 'Hostels, local transport, street food' },
      { icon: '💼', title: 'Comfortable', desc: 'Good hotels, balanced spending' },
      { icon: '👑', title: 'Luxury', desc: 'Premium stays, curated experiences' },
    ]
  },
  {
    id: 'duration', label: 'Duration',
    question: 'How long do you want to travel?',
    hint: 'Days away from home.',
    type: 'pills',
    options: [
      { icon: '🌅', title: 'Weekend (2–3 days)' },
      { icon: '📅', title: 'Short trip (4–6 days)' },
      { icon: '🗓️', title: '1 week' },
      { icon: '📆', title: '2 weeks' },
      { icon: '🌍', title: '1 month+' },
    ]
  },
  {
    id: 'scenery', label: 'Scenery',
    question: 'What scenery speaks to you?',
    hint: 'Pick as many as you like.',
    type: 'cards', cols: 'cols-3', multi: true,
    options: [
      { icon: '🏖️', title: 'Beaches', desc: 'Coastal, sun, water' },
      { icon: '🏔️', title: 'Mountains', desc: 'Heights, cold, majesty' },
      { icon: '🌳', title: 'Forests', desc: 'Wildlife, green, calm' },
      { icon: '🌆', title: 'Cities', desc: 'Urban, vibrant, buzzing' },
      { icon: '🌾', title: 'Countryside', desc: 'Villages, slow life' },
      { icon: '🏛️', title: 'Heritage', desc: 'Temples, forts, ruins' },
      { icon: '🏜️', title: 'Deserts', desc: 'Sand dunes, vast skies' },
      { icon: '💦', title: 'Waterfalls', desc: 'Cascades, gorges, mist' },
    ]
  },
  {
    id: 'food', label: 'Food',
    question: 'What kind of food are you into?',
    hint: 'Pick everything that applies.',
    type: 'cards', cols: 'cols-3', multi: true,
    options: [
      { icon: '🌱', title: 'Vegetarian', desc: 'Plant-based, no meat' },
      { icon: '🍗', title: 'Non-veg', desc: 'Meat, chicken, eggs' },
      { icon: '🐟', title: 'Seafood', desc: 'Fish, prawns, coastal' },
      { icon: '🥗', title: 'Vegan', desc: 'No dairy, fully plant' },
      { icon: '🙏', title: 'Jain / No onion-garlic', desc: 'Sattvic, pure veg' },
      { icon: '🍜', title: 'Street food', desc: 'Chaat, hawkers, local stalls' },
      { icon: '🍢', title: 'Local cuisine', desc: 'Regional specialties' },
      { icon: '🌍', title: 'International', desc: 'Global flavours' },
    ]
  },
  {
    id: 'season', label: 'Season',
    question: 'Which season do you prefer?',
    hint: 'Pick one or more.',
    type: 'cards', cols: 'cols-2', multi: true,
    options: [
      { icon: '☀️', title: 'Summer', desc: 'Heat, brightness, peak energy' },
      { icon: '🌧️', title: 'Monsoon', desc: 'Lush greens, waterfalls, romance' },
      { icon: '❄️', title: 'Winter', desc: 'Crisp air, festivals, fog' },
      { icon: '🎲', title: 'Any season', desc: 'Flexible, open to anything' },
    ]
  },
  {
    id: 'region', label: 'Region',
    question: 'Which region are you drawn to?',
    hint: 'India has 6 wildly different zones.',
    type: 'pills',
    options: [
      { icon: '🏔️', title: 'North India' },
      { icon: '🌴', title: 'South India' },
      { icon: '🌈', title: 'East India' },
      { icon: '🏜️', title: 'West India' },
      { icon: '🌿', title: 'Northeast India' },
      { icon: '🎲', title: 'Anywhere' },
    ]
  },
  {
    id: 'notes', label: 'Special notes',
    question: 'Anything specific on your mind?',
    hint: 'Optional — allergies, accessibility needs, dream experiences.',
    type: 'textarea', optional: true,
    placeholder: 'e.g. "Need wheelchair access", "Celebrating anniversary", "Allergic to nuts"…',
  },
]

export default function Quiz({ onComplete }) {
  const [currentQ, setCurrentQ] = useState(0)
  const [answers, setAnswers] = useState({})

  const q = QUESTIONS[currentQ]

  const setAnswer = (id, val) => setAnswers(prev => ({ ...prev, [id]: [val] }))
  const toggleAnswer = (id, val) => {
    setAnswers(prev => {
      const arr = prev[id] || []
      const i = arr.indexOf(val)
      const next = i === -1 ? [...arr, val] : arr.filter((_, idx) => idx !== i)
      return { ...prev, [id]: next }
    })
  }

  const isNextEnabled = () => {
    if (q.optional || q.type === 'textarea') return true
    return (answers[q.id] || []).length > 0
  }

  const handleNext = () => {
    if (currentQ < QUESTIONS.length - 1) {
      setCurrentQ(currentQ + 1)
    } else {
      onComplete(answers)
    }
  }

  const handleBack = () => {
    if (currentQ > 0) setCurrentQ(currentQ - 1)
  }

  const renderCards = () => (
    <div className={`ts-options-grid ${q.cols || 'cols-3'}`}>
      {q.options.map(opt => {
        const selected = (answers[q.id] || []).includes(opt.title)
        return (
          <div
            key={opt.title}
            className={`ts-option-card ${selected ? 'selected' : ''}`}
            onClick={() => {
              if (q.multi) toggleAnswer(q.id, opt.title)
              else setAnswer(q.id, opt.title)
            }}
          >
            <div className="ts-option-check">
              <svg viewBox="0 0 10 10" fill="none">
                <path d="M2 5l2.5 2.5L8 3" stroke="#0B0F1A" strokeWidth="1.5"
                  strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div className="ts-option-icon">{opt.icon}</div>
            <div className="ts-option-title">{opt.title}</div>
            {opt.desc && <div className="ts-option-desc">{opt.desc}</div>}
          </div>
        )
      })}
    </div>
  )

  const renderPills = () => (
    <div className="ts-options-pills">
      {q.options.map(opt => {
        const selected = (answers[q.id] || []).includes(opt.title)
        return (
          <div
            key={opt.title}
            className={`ts-option-pill ${selected ? 'selected' : ''}`}
            onClick={() => {
              if (q.multi) toggleAnswer(q.id, opt.title)
              else setAnswer(q.id, opt.title)
            }}
          >
            <span>{opt.icon}</span> {opt.title}
          </div>
        )
      })}
    </div>
  )

  const renderTextarea = () => (
    <div className="ts-notes-wrap">
      <textarea
        className="ts-notes-textarea"
        placeholder={q.placeholder || 'Type anything here…'}
        rows={5}
        value={answers[q.id] || ''}
        maxLength={300}
        onChange={e => setAnswers(prev => ({ ...prev, [q.id]: e.target.value.trim() }))}
      />
      <div className="ts-notes-counter">{(answers[q.id] || '').length} / 300</div>
      <div className="ts-notes-optional-label">Optional — skip if nothing to add</div>
    </div>
  )

  return (
    <section className="ts-quiz-screen">
      {/* Mobile header */}
      <div className="ts-mobile-quiz-header">
        <div className="ts-mobile-logo">Trip<span>Soul</span></div>
        <div className="ts-mobile-progress">{currentQ + 1} / {QUESTIONS.length}</div>
      </div>

      <div className="ts-quiz-layout">
        {/* Sidebar */}
        <aside className="ts-quiz-sidebar">
          <div className="ts-sidebar-logo">Trip<span>Soul</span></div>
          <div className="ts-sidebar-progress-label">Your progress</div>
          <div className="ts-sidebar-progress-track">
            <div className="ts-sidebar-progress-fill"
              style={{ width: `${Math.round((currentQ / QUESTIONS.length) * 100)}%` }} />
          </div>
          <div className="ts-sidebar-steps">
            {QUESTIONS.map((sq, i) => (
              <div key={sq.id} className={`ts-sidebar-step ${
                i < currentQ ? 'done' : i === currentQ ? 'active' : ''
              }`}>
                <div className="ts-step-dot">{i + 1}</div>
                <div className="ts-step-label">{sq.label}</div>
              </div>
            ))}
          </div>
        </aside>

        {/* Main quiz area */}
        <main className="ts-quiz-main">
          <div className="animate-in" key={currentQ}>
            <div className="ts-quiz-q-counter">
              Question {currentQ + 1} of {QUESTIONS.length}
            </div>
            <h2 className="ts-quiz-question">{q.question}</h2>
            <p className="ts-quiz-hint">{q.hint}</p>

            {q.type === 'cards' && renderCards()}
            {q.type === 'pills' && renderPills()}
            {q.type === 'textarea' && renderTextarea()}

            {/* Nav */}
            <div className="ts-quiz-nav">
              <button className="ts-btn-nav-back" disabled={currentQ === 0} onClick={handleBack}>
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M10 7H4M6 4L3 7l3 3" stroke="currentColor" strokeWidth="1.4"
                    strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                Back
              </button>
              <button
                className="ts-btn-nav-next"
                disabled={!isNextEnabled()}
                onClick={handleNext}
              >
                {currentQ === QUESTIONS.length - 1 ? 'Find my destinations' : 'Next'}
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M2 7h10M8 3l4 4-4 4" stroke="currentColor" strokeWidth="1.4"
                    strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </div>
          </div>
        </main>
      </div>
    </section>
  )
}
