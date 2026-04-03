import { useState, useEffect } from 'react'
import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import LandingPage from './components/LandingPage'
import Quiz from './components/Quiz'
import LoadingScreen from './components/LoadingScreen'
import Results from './components/Results'
import Handbook from './components/Handbook'
import Planner from './components/Planner'
import MapView from './components/MapView'
import Timeline from './components/Timeline'
import BudgetOptimizer from './components/BudgetOptimizer'
import Decisions from './components/Decisions'
import DisruptionBanner from './components/DisruptionBanner'
import { connectSSE, recommend } from './api/client'

// App phases: landing → quiz → loading → results → planner
const PHASE = { LANDING: 0, QUIZ: 1, LOADING: 2, RESULTS: 3, PLANNER: 4 }

// Local fallback destinations (from pr_05)
const FALLBACK_DESTINATIONS = [
  { name: 'Spiti Valley', state: 'Himachal Pradesh', icon: '🏔️', img: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=75', mood: ['Adventure', 'Relaxation', 'Wellness & Detox'], region: ['North India', 'Anywhere'], season: ['Summer', 'Any season'], tags: ['Off-beat', 'High altitude', 'Spiritual'], reason: 'Stark lunar landscapes and Buddhist monasteries. Perfect for deep reflection and mental reset.', itinerary_hint: 'Shared jeep from Manali, homestays in Kaza, Dhankar monastery hike, local thukpa.' },
  { name: 'Goa', state: 'Goa', icon: '🏖️', img: 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800&q=75', mood: ['Party & Fun', 'Relaxation', 'Romantic'], region: ['West India', 'Anywhere'], season: ['Winter', 'Any season'], tags: ['Beach', 'Nightlife', 'Food'], reason: 'Sun-soaked beaches, Portuguese architecture, vibrant nightlife and legendary seafood.', itinerary_hint: 'Anjuna beach mornings, scooter to Fontainhas, shack dinners, Saturday Night Market.' },
  { name: 'Munnar', state: 'Kerala', icon: '🌿', img: 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=800&q=75', mood: ['Relaxation', 'Romantic', 'Cultural', 'Wellness & Detox'], region: ['South India', 'Anywhere'], season: ['Winter', 'Monsoon', 'Any season'], tags: ['Tea estates', 'Romantic', 'Misty'], reason: 'Rolling tea estates draped in mist. The kind of place where you forget your phone exists.', itinerary_hint: 'Estate homestay, tea factory visit, Eravikulam day trip, Kerala thali evenings.' },
  { name: 'Varanasi', state: 'Uttar Pradesh', icon: '🔎', img: 'https://images.unsplash.com/photo-1561361058-c24cecae35ca?w=800&q=75', mood: ['Cultural', 'Relaxation'], region: ['North India', 'Anywhere'], season: ['Winter', 'Any season'], tags: ['Spiritual', 'Heritage', 'Ancient'], reason: 'The oldest living city on earth. Ghats, Ganga aartis and a spiritual intensity unlike anywhere else.', itinerary_hint: 'Dawn boat ride, kachori breakfast, Sarnath day trip, sunset Ganga aarti.' },
  { name: 'Ladakh', state: 'Jammu & Kashmir', icon: '🏔️', img: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=75', mood: ['Adventure', 'Romantic'], region: ['North India', 'Anywhere'], season: ['Summer', 'Any season'], tags: ['Adventure', 'Road trip', 'Remote'], reason: 'High-altitude desert with turquoise lakes and roads that feel like the edge of the world.', itinerary_hint: 'Flight to Leh, Royal Enfield rental, Nubra Valley + Pangong circuit, monastery stops.' },
  { name: 'Hampi', state: 'Karnataka', icon: '🏛️', img: 'https://images.unsplash.com/photo-1600697230061-c7e84c7f0e46?w=800&q=75', mood: ['Cultural', 'Adventure'], region: ['South India', 'Anywhere'], season: ['Winter', 'Any season'], tags: ['Ruins', 'Heritage', 'Boulders'], reason: 'Ancient Vijayanagara ruins across a surreal boulder landscape.', itinerary_hint: 'Bicycle the ruins, Vittala Temple sunrise, boulder scramble, coracle river crossing.' },
]

function getLocalRecs(payload, shownPlaces) {
  const moods = payload.mood || []
  const region = (payload.region || ['Anywhere'])[0]
  const seasons = payload.season || []

  return FALLBACK_DESTINATIONS
    .map(d => {
      let score = 0
      moods.forEach(m => { if (d.mood.includes(m)) score += 3 })
      if (d.region.includes(region) || d.region.includes('Anywhere')) score += 2
      seasons.forEach(s => { if (d.season.includes(s) || d.season.includes('Any season')) score += 2 })
      score += Math.random() * 0.5
      return { ...d, score }
    })
    .sort((a, b) => b.score - a.score)
    .filter(d => !shownPlaces.includes(d.name))
    .slice(0, 3)
}

export default function App() {
  const [phase, setPhase] = useState(PHASE.LANDING)
  const [quizAnswers, setQuizAnswers] = useState({})
  const [recommendations, setRecommendations] = useState([])
  const [shownPlaces, setShownPlaces] = useState([])
  const [handbookCity, setHandbookCity] = useState(null)

  // Planner state (from sun_04)
  const [itinerary, setItinerary] = useState(null)
  const [weather, setWeather] = useState(null)
  const [disruption, setDisruption] = useState(null)
  const [decisions, setDecisions] = useState([])
  const [hasDisruption, setHasDisruption] = useState(false)
  const location = useLocation()

  const handleItineraryGenerated = (data) => {
    if (!data) {
      setItinerary(null)
      setWeather(null)
      return
    }
    setItinerary(data.itinerary)
    setWeather(data.weather)
    setDisruption(null)
    setHasDisruption(false)
    setDecisions(prev => [{
      type: 'info',
      title: `Itinerary generated for ${data.itinerary.city.toUpperCase()}`,
      reason: data.itinerary.reasoning,
      time: new Date().toLocaleTimeString(),
    }, ...prev])
  }

  const handleOptimized = (data) => {
    setItinerary(data.itinerary)
    setDecisions(prev => [{
      type: 'info',
      title: 'Budget re-optimized',
      reason: data.pareto_notes,
      time: new Date().toLocaleTimeString(),
    }, ...prev])
  }

  // Quiz complete → fetch AI recommendations
  const handleQuizComplete = async (answers) => {
    setQuizAnswers(answers)
    setPhase(PHASE.LOADING)

    const payload = {
      mood: answers.mood || [],
      who: answers.who || [],
      pace: answers.pace || [],
      style: answers.style || ['Comfortable'],
      duration: answers.duration || [],
      scenery: answers.scenery || [],
      food: answers.food || [],
      season: answers.season || [],
      region: answers.region || ['Anywhere'],
      notes: answers.notes || '',
      exclude: shownPlaces,
    }

    const loadStart = Date.now()
    let recs = null

    try {
      const data = await recommend(payload)
      recs = data.recommendations
      console.log('✅ AI recommendations received:', recs)
    } catch (err) {
      console.warn('⚠️ API error, using local fallback:', err.message)
      recs = getLocalRecs(payload, shownPlaces)
    }

    // Wait for min loading animation
    const elapsed = Date.now() - loadStart
    const waitLeft = Math.max(0, 3600 - elapsed)

    setTimeout(() => {
      setRecommendations(recs)
      setShownPlaces(prev => [...new Set([...prev, ...recs.map(d => d.name)])])
      setPhase(PHASE.RESULTS)
    }, waitLeft + 400)
  }

  // Refine = get different suggestions
  const handleRefine = () => {
    handleQuizComplete(quizAnswers)
  }

  // Restart = back to landing
  const handleRestart = () => {
    setPhase(PHASE.LANDING)
    setQuizAnswers({})
    setShownPlaces([])
    setRecommendations([])
  }

  // Plan trip = transition to planner
  const handlePlanTrip = () => {
    setPhase(PHASE.PLANNER)
  }

  // ─── Landing / Quiz / Loading / Results flow ───
  if (phase === PHASE.LANDING) {
    return <LandingPage onStart={() => setPhase(PHASE.QUIZ)} />
  }

  if (phase === PHASE.QUIZ) {
    return <Quiz onComplete={handleQuizComplete} />
  }

  if (phase === PHASE.LOADING) {
    return <LoadingScreen />
  }

  if (phase === PHASE.RESULTS) {
    return (
      <>
        <Results
          answers={quizAnswers}
          recommendations={recommendations}
          onRestart={handleRestart}
          onRefine={handleRefine}
          onPlanTrip={handlePlanTrip}
          onOpenHandbook={city => setHandbookCity(city)}
        />
        {handbookCity && (
          <Handbook city={handbookCity} onClose={() => setHandbookCity(null)} />
        )}
      </>
    )
  }

  // ─── Planner phase (sun_04 UI) ───
  const navItems = [
    { to: '/', label: 'Planner', icon: '🧠' },
    { to: '/map', label: 'Map', icon: '🗺️' },
    { to: '/timeline', label: 'Timeline', icon: '📅' },
    { to: '/budget', label: 'Budget', icon: '💰' },
    { to: '/decisions', label: 'Decisions', icon: '⚡' },
  ]

  return (
    <div className="app-layout">
      <nav className="navbar">
        <a href="#" className="nav-logo" onClick={e => { e.preventDefault(); handleRestart() }}>
          Trip<span>Soul</span>
          <span className="nav-logo-tag">AI OS</span>
        </a>
        <div className="nav-links">
          {navItems.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              {item.label}
              {item.label === 'Decisions' && hasDisruption && (
                <span className="nav-disruption-dot" />
              )}
            </NavLink>
          ))}
        </div>
      </nav>

      <main className="main-content">
        {disruption && <DisruptionBanner disruption={disruption} />}

        <Routes>
          <Route path="/" element={
            <Planner
              onGenerated={handleItineraryGenerated}
              itinerary={itinerary}
              weather={weather}
              quizAnswers={quizAnswers}
              selectedDestination={recommendations?.[0]?.name || ''}
            />
          } />
          <Route path="/map" element={
            <MapView itinerary={itinerary} />
          } />
          <Route path="/timeline" element={
            <Timeline itinerary={itinerary} setItinerary={setItinerary} />
          } />
          <Route path="/budget" element={
            <BudgetOptimizer
              itinerary={itinerary}
              onOptimized={handleOptimized}
            />
          } />
          <Route path="/decisions" element={
            <Decisions
              decisions={decisions}
              itinerary={itinerary}
              onSimulate={(data) => {
                if (data?.disruption) {
                  setDisruption(data)
                  setHasDisruption(true)
                  if (data.adapted_plan) setItinerary(data.adapted_plan)
                }
              }}
            />
          } />
        </Routes>
      </main>
    </div>
  )
}
