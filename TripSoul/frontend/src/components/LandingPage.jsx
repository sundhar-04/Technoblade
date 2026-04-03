/**
 * LandingPage — TripSoul's hero landing screen.
 * Ported from pr_05's index.html landing section.
 */
export default function LandingPage({ onStart }) {
  return (
    <section className="ts-landing">
      <div className="landing-eyebrow">
        <span></span>AI-powered travel intelligence
      </div>
      <h1 className="landing-title">
        Travel that<br /><em>understands you</em>
      </h1>
      <p className="landing-sub">
        Not where to go — but why. TripSoul reads your mood, maps your journey,
        and handles everything in between.
      </p>
      <button className="ts-btn-primary" onClick={onStart}>
        Begin your journey
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5"
            strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      <div className="landing-stats">
        <div className="stat-item">
          <div className="stat-num">10K+</div>
          <div className="stat-label">Routes mapped</div>
        </div>
        <div className="stat-item">
          <div className="stat-num">500+</div>
          <div className="stat-label">Destinations</div>
        </div>
        <div className="stat-item">
          <div className="stat-num">9</div>
          <div className="stat-label">Smart questions</div>
        </div>
      </div>
      <div className="landing-scroll-hint">
        <div className="scroll-line"></div>scroll
      </div>
    </section>
  )
}
