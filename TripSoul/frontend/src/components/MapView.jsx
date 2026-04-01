import { useEffect, useRef } from 'react'
import L from 'leaflet'

export default function MapView({ itinerary }) {
  const mapRef = useRef(null)
  const mapInstance = useRef(null)
  const markersRef = useRef([])

  useEffect(() => {
    if (!mapRef.current || mapInstance.current) return

    // Initialize Leaflet map
    const map = L.map(mapRef.current, {
      zoomControl: true,
      attributionControl: false,
    }).setView([40.7128, -74.006], 12)

    // Dark tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
    }).addTo(map)

    mapInstance.current = map

    return () => {
      map.remove()
      mapInstance.current = null
    }
  }, [])

  useEffect(() => {
    if (!mapInstance.current || !itinerary?.days) return
    const map = mapInstance.current

    // Clear existing markers
    markersRef.current.forEach(m => map.removeLayer(m))
    markersRef.current = []

    const allCoords = []
    const dayColors = ['#E8A838', '#4CC9A0', '#5B8DEF', '#A78BFA', '#E05C5C']

    itinerary.days.forEach((day, dayIdx) => {
      const coords = []
      const color = dayColors[dayIdx % dayColors.length]

      day.slots.forEach((slot, slotIdx) => {
        const { lat, lng } = slot.activity
        allCoords.push([lat, lng])
        coords.push([lat, lng])

        // Custom marker
        const icon = L.divIcon({
          className: '',
          html: `<div style="
            width:28px;height:28px;border-radius:50%;
            background:${color};color:#080C14;
            display:flex;align-items:center;justify-content:center;
            font-size:12px;font-weight:700;
            border:2px solid #080C14;
            box-shadow:0 2px 8px rgba(0,0,0,0.4);
          ">${slotIdx + 1}</div>`,
          iconSize: [28, 28],
          iconAnchor: [14, 14],
        })

        const marker = L.marker([lat, lng], { icon }).addTo(map)
        marker.bindPopup(`
          <div style="font-family:'Inter',sans-serif;padding:4px 0">
            <div style="font-weight:600;font-size:13px;margin-bottom:4px">${slot.activity.name}</div>
            <div style="font-size:11px;color:#888;margin-bottom:4px">${slot.start_time} — ${slot.end_time}</div>
            <div style="font-size:11px;color:#666">${slot.activity.description}</div>
            ${slot.activity.cost > 0 ? `<div style="font-size:12px;color:#E8A838;margin-top:4px;font-weight:600">$${slot.activity.cost}</div>` : ''}
          </div>
        `)
        markersRef.current.push(marker)
      })

      // Route polyline between activities
      if (coords.length > 1) {
        const polyline = L.polyline(coords, {
          color,
          weight: 2.5,
          opacity: 0.6,
          dashArray: '8 6',
        }).addTo(map)
        markersRef.current.push(polyline)
      }
    })

    // Fit bounds
    if (allCoords.length > 0) {
      map.fitBounds(allCoords, { padding: [40, 40] })
    }
  }, [itinerary])

  return (
    <div className="animate-in">
      <div className="section-label">Interactive Map</div>
      <h2 className="section-title" style={{ marginBottom: '1rem' }}>
        Your trip visualized
      </h2>

      {itinerary && (
        <div style={{ display: 'flex', gap: 8, marginBottom: '1rem', flexWrap: 'wrap' }}>
          {itinerary.days?.map((day, i) => (
            <span key={i} className="tag tag-gold">
              Day {day.day}: {day.slots.length} stops
            </span>
          ))}
        </div>
      )}

      <div className="map-container" ref={mapRef} />

      {!itinerary && (
        <div className="empty-state" style={{ marginTop: '2rem' }}>
          <div className="empty-state-icon">🗺️</div>
          <div className="empty-state-title">No itinerary yet</div>
          <p>Generate an itinerary in the Planner tab to see it on the map.</p>
        </div>
      )}
    </div>
  )
}
