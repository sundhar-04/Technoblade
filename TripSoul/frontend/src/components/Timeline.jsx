import { useState, useRef, useCallback } from 'react'

const API_URL = 'http://127.0.0.1:8000'

const CATEGORIES = ['culture', 'food', 'adventure', 'nature', 'shopping', 'nightlife', 'history']
const CATEGORY_COLORS = {
  culture: '#E8A838',
  food: '#4CC9A0',
  adventure: '#5B8DEF',
  nightlife: '#A78BFA',
  nature: '#4CC9A0',
  shopping: '#F59E0B',
  history: '#E05C5C',
  transport: '#8B5CF6',
  hotel: '#F59E0B',
}

export default function Timeline({ itinerary, setItinerary }) {
  const [activeDay, setActiveDay] = useState(0)
  const [dragIdx, setDragIdx] = useState(null)
  const [dropIdx, setDropIdx] = useState(null)
  const [showAddPanel, setShowAddPanel] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [aiSuggestions, setAiSuggestions] = useState([])
  const [loadingSuggestions, setLoadingSuggestions] = useState(false)
  const [editingTimeIdx, setEditingTimeIdx] = useState(null)

  // Manual entry state
  const [manualName, setManualName] = useState('')
  const [manualCategory, setManualCategory] = useState('culture')
  const [manualStartTime, setManualStartTime] = useState('10:00')
  const [manualEndTime, setManualEndTime] = useState('11:30')
  const [manualCost, setManualCost] = useState(0)
  const [manualDescription, setManualDescription] = useState('')

  const debounceRef = useRef(null)

  // ── Empty state ──
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

  // ── Recalculate day stats ──
  const totalCost = day.slots.reduce((sum, s) => sum + (s.activity?.cost || 0), 0)
  const totalTravel = day.slots.reduce((sum, s) => sum + (s.travel_time_minutes || 0), 0)

  // ═══════════════════════════════════════════
  //  DRAG AND DROP (same day only)
  // ═══════════════════════════════════════════
  const handleDragStart = (e, idx) => {
    setDragIdx(idx)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', idx)
    // Add a small delay to allow the ghost to render
    setTimeout(() => {
      const el = document.querySelector(`[data-slot-idx="${idx}"]`)
      if (el) el.classList.add('timeline-item-dragging')
    }, 0)
  }

  const handleDragEnd = () => {
    // Clean up all drag classes
    document.querySelectorAll('.timeline-item-dragging').forEach(el =>
      el.classList.remove('timeline-item-dragging')
    )
    document.querySelectorAll('.timeline-drop-active').forEach(el =>
      el.classList.remove('timeline-drop-active')
    )
    setDragIdx(null)
    setDropIdx(null)
  }

  const handleDragOver = (e, idx) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setDropIdx(idx)
  }

  const handleDragLeave = () => {
    setDropIdx(null)
  }

  const handleDrop = (e, targetIdx) => {
    e.preventDefault()
    const sourceIdx = dragIdx
    if (sourceIdx === null || sourceIdx === targetIdx) {
      handleDragEnd()
      return
    }

    const newDays = JSON.parse(JSON.stringify(itinerary.days))
    const slots = newDays[activeDay].slots
    const [moved] = slots.splice(sourceIdx, 1)
    slots.splice(targetIdx, 0, moved)

    // Reassign times sequentially
    reassignTimes(slots)

    newDays[activeDay].slots = slots
    newDays[activeDay].total_cost = slots.reduce((s, sl) => s + (sl.activity?.cost || 0), 0)
    setItinerary({ ...itinerary, days: newDays })
    handleDragEnd()
  }

  // ── Reassign times after reorder ──
  const reassignTimes = (slots) => {
    let currentTime = parseTime(slots[0]?.start_time || '09:00')
    slots.forEach(slot => {
      slot.start_time = formatTime(currentTime)
      const duration = slot.activity?.estimated_duration_minutes || 90
      currentTime += duration
      slot.end_time = formatTime(currentTime)
      currentTime += (slot.travel_time_minutes || 15)
    })
  }

  // ═══════════════════════════════════════════
  //  DELETE ACTIVITY
  // ═══════════════════════════════════════════
  const deleteSlot = (idx) => {
    const newDays = JSON.parse(JSON.stringify(itinerary.days))
    newDays[activeDay].slots.splice(idx, 1)
    if (newDays[activeDay].slots.length > 0) {
      reassignTimes(newDays[activeDay].slots)
    }
    newDays[activeDay].total_cost = newDays[activeDay].slots.reduce((s, sl) => s + (sl.activity?.cost || 0), 0)
    newDays[activeDay].total_travel_minutes = newDays[activeDay].slots.reduce((s, sl) => s + (sl.travel_time_minutes || 0), 0)
    setItinerary({ ...itinerary, days: newDays })
  }

  // ═══════════════════════════════════════════
  //  INLINE TIME EDITING
  // ═══════════════════════════════════════════
  const updateSlotTime = (idx, field, value) => {
    const newDays = JSON.parse(JSON.stringify(itinerary.days))
    newDays[activeDay].slots[idx][field] = value
    setItinerary({ ...itinerary, days: newDays })
  }

  // ═══════════════════════════════════════════
  //  AI SUGGESTIONS
  // ═══════════════════════════════════════════
  const fetchSuggestions = useCallback((query) => {
    if (debounceRef.current) clearTimeout(debounceRef.current)

    if (!query || query.length < 2) {
      setAiSuggestions([])
      return
    }

    debounceRef.current = setTimeout(async () => {
      setLoadingSuggestions(true)
      try {
        const existingPlaces = day.slots.map(s => s.activity?.name).filter(Boolean)
        const res = await fetch(`${API_URL}/suggest-places`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            city: itinerary.city || query,
            day_theme: query,
            existing_places: existingPlaces,
            mood: '',
            interests: [],
          }),
        })
        if (res.ok) {
          const data = await res.json()
          setAiSuggestions(data.suggestions || [])
        }
      } catch {
        // Fallback - show nothing on error
        setAiSuggestions([])
      }
      setLoadingSuggestions(false)
    }, 500)
  }, [activeDay, day, itinerary])

  const handleSearchChange = (e) => {
    const q = e.target.value
    setSearchQuery(q)
    fetchSuggestions(q)
  }

  // ═══════════════════════════════════════════
  //  ADD ACTIVITY (from suggestion or manual)
  // ═══════════════════════════════════════════
  const addActivityFromSuggestion = (suggestion) => {
    const lastSlot = day.slots[day.slots.length - 1]
    const startMinutes = lastSlot ? parseTime(lastSlot.end_time) + 15 : parseTime('09:00')

    const lat = suggestion.lat || (lastSlot?.activity?.lat) || 40.730610
    const lng = suggestion.lng || (lastSlot?.activity?.lng) || -73.935242

    const newSlot = {
      start_time: formatTime(startMinutes),
      end_time: formatTime(startMinutes + (suggestion.estimated_duration_minutes || 90)),
      travel_time_minutes: 15,
      travel_distance_km: 2,
      activity: {
        name: suggestion.name,
        category: suggestion.category || 'culture',
        description: suggestion.description || '',
        cost: suggestion.cost || 0,
        confidence_score: 0.85,
        reason: suggestion.reason || '',
        estimated_duration_minutes: suggestion.estimated_duration_minutes || 90,
        lat: lat,
        lng: lng,
      },
    }

    const newDays = JSON.parse(JSON.stringify(itinerary.days))
    newDays[activeDay].slots.push(newSlot)
    newDays[activeDay].total_cost = newDays[activeDay].slots.reduce((s, sl) => s + (sl.activity?.cost || 0), 0)
    
    // Recalculate root totals
    const newTotalCost = newDays.reduce((sum, d) => sum + (d.total_cost || 0), 0)
    
    setItinerary({ ...itinerary, days: newDays, total_cost: newTotalCost })
    setShowAddPanel(false)
    setSearchQuery('')
    setAiSuggestions([])
  }

  const addManualActivity = () => {
    if (!manualName.trim()) return

    addActivityFromSuggestion({
      name: manualName.trim(),
      category: manualCategory,
      description: manualDescription.trim() || `Visit ${manualName.trim()}`,
      estimated_duration_minutes: timeDiffMinutes(manualStartTime, manualEndTime),
      cost: manualCost,
      reason: 'Manually added by you',
    })

    // Reset form
    setManualName('')
    setManualCategory('culture')
    setManualStartTime('10:00')
    setManualEndTime('11:30')
    setManualCost(0)
    setManualDescription('')
  }

  // ── Time helpers ──
  function parseTime(str) {
    if (!str) return 540 // 09:00
    const [h, m] = str.split(':').map(Number)
    return (h || 0) * 60 + (m || 0)
  }

  function formatTime(minutes) {
    const h = Math.floor(minutes / 60) % 24
    const m = minutes % 60
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
  }

  function timeDiffMinutes(start, end) {
    return Math.max(30, parseTime(end) - parseTime(start))
  }

  // ═══════════════════════════════════════════
  //  RENDER
  // ═══════════════════════════════════════════
  return (
    <div className="animate-in">
      <div className="section-label">Timeline</div>
      <h2 className="section-title" style={{ marginBottom: '0.25rem' }}>
        Day-by-day schedule
      </h2>
      <p style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: '1.25rem' }}>
        ≡ Drag to reorder · + Add places · AI suggests activities
      </p>

      {/* ── Day Tabs ── */}
      <div className="day-tabs">
        {itinerary.days.map((d, i) => (
          <button
            key={i}
            className={`day-tab ${i === activeDay ? 'active' : ''}`}
            onClick={() => { setActiveDay(i); setShowAddPanel(false) }}
          >
            Day {d.day} · ₹{(d.total_cost || 0).toFixed(0)}
          </button>
        ))}
      </div>

      {/* ── Day Stats ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: '1.5rem' }}>
        <div className="tradeoff-card">
          <div className="tradeoff-value">{day.slots.length}</div>
          <div className="tradeoff-label">Activities</div>
        </div>
        <div className="tradeoff-card">
          <div className="tradeoff-value">₹{totalCost.toFixed(0)}</div>
          <div className="tradeoff-label">Day cost</div>
        </div>
        <div className="tradeoff-card">
          <div className="tradeoff-value">{totalTravel}m</div>
          <div className="tradeoff-label">Travel time</div>
        </div>
      </div>

      {/* ── Timeline Items (Draggable) ── */}
      <div className="timeline tl-drag-container">
        {day.slots.map((slot, i) => {
          const catColor = CATEGORY_COLORS[slot.activity?.category] || 'var(--gold)'

          return (
            <div key={i}>
              {/* Travel connector */}
              {slot.travel_time_minutes > 0 && i > 0 && (
                <div className="timeline-item" style={{ paddingBottom: '0.35rem' }}>
                  <div className="timeline-dot travel" />
                  <div className="timeline-travel">
                    🚶 {slot.travel_time_minutes} min · {slot.travel_distance_km || '?'} km
                  </div>
                </div>
              )}

              {/* Drop zone indicator */}
              {dragIdx !== null && dropIdx === i && dragIdx !== i && (
                <div className="timeline-drop-zone timeline-drop-active">
                  <div className="drop-zone-line" />
                  <span className="drop-zone-label">Drop here</span>
                </div>
              )}

              {/* Activity item */}
              <div
                className={`timeline-item tl-draggable ${dragIdx === i ? 'timeline-item-dragging' : ''}`}
                data-slot-idx={i}
                draggable
                onDragStart={(e) => handleDragStart(e, i)}
                onDragEnd={handleDragEnd}
                onDragOver={(e) => handleDragOver(e, i)}
                onDragLeave={handleDragLeave}
                onDrop={(e) => handleDrop(e, i)}
              >
                {/* Drag handle */}
                <div className="tl-drag-handle" title="Drag to reorder">≡</div>

                <div className="timeline-dot" style={{ background: catColor }} />

                {/* Time (click to edit) */}
                {editingTimeIdx === i ? (
                  <div className="tl-time-editor">
                    <input
                      type="time"
                      value={slot.start_time}
                      onChange={(e) => updateSlotTime(i, 'start_time', e.target.value)}
                      className="time-input"
                    />
                    <span>—</span>
                    <input
                      type="time"
                      value={slot.end_time}
                      onChange={(e) => updateSlotTime(i, 'end_time', e.target.value)}
                      className="time-input"
                    />
                    <button className="tl-time-done" onClick={() => setEditingTimeIdx(null)}>✓</button>
                  </div>
                ) : (
                  <div
                    className="timeline-time tl-time-clickable"
                    onClick={() => setEditingTimeIdx(i)}
                    title="Click to edit time"
                  >
                    {slot.start_time} — {slot.end_time}
                    <span className="tl-edit-hint">✎</span>
                  </div>
                )}

                <div className="timeline-activity">{slot.activity?.name}</div>
                <div className="timeline-desc">{slot.activity?.description}</div>

                {/* Tags row */}
                <div style={{ display: 'flex', gap: 6, marginTop: 6, flexWrap: 'wrap', alignItems: 'center' }}>
                  <span className="tag" style={{
                    background: `${catColor}20`,
                    color: catColor,
                    border: `1px solid ${catColor}40`,
                  }}>
                    {slot.activity?.category}
                  </span>
                  {slot.activity?.cost > 0 && (
                    <span className="tag tag-gold">₹{slot.activity.cost}</span>
                  )}
                  {slot.activity?.cost === 0 && (
                    <span className="tag tag-emerald">Free</span>
                  )}
                  {slot.metadata?.carrier && (
                    <span className="tag" style={{ background: 'var(--surface-high)', color: '#fff', border: '1px solid #8B5CF6' }}>
                      ✈️ {slot.metadata.carrier}
                    </span>
                  )}
                  {slot.metadata?.type === 'hotel' && (
                    <span className="tag" style={{ background: 'var(--surface-high)', color: '#fff', border: '1px solid #F59E0B' }}>
                      🏨 Check-in
                    </span>
                  )}
                  <span className={`confidence ${slot.activity?.confidence_score > 0.8 ? 'confidence-high' : 'confidence-med'}`}>
                    <span className="confidence-bar" style={{ width: 30 }}>
                      <span className="confidence-fill" style={{ width: `${(slot.activity?.confidence_score || 0.7) * 100}%` }} />
                    </span>
                    {((slot.activity?.confidence_score || 0.7) * 100).toFixed(0)}%
                  </span>
                </div>

                {slot.activity?.reason && (
                  <div style={{ fontSize: 11, color: 'var(--text-faint)', marginTop: 6, fontStyle: 'italic' }}>
                    {slot.activity.reason}
                  </div>
                )}

                {/* Delete button */}
                <button
                  className="tl-delete-btn"
                  onClick={(e) => { e.stopPropagation(); deleteSlot(i) }}
                  title="Remove activity"
                >
                  ×
                </button>
              </div>
            </div>
          )
        })}

        {/* Drop zone at end */}
        {dragIdx !== null && (
          <div
            className={`timeline-drop-zone ${dropIdx === day.slots.length ? 'timeline-drop-active' : ''}`}
            onDragOver={(e) => handleDragOver(e, day.slots.length)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, day.slots.length)}
          >
            <div className="drop-zone-line" />
          </div>
        )}
      </div>

      {/* ═══════════════════════════════════════════
           ADD PLACE BUTTON & PANEL
         ═══════════════════════════════════════════ */}
      <button
        className="tl-add-btn"
        onClick={() => setShowAddPanel(!showAddPanel)}
      >
        {showAddPanel ? '✕ Close' : '＋ Add a place'}
      </button>

      {showAddPanel && (
        <div className="add-place-panel animate-in">
          {/* AI Search */}
          <div className="add-place-section">
            <div className="add-place-section-label">
              <span className="add-place-ai-icon">✨</span>
              AI Suggestions
            </div>
            <input
              type="text"
              className="add-place-search"
              placeholder="Type a place, activity, or theme (e.g. 'temples', 'sunset')..."
              value={searchQuery}
              onChange={handleSearchChange}
              autoFocus
            />

            {loadingSuggestions && (
              <div className="add-place-loading">
                <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                Finding suggestions...
              </div>
            )}

            {aiSuggestions.length > 0 && (
              <div className="ai-suggestions-grid">
                {aiSuggestions.map((s, i) => {
                  const sColor = CATEGORY_COLORS[s.category] || 'var(--gold)'
                  return (
                    <button
                      key={i}
                      className="ai-suggestion-card"
                      onClick={() => addActivityFromSuggestion(s)}
                    >
                      <div className="ai-sug-header">
                        <span className="ai-sug-name">{s.name}</span>
                        <span className="ai-sug-cost" style={{ color: sColor }}>
                          {s.cost > 0 ? `₹${s.cost}` : 'Free'}
                        </span>
                      </div>
                      <div className="ai-sug-desc">{s.description}</div>
                      <div className="ai-sug-footer">
                        <span className="tag" style={{
                          background: `${sColor}20`, color: sColor,
                          border: `1px solid ${sColor}40`, fontSize: 10,
                        }}>
                          {s.category}
                        </span>
                        <span style={{ fontSize: 10, color: 'var(--text-faint)' }}>
                          ~{s.estimated_duration_minutes || 90} min
                        </span>
                      </div>
                      {s.reason && (
                        <div className="ai-sug-reason">💡 {s.reason}</div>
                      )}
                    </button>
                  )
                })}
              </div>
            )}
          </div>

          {/* Divider */}
          <div className="add-place-divider">
            <span>or add manually</span>
          </div>

          {/* Manual Entry Form */}
          <div className="manual-entry-form">
            <div className="manual-entry-row">
              <div className="input-group" style={{ flex: 2 }}>
                <label className="input-label">Place name *</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. Amber Fort, Chai at Tapri..."
                  value={manualName}
                  onChange={(e) => setManualName(e.target.value)}
                />
              </div>
              <div className="input-group" style={{ flex: 1 }}>
                <label className="input-label">Category</label>
                <select
                  className="select"
                  value={manualCategory}
                  onChange={(e) => setManualCategory(e.target.value)}
                >
                  {CATEGORIES.map(c => (
                    <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="manual-entry-row">
              <div className="input-group" style={{ flex: 1 }}>
                <label className="input-label">Start time</label>
                <input
                  type="time"
                  className="input"
                  value={manualStartTime}
                  onChange={(e) => setManualStartTime(e.target.value)}
                />
              </div>
              <div className="input-group" style={{ flex: 1 }}>
                <label className="input-label">End time</label>
                <input
                  type="time"
                  className="input"
                  value={manualEndTime}
                  onChange={(e) => setManualEndTime(e.target.value)}
                />
              </div>
              <div className="input-group" style={{ flex: 1 }}>
                <label className="input-label">Cost (₹)</label>
                <input
                  type="number"
                  className="input"
                  min={0}
                  value={manualCost}
                  onChange={(e) => setManualCost(Number(e.target.value))}
                />
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">Description (optional)</label>
              <input
                type="text"
                className="input"
                placeholder="A short note about this activity..."
                value={manualDescription}
                onChange={(e) => setManualDescription(e.target.value)}
              />
            </div>

            <button
              className="btn btn-primary"
              onClick={addManualActivity}
              disabled={!manualName.trim()}
              style={{ marginTop: '0.75rem', width: '100%' }}
            >
              ＋ Add to Day {day.day}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
