import { useState, useEffect, useRef } from 'react'
import { generateItinerary, searchFlights, searchHotels } from '../api/client'

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

// Maps quiz answers to Planner state values
function mapQuizToPlanner(quizAnswers) {
  if (!quizAnswers || Object.keys(quizAnswers).length === 0) return null

  const whoMap = { 'Solo escape': 'solo', 'Couple': 'couple', 'Friends': 'group', 'Family': 'family', 'With pets': 'couple', 'Group / Team': 'group' }
  const moodMap = { 'Adventure': 'energetic', 'Relaxation': 'relaxed', 'Cultural': 'relaxed', 'Party & Fun': 'energetic', 'Romantic': 'romantic', 'Wellness & Detox': 'relaxed', 'Surprise me': 'relaxed' }
  const paceMap = { 'Fast & packed': 'packed', 'Balanced': 'balanced', 'Slow & easy': 'relaxed', 'Immersive': 'relaxed' }
  const durationMap = { 'Weekend (2–3 days)': 3, 'Short trip (4–6 days)': 5, '1 week': 7, '2 weeks': 14, '1 month+': 14 }
  const foodMap = { 'Vegetarian': 'vegetarian', 'Non-veg': 'any', 'Seafood': 'any', 'Vegan': 'vegan', 'Jain / No onion-garlic': 'vegetarian', 'Street food': 'any', 'Local cuisine': 'any', 'International': 'any' }

  const who = (quizAnswers.who || [])[0] || ''
  const qMood = (quizAnswers.mood || [])[0] || ''
  const qPace = (quizAnswers.pace || [])[0] || ''
  const qDuration = (quizAnswers.duration || [])[0] || ''
  const qFood = (quizAnswers.food || [])[0] || ''

  // Map quiz interests to planner interests
  const interestMap = { 'Adventure': 'adventure', 'Cultural': 'culture', 'Relaxation': 'nature', 'Party & Fun': 'nightlife', 'Romantic': 'culture', 'Wellness & Detox': 'nature', 'Surprise me': 'culture' }
  const sceneryMap = { 'Beaches': 'nature', 'Mountains': 'adventure', 'Forests': 'nature', 'Cities': 'shopping', 'Countryside': 'nature', 'Heritage': 'history', 'Deserts': 'adventure', 'Waterfalls': 'nature' }

  const mappedInterests = new Set()
  ;(quizAnswers.mood || []).forEach(m => { if (interestMap[m]) mappedInterests.add(interestMap[m]) })
  ;(quizAnswers.scenery || []).forEach(s => { if (sceneryMap[s]) mappedInterests.add(sceneryMap[s]) })
  if (mappedInterests.size === 0) { mappedInterests.add('culture'); mappedInterests.add('food') }

  return {
    partySize: whoMap[who] || 'couple',
    mood: moodMap[qMood] || 'relaxed',
    pace: paceMap[qPace] || 'balanced',
    duration: durationMap[qDuration] || 3,
    dietary: foodMap[qFood] || 'any',
    interests: [...mappedInterests],
    budget: (quizAnswers.style || ['Comfortable'])[0] === 'Backpacker' ? 300 : (quizAnswers.style || [])[0] === 'Luxury' ? 2000 : 800,
  }
}

