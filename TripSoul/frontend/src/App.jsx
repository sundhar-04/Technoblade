import { useState, useEffect } from 'react'
import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import Planner from './components/Planner'
import MapView from './components/MapView'
import Timeline from './components/Timeline'
import BudgetOptimizer from './components/BudgetOptimizer'
import Decisions from './components/Decisions'
import DisruptionBanner from './components/DisruptionBanner'
import { connectSSE } from './api/client'

export default function App() {
  const [itinerary, setItinerary] = useState(null)
  const [weather, setWeather] = useState(null)
  const [disruption, setDisruption] = useState(null)
  const [decisions, setDecisions] = useState([])
  const [hasDisruption, setHasDisruption] = useState(false)
  const location = useLocation()

  // SSE connection for live adaptation updates
  useEffect(() => {
    // Disabled temporary
  }, [])

  const handleItineraryGenerated = (data) => {
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
        <a href="/" className="nav-logo">
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
