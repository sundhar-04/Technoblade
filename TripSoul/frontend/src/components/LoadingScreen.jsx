/**
 * LoadingScreen — Animated "Reading your soul…" loading state.
 * Ported from pr_05's loading section.
 */
import { useState, useEffect } from 'react'

const STEPS = [
  'Analysing your travel personality',
  'Matching mood to destinations',
  'Checking route logistics',
  'Building your itinerary',
]

export default function LoadingScreen() {
  const [activeStep, setActiveStep] = useState(0)
  const [doneSteps, setDoneSteps] = useState([])

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep(prev => {
        if (prev > 0) {
          setDoneSteps(d => [...d, prev - 1])
        }
        if (prev < STEPS.length) return prev + 1
        clearInterval(interval)
        return prev
      })
    }, 900)
    return () => clearInterval(interval)
  }, [])

  return (
    <section className="ts-loading-screen">
      <div className="ts-loading-icon"></div>
      <div className="ts-loading-title">Reading your soul…</div>
      <div className="ts-loading-sub">
        Our AI is matching your mood to the perfect destinations.
      </div>
      <div className="ts-loading-steps">
        {STEPS.map((step, i) => (
          <div
            key={i}
            className={`ts-loading-step ${
              doneSteps.includes(i) ? 'done' : activeStep === i ? 'active' : ''
            }`}
          >
            <div className="ts-loading-step-dot"></div>
            {step}
          </div>
        ))}
      </div>
    </section>
  )
}