export default function Planner({ onGenerated, itinerary, weather, quizAnswers, selectedDestination }) {
  const hasQuiz = quizAnswers && Object.keys(quizAnswers).length > 0
  const mapped = hasQuiz ? mapQuizToPlanner(quizAnswers) : null
  const initializedRef = useRef(false)

  // Start at step 1 (origin/dates) — skip steps 2-4 when quiz data is present
  const [step, setStep] = useState(1)
  const [originCity, setOriginCity] = useState('')
  const [city, setCity] = useState(selectedDestination || 'nyc')
  
  // Create a dynamic list of cities that includes the selected destination from the quiz
  const dynamicCities = [...CITIES]
  if (selectedDestination && !dynamicCities.find(c => c.key === selectedDestination)) {
    dynamicCities.unshift({ key: selectedDestination, label: selectedDestination, icon: '📍' })
  }
  
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [duration, setDuration] = useState(mapped?.duration || 3)
  const [budget, setBudget] = useState(mapped?.budget || 500)
  const [partySize, setPartySize] = useState(mapped?.partySize || 'couple')
  const [mood, setMood] = useState(mapped?.mood || 'relaxed')
  const [dietary, setDietary] = useState(mapped?.dietary || 'any')
  const [interests, setInterests] = useState(mapped?.interests || ['culture', 'food'])
  const [pace, setPace] = useState(mapped?.pace || 'balanced')

  // Set city when selectedDestination changes
  useEffect(() => {
    if (selectedDestination) {
      setCity(selectedDestination)
    }
  }, [selectedDestination])
  
  // Flight selection state
  const [outboundFlights, setOutboundFlights] = useState([])
  const [returnFlights, setReturnFlights] = useState([])
  const [selectedOutbound, setSelectedOutbound] = useState(null)
  const [selectedReturn, setSelectedReturn] = useState(null)
  const [flightLoading, setFlightLoading] = useState(false)
  const [flightError, setFlightError] = useState(null)
  
  // Hotel selection state
  const [hotels, setHotels] = useState([])
  const [selectedHotel, setSelectedHotel] = useState(null)
  const [hotelLoading, setHotelLoading] = useState(false)
  const [hotelError, setHotelError] = useState(null)  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const toggleInterest = (i) => {
    setInterests(prev =>
      prev.includes(i) ? prev.filter(x => x !== i) : [...prev, i]
    )
  }

  // Sync duration from date inputs
  useEffect(() => {
    if (startDate && endDate) {
      const diff = new Date(endDate) - new Date(startDate)
      const days = Math.ceil(diff / (1000 * 60 * 60 * 24))
      if (days >= 1 && days <= 14) setDuration(days)
    }
  }, [startDate, endDate])

  const handleSearchFlights = async () => {
    if (!originCity.trim()) {
      setFlightError('Please enter an origin city')
      return
    }
    setFlightLoading(true)
    setFlightError(null)
    setOutboundFlights([])
    setReturnFlights([])
    setSelectedOutbound(null)
    setSelectedReturn(null)

    try {
      const destLabel = CITIES.find(c => c.key === city)?.label || city
      
      const [outRes, retRes] = await Promise.all([
        searchFlights({ origin_city: originCity, destination_city: city, date: startDate }),
        searchFlights({ origin_city: city, destination_city: originCity, date: endDate })
      ])
      
      setOutboundFlights(outRes.flights || [])
      setReturnFlights(retRes.flights || [])
      
      if (!outRes.flights?.length && !retRes.flights?.length) {
        setFlightError('No flights found for this route.')
      }
    } catch (e) {
      setFlightError(e.message)
    }
    setFlightLoading(false)
  }

  const handleSearchHotels = async () => {
    setHotelLoading(true)
    setHotelError(null)
    setHotels([])
    setSelectedHotel(null)
    
    const durationSec = duration

    try {
      const res = await searchHotels({ city, nights: durationSec, budget, party_size: partySize, mood })
      setHotels(res.hotels || [])
      if (!res.hotels?.length) setHotelError('No hotels found matching your criteria.')
    } catch (e) {
      setHotelError(e.message)
    }
    setHotelLoading(false)
  }

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)
    
    const durationSec = duration

    try {
      const data = await generateItinerary({ 
          planner: {
              city, origin_city: originCity, budget, duration: durationSec, 
              start_date: startDate, end_date: endDate,
              party_size: partySize, mood, dietary_preference: dietary,
              interests, pace
          },
          selected_outbound: selectedOutbound,
          selected_return: selectedReturn,
          selected_hotel: selectedHotel,
      })
      onGenerated(data)
      setStep(7) // Results view
    } catch (e) {
      setError(e.message)
    }
    setLoading(false)
  }
  
  const resetPlanner = () => {
      onGenerated(null)
      setSelectedOutbound(null)
      setSelectedReturn(null)
      setSelectedHotel(null)
      setOutboundFlights([])
      setReturnFlights([])
      setHotels([])
      setStep(1)
  }

  const formatTime = (isoStr) => {
    if (!isoStr) return '--:--'
    const t = isoStr.split('T')[1]
    return t ? t.substring(0, 5) : '--:--'
  }

  const renderFlightCard = (flight, isSelected, onSelect) => (
    <div 
      key={`${flight.iata}${flight.flight_number}`}
      onClick={() => onSelect(flight)}
      style={{
        padding: '1rem',
        borderRadius: 12,
        border: isSelected ? '2px solid var(--gold)' : '1px solid var(--border)',
        background: isSelected ? 'rgba(232, 168, 56, 0.08)' : 'var(--surface)',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        marginBottom: 8,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontWeight: 600, fontSize: 15 }}>
            ✈️ {flight.carrier}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 2 }}>
            {flight.iata}{flight.flight_number} · {flight.dep_airport} → {flight.arr_airport}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontWeight: 700, fontSize: 18, color: 'var(--gold)' }}>
            ${flight.price}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-faint)' }}>
            {flight.class}
          </div>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 16, marginTop: 10, fontSize: 13, color: 'var(--text-dim)' }}>
        <span>🛫 {formatTime(flight.departure_time)}</span>
        <span style={{ color: 'var(--text-faint)' }}>→</span>
        <span>🛬 {formatTime(flight.arrival_time)}</span>
        <span style={{ marginLeft: 'auto', fontSize: 11 }}>{flight.duration_min}min</span>
      </div>
      {isSelected && (
        <div style={{ marginTop: 8, fontSize: 11, color: 'var(--gold)', fontWeight: 600 }}>
          ✓ Selected
        </div>
      )}
    </div>
  )

  const renderHotelCard = (hotel, isSelected, onSelect) => (
    <div 
      key={hotel.id}
      onClick={() => onSelect(hotel)}
      style={{
        padding: '1rem',
        borderRadius: 12,
        border: isSelected ? '2px solid var(--gold)' : '1px solid var(--border)',
        background: isSelected ? 'rgba(232, 168, 56, 0.08)' : 'var(--surface)',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        marginBottom: 8,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontWeight: 600, fontSize: 15 }}>
            🏨 {hotel.name}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 2 }}>
            {hotel.stars}★ {hotel.style} · {hotel.neighborhood}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontWeight: 700, fontSize: 18, color: 'var(--gold)' }}>
            ${hotel.total_price}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-faint)' }}>
            for {hotel.nights} nights
          </div>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 10 }}>
        {hotel.amenities.slice(0, 3).map(a => (
          <span key={a} style={{ fontSize: 10, background: 'var(--bg)', padding: '2px 6px', borderRadius: 4, color: 'var(--text-dim)' }}>
            {a}
          </span>
        ))}
        <span style={{ fontSize: 10, color: '#4CC9A0', border: '1px solid #4CC9A0', padding: '1px 5px', borderRadius: 4, marginLeft: 'auto' }}>
          {hotel.budget_fit}
        </span>
      </div>
      {isSelected && (
        <div style={{ marginTop: 8, fontSize: 11, color: 'var(--gold)', fontWeight: 600 }}>
          ✓ Selected
        </div>
      )}
    </div>
  )

  const renderWizardStep = () => {
      if (step === 1) {
          return (
              <div className="animate-in">
                  <div className="input-group">
                      <label className="input-label">Where are you flying from? (Origin)</label>
                      <input className="input" type="text" placeholder="e.g. London, San Francisco, Chicago" value={originCity} onChange={e => setOriginCity(e.target.value)} />
                  </div>
                  <div className="input-group" style={{ marginTop: '1.5rem' }}>
                      <label className="input-label">Where are we going?</label>
                      <select className="select" value={city} onChange={e => setCity(e.target.value)}>
                        {dynamicCities.map(c => (
                          <option key={c.key} value={c.key}>{c.icon} {c.label}</option>
                        ))}
                      </select>
                  </div>
                  <div style={{ display: 'flex', gap: 16, marginTop: '1.5rem' }}>
                      <div className="input-group" style={{ flex: 1 }}>
                          <label className="input-label">Start Date</label>
                          <input className="input" type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
                      </div>
                      <div className="input-group" style={{ flex: 1 }}>
                          <label className="input-label">End Date</label>
                          <input className="input" type="date" value={endDate} onChange={e => setEndDate(e.target.value)} />
                      </div>
                  </div>
                  <div className="input-group" style={{ marginTop: '1.5rem' }}>
                      <label className="input-label">Trip Duration (days)</label>
                      <input className="input" type="number" min={1} max={14} value={duration} onChange={e => setDuration(Math.min(14, Math.max(1, Number(e.target.value) || 1)))} />
                      <span style={{ fontSize: 11, color: 'var(--text-faint)', marginTop: 4, display: 'block' }}>Auto-calculated from dates. Max 14 days.</span>
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

      // Step 5: Flight Selection
      if (step === 5) {
          return (
              <div className="animate-in">
                  <div style={{ marginBottom: '1.5rem' }}>
                      <label className="input-label">Select Your Flights</label>
                      <p style={{ fontSize: 13, color: 'var(--text-dim)', marginTop: 4 }}>
                        Search for available flights between <strong>{originCity || 'Origin'}</strong> and <strong>{dynamicCities.find(c=>c.key===city)?.label || city}</strong>
                      </p>
                      <button className="btn btn-primary" onClick={handleSearchFlights} disabled={flightLoading} style={{ marginTop: 12, width: '100%' }}>
                        {flightLoading ? (
                          <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Searching flights...</>
                        ) : (
                          <>🔍 Search Available Flights</>
                        )}
                      </button>
                  </div>

                  {flightError && (
                    <div className="disruption-banner" style={{ marginBottom: '1rem' }}>
                      <div className="disruption-icon">⚠️</div>
                      <div><div className="disruption-text">{flightError}</div></div>
                    </div>
                  )}

                  {outboundFlights.length > 0 && (
                    <div style={{ marginBottom: '1.5rem' }}>
                      <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 8, color: 'var(--text)' }}>
                        🛫 Outbound Flights ({originCity} → {dynamicCities.find(c=>c.key===city)?.label || city})
                      </div>
                      {outboundFlights.map(f => renderFlightCard(
                        f,
                        selectedOutbound?.flight_number === f.flight_number && selectedOutbound?.carrier === f.carrier,
                        setSelectedOutbound
                      ))}
                    </div>
                  )}

                  {returnFlights.length > 0 && (
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 8, color: 'var(--text)' }}>
                        🛬 Return Flights ({dynamicCities.find(c=>c.key===city)?.label || city} → {originCity})
                      </div>
                      {returnFlights.map(f => renderFlightCard(
                        f,
                        selectedReturn?.flight_number === f.flight_number && selectedReturn?.carrier === f.carrier,
                        setSelectedReturn
                      ))}
                    </div>
                  )}

                  {(outboundFlights.length > 0 || returnFlights.length > 0) && !selectedOutbound && !selectedReturn && (
                    <p style={{ fontSize: 12, color: 'var(--text-faint)', textAlign: 'center', marginTop: 12 }}>
                      Tap a flight card to select it. You can skip flight selection to generate without flights.
                    </p>
                  )}
              </div>
          )
      }

      // Step 6: Hotel Selection
      if (step === 6) {
          return (
              <div className="animate-in">
                  <div style={{ marginBottom: '1.5rem' }}>
                      <label className="input-label">Select Your Hotel</label>
                      <p style={{ fontSize: 13, color: 'var(--text-dim)', marginTop: 4 }}>
                        Search for hotel recommendations in <strong>{CITIES.find(c=>c.key===city)?.label || city}</strong> tailored to a budget of <strong>${budget}</strong>.
                      </p>
                      <button className="btn btn-primary" onClick={handleSearchHotels} disabled={hotelLoading} style={{ marginTop: 12, width: '100%' }}>
                        {hotelLoading ? (
                          <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Finding top hotels...</>
                        ) : (
                          <>🔍 Find Perfect Hotels</>
                        )}
                      </button>
                  </div>

                  {hotelError && (
                    <div className="disruption-banner" style={{ marginBottom: '1rem' }}>
                      <div className="disruption-icon">⚠️</div>
                      <div><div className="disruption-text">{hotelError}</div></div>
                    </div>
                  )}

                  {hotels.length > 0 && (
                    <div style={{ marginBottom: '1.5rem' }}>
                      <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 8, color: 'var(--text)' }}>
                        🏨 Top Recommendations based on your budget & mood
                      </div>
                      {hotels.map(h => renderHotelCard(
                        h,
                        selectedHotel?.id === h.id,
                        setSelectedHotel
                      ))}
                    </div>
                  )}

                  {hotels.length > 0 && !selectedHotel && (
                    <p style={{ fontSize: 12, color: 'var(--text-faint)', textAlign: 'center', marginTop: 12 }}>
                      Tap a hotel card to select it. You can skip to generate without a hotel.
                    </p>
                  )}
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
                  {[1, 2, 3, 4, 5, 6].map(s => (
                      <div key={s} style={{ height: 4, flex: 1, borderRadius: 2, background: step >= s ? 'var(--gold)' : 'var(--surface)' }} />
                  ))}
              </div>

              <div className="planner-form" style={{ minHeight: 300, display: 'flex', flexDirection: 'column', justifyContent: step >= 5 ? 'flex-start' : 'center' }}>
                  {renderWizardStep()}
              </div>

              <div className="planner-actions" style={{ marginTop: '2rem', display: 'flex', justifyContent: 'space-between' }}>
                  <button className="btn btn-secondary" disabled={step === 1 || loading} onClick={() => setStep(s => hasQuiz && s === 5 ? 1 : s - 1)}>
                      Back
                  </button>
                  
                  {step < 6 ? (
                      <button className="btn btn-primary" onClick={() => setStep(s => hasQuiz && s === 1 ? 5 : s + 1)}>
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
                        <div style={{ fontSize: 12, fontWeight: 600, color: slot.metadata?.type === 'flight' ? '#8B5CF6' : 'var(--gold)' }}>{slot.start_time}</div>
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
                          
                          {slot.metadata?.type === 'flight' && (
                            <span style={{ fontSize: 10, color: '#8B5CF6', background: 'rgba(139, 92, 246, 0.1)', padding: '2px 6px', borderRadius: 4, border: '1px solid rgba(139, 92, 246, 0.3)' }}>
                              ✈️ {slot.metadata.carrier} {slot.metadata.flight_number}
                            </span>
                          )}
                          
                          {slot.metadata?.type === 'hotel' && (
                            <span style={{ fontSize: 10, color: '#F59E0B', background: 'rgba(245, 158, 11, 0.1)', padding: '2px 6px', borderRadius: 4, border: '1px solid rgba(245, 158, 11, 0.3)' }}>
                              🏨 Check-in
                            </span>
                          )}
                          
                          {slot.availability_status === 'Available' && !slot.metadata?.type && (
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
