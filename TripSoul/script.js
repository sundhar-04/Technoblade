/* ============================================================
   QUESTIONS
============================================================ */

// FIX #1 (HIGH): shownPlaces must be initialised from any previously seen results
// so the exclude list is populated BEFORE the first API call, not after.
// Previously shownPlaces was only updated inside renderResultCards (too late).
// Now it is the single source of truth — prevShown is removed (Fix #8 medium).
// API base URL — update this if your backend runs on a different port
const API_URL = 'http://127.0.0.1:8000';

let shownPlaces = [];

const QUESTIONS = [
  {
    id: 'mood', label: 'Travel mood',
    question: "What's your travel mood right now?",
    hint: 'Pick one or more — you can want adventure and culture at once.',
    type: 'cards', cols: 'cols-3', multi: true,
    options: [
      { icon: '🧗', title: 'Adventure', desc: 'Thrill, challenge, the unknown' },
      { icon: '🛶', title: 'Relaxation', desc: 'Unwind, reset, breathe' },
      { icon: '🕌', title: 'Cultural', desc: 'History, heritage, spiritual' },
      { icon: '🎉', title: 'Party & Fun', desc: 'Energy, nightlife, people' },
      { icon: '💕', title: 'Romantic', desc: 'Intimate, scenic, special' },
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
      { icon: '👯', title: 'Friends' },
      { icon: '👨‍👩‍👧', title: 'Family' },
      { icon: '🐾', title: 'With pets' },
      { icon: '🏢', title: 'Group / Team' },
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
      { icon: '💧', title: 'Waterfalls', desc: 'Cascades, gorges, mist' },
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
      { icon: '🍢', title: 'Street food', desc: 'Chaat, hawkers, local stalls' },
      { icon: '🍛', title: 'Local cuisine', desc: 'Regional specialties' },
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
      { icon: '🌊', title: 'East India' },
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
];

/* ============================================================
   LOCAL DESTINATION FALLBACK (used if API is down)
============================================================ */
const DESTINATIONS = [
  { name: 'Spiti Valley', state: 'Himachal Pradesh', icon: '🏔️', img: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=75', mood: ['Adventure', 'Relaxation', 'Wellness & Detox', 'Surprise me'], region: ['North India', 'Anywhere'], season: ['Summer', 'Any season'], tags: ['Off-beat', 'High altitude', 'Spiritual'], reason: 'Stark lunar landscapes and Buddhist monasteries. Perfect for deep reflection and mental reset.', itinerary_hint: 'Shared jeep from Manali, homestays in Kaza, Dhankar monastery hike, local thukpa.' },
  { name: 'Goa', state: 'Goa', icon: '🏖️', img: 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800&q=75', mood: ['Party & Fun', 'Relaxation', 'Romantic', 'Surprise me'], region: ['West India', 'Anywhere'], season: ['Winter', 'Any season'], tags: ['Beach', 'Nightlife', 'Food'], reason: 'Sun-soaked beaches, Portuguese architecture, vibrant nightlife and legendary seafood.', itinerary_hint: 'Anjuna beach mornings, scooter to Fontainhas, shack dinners, Saturday Night Market.' },
  { name: 'Munnar', state: 'Kerala', icon: '🌿', img: 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=800&q=75', mood: ['Relaxation', 'Romantic', 'Cultural', 'Wellness & Detox'], region: ['South India', 'Anywhere'], season: ['Winter', 'Monsoon', 'Any season'], tags: ['Tea estates', 'Romantic', 'Misty'], reason: 'Rolling tea estates draped in mist. The kind of place where you forget your phone exists.', itinerary_hint: 'Estate homestay, tea factory visit, Eravikulam day trip, Kerala thali evenings.' },
  { name: 'Varanasi', state: 'Uttar Pradesh', icon: '🕌', img: 'https://images.unsplash.com/photo-1561361058-c24cecae35ca?w=800&q=75', mood: ['Cultural', 'Relaxation', 'Surprise me'], region: ['North India', 'Anywhere'], season: ['Winter', 'Any season'], tags: ['Spiritual', 'Heritage', 'Ancient'], reason: 'The oldest living city on earth. Ghats, Ganga aartis and a spiritual intensity unlike anywhere else.', itinerary_hint: 'Dawn boat ride, kachori breakfast, Sarnath day trip, sunset Ganga aarti.' },
  { name: 'Ladakh', state: 'Jammu & Kashmir', icon: '🏔️', img: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=75', mood: ['Adventure', 'Romantic', 'Surprise me'], region: ['North India', 'Anywhere'], season: ['Summer', 'Any season'], tags: ['Adventure', 'Road trip', 'Remote'], reason: 'High-altitude desert with turquoise lakes and roads that feel like the edge of the world.', itinerary_hint: 'Flight to Leh, Royal Enfield rental, Nubra Valley + Pangong circuit, monastery stops.' },
  { name: 'Coorg', state: 'Karnataka', icon: '☕', img: 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&q=75', mood: ['Relaxation', 'Romantic', 'Cultural', 'Wellness & Detox'], region: ['South India', 'Anywhere'], season: ['Winter', 'Monsoon', 'Any season'], tags: ['Coffee', 'Romantic', 'Hills'], reason: "India's coffee country. Misty hills, waterfalls, and homestays where breakfast smells like arabica.", itinerary_hint: 'Coffee estate stay, Abbey Falls, Nagarhole day trip, craft brewery evening.' },
  { name: 'Rajasthan', state: 'Rajasthan', icon: '🏜️', img: 'https://images.unsplash.com/photo-1477587458883-47145ed31672?w=800&q=75', mood: ['Cultural', 'Adventure', 'Romantic'], region: ['West India', 'North India', 'Anywhere'], season: ['Winter', 'Any season'], tags: ['Heritage', 'Forts', 'Desert'], reason: "Forts, palaces, camels and a colour palette straight out of a painting.", itinerary_hint: 'Jaipur → Jaisalmer train, haveli hotel, camel safari, rooftop dal baati dinner.' },
  { name: 'Andaman Islands', state: 'Andaman & Nicobar', icon: '🌊', img: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800&q=75', mood: ['Adventure', 'Relaxation', 'Romantic'], region: ['East India', 'Anywhere'], season: ['Winter', 'Any season'], tags: ['Island', 'Diving', 'Pristine'], reason: 'Coral reefs, bioluminescent beaches, and some of the clearest water in Asia.', itinerary_hint: 'Flight + ferry to Havelock, snorkelling at Radhanagar, kayaking, beach bonfires.' },
  { name: 'Meghalaya', state: 'Meghalaya', icon: '🌧️', img: 'https://images.unsplash.com/photo-1564507592333-c60657eea523?w=800&q=75', mood: ['Adventure', 'Cultural', 'Surprise me'], region: ['Northeast India', 'Anywhere'], season: ['Monsoon', 'Summer', 'Any season'], tags: ['Off-beat', 'Waterfalls', 'Caves'], reason: 'Living root bridges, the wettest place on earth, and waterfalls barely on any tourist map.', itinerary_hint: 'Shillong base, Cherrapunji day, double-decker root bridge trek, Dawki river kayak.' },
  { name: 'Hampi', state: 'Karnataka', icon: '🏛️', img: 'https://images.unsplash.com/photo-1600697230061-c7e84c7f0e46?w=800&q=75', mood: ['Cultural', 'Adventure', 'Surprise me'], region: ['South India', 'Anywhere'], season: ['Winter', 'Any season'], tags: ['Ruins', 'Heritage', 'Boulders'], reason: 'Ancient Vijayanagara ruins across a surreal boulder landscape.', itinerary_hint: 'Bicycle the ruins, Vittala Temple sunrise, boulder scramble, coracle river crossing.' },
  { name: 'Rishikesh', state: 'Uttarakhand', icon: '🧘', img: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=75', mood: ['Wellness & Detox', 'Adventure', 'Cultural', 'Relaxation'], region: ['North India', 'Anywhere'], season: ['Winter', 'Summer', 'Any season'], tags: ['Yoga', 'Wellness', 'River'], reason: 'The yoga capital of the world. White-water rafting at dawn, sunset aarti on the Ganga.', itinerary_hint: 'Ashram stay, morning yoga, Ganga aarti, bungee jumping, riverside café evenings.' },
];

/* ============================================================
   SOUL PANEL TEXT MAPS
============================================================ */
const MOOD_LINE = {
  'Adventure': 'a craving for the unknown and raw challenge',
  'Relaxation': 'a deep need to slow down, breathe, and just be',
  'Cultural': 'a hunger for depth, meaning, and living heritage',
  'Party & Fun': 'a hunger for energy, people, and great stories',
  'Romantic': 'a desire for intimate and beautiful shared moments',
  'Wellness & Detox': 'a call to heal, restore, and come back to yourself',
  'Surprise me': 'an open, curious spirit ready for anything',
};
const PACE_LINE = {
  'Fast & packed': 'you want every single hour to count',
  'Balanced': 'you move at your own unhurried rhythm',
  'Slow & easy': 'you believe travel is about being, not rushing',
  'Immersive': 'you go deep — not wide',
};
const WHO_LINE = {
  'Solo escape': 'travelling alone means freedom without compromise',
  'Couple': 'this journey is about shared memory-making',
  'Friends': 'the best stories need the right people beside you',
  'Family': 'every moment here is a chance to connect deeply',
  'With pets': 'your best travel companion comes with four paws',
  'Group / Team': 'shared experiences build the strongest bonds',
};

/* ============================================================
   STATE
============================================================ */
let currentQ = 0;
let answers = {};
// NOTE: prevShown removed — shownPlaces is the single source of truth (Fix #8)

/* ============================================================
   SCREEN NAVIGATION
============================================================ */
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
  document.getElementById(id).classList.remove('hidden');
  window.scrollTo(0, 0);
}

function startJourney() {
  currentQ = 0;
  answers = {};
  showScreen('screen-quiz');
  buildSidebar();
  renderQuestion(0);
}

function restartQuiz() {
  currentQ = 0;
  answers = {};
  shownPlaces = []; // FIX #1: also reset exclusion list on full restart
  showScreen('screen-landing');
}

/* ============================================================
   SIDEBAR
============================================================ */
function buildSidebar() {
  document.getElementById('sidebar-steps').innerHTML = QUESTIONS.map((q, i) => `
    <div class="sidebar-step ${i === 0 ? 'active' : ''}" id="sstep-${i}">
      <div class="step-dot">${i + 1}</div>
      <div class="step-label">${q.label}</div>
    </div>
  `).join('');
}

function updateSidebar(idx) {
  QUESTIONS.forEach((_, i) => {
    const el = document.getElementById(`sstep-${i}`);
    if (!el) return;
    el.classList.remove('active', 'done');
    if (i < idx) el.classList.add('done');
    else if (i === idx) el.classList.add('active');
  });
  document.getElementById('sidebar-fill').style.width =
    Math.round((idx / QUESTIONS.length) * 100) + '%';
  const mob = document.getElementById('mobile-progress-label');
  if (mob) mob.textContent = `${idx + 1} / ${QUESTIONS.length}`;
}

/* ============================================================
   RENDER QUESTION
============================================================ */
function renderQuestion(idx) {
  const q = QUESTIONS[idx];
  updateSidebar(idx);

  const area = document.getElementById('quiz-main-area');
  area.innerHTML = '';

  const wrap = document.createElement('div');
  wrap.className = 'animate-in';

  wrap.innerHTML = `
    <div class="quiz-q-counter">Question ${idx + 1} of ${QUESTIONS.length}</div>
    <h2 class="quiz-question">${q.question}</h2>
    <p class="quiz-hint">${q.hint}</p>
  `;

  // Build input
  if (q.type === 'cards') wrap.appendChild(buildCards(q, idx));
  else if (q.type === 'pills') wrap.appendChild(buildPills(q, idx));
  else if (q.type === 'textarea') wrap.appendChild(buildTextarea(q, idx));

  // Nav
  const nav = document.createElement('div');
  nav.className = 'quiz-nav';

  const backBtn = document.createElement('button');
  backBtn.className = 'btn-nav-back';
  backBtn.disabled = idx === 0;
  backBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M10 7H4M6 4L3 7l3 3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg> Back`;
  backBtn.onclick = () => { if (idx > 0) renderQuestion(--currentQ); };

  const isLast = idx === QUESTIONS.length - 1;
  const nextBtn = document.createElement('button');
  nextBtn.className = 'btn-nav-next';
  nextBtn.id = 'next-btn';
  nextBtn.innerHTML = isLast
    ? `Find my destinations <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 7h10M8 3l4 4-4 4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>`
    : `Next <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 7h10M8 3l4 4-4 4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  nextBtn.onclick = () => {
    if (idx < QUESTIONS.length - 1) renderQuestion(++currentQ);
    else showResults();
  };

  nav.appendChild(backBtn);
  nav.appendChild(nextBtn);
  wrap.appendChild(nav);
  area.appendChild(wrap);
  updateNextBtn(idx);
}

/* ── CARD INPUT ── */
function buildCards(q, idx) {
  const grid = document.createElement('div');
  grid.className = `options-grid ${q.cols || 'cols-3'}`;

  q.options.forEach(opt => {
    const card = document.createElement('div');
    card.className = 'option-card';
    if ((answers[q.id] || []).includes(opt.title)) card.classList.add('selected');

    card.innerHTML = `
      <div class="option-check"><svg viewBox="0 0 10 10" fill="none"><path d="M2 5l2.5 2.5L8 3" stroke="#0B0F1A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
      <div class="option-icon">${opt.icon}</div>
      <div class="option-title">${opt.title}</div>
      ${opt.desc ? `<div class="option-desc">${opt.desc}</div>` : ''}
    `;

    card.onclick = () => {
      if (q.multi) {
        toggleAnswer(q.id, opt.title);
        card.classList.toggle('selected');
      } else {
        setAnswer(q.id, opt.title);
        grid.querySelectorAll('.option-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
      }
      updateNextBtn(idx);
    };

    grid.appendChild(card);
  });
  return grid;
}

/* ── PILL INPUT ── */
function buildPills(q, idx) {
  const wrap = document.createElement('div');
  wrap.className = 'options-pills';

  q.options.forEach(opt => {
    const pill = document.createElement('div');
    pill.className = 'option-pill';
    if ((answers[q.id] || []).includes(opt.title)) pill.classList.add('selected');
    pill.innerHTML = `<span>${opt.icon}</span> ${opt.title}`;

    pill.onclick = () => {
      if (q.multi) {
        toggleAnswer(q.id, opt.title);
        pill.classList.toggle('selected');
      } else {
        setAnswer(q.id, opt.title);
        wrap.querySelectorAll('.option-pill').forEach(p => p.classList.remove('selected'));
        pill.classList.add('selected');
      }
      updateNextBtn(idx);
    };

    wrap.appendChild(pill);
  });
  return wrap;
}

/* ── TEXTAREA INPUT ── */
function buildTextarea(q, idx) {
  const taWrap = document.createElement('div');
  taWrap.className = 'notes-wrap';

  const ta = document.createElement('textarea');
  ta.className = 'notes-textarea';
  ta.placeholder = q.placeholder || 'Type anything here…';
  ta.rows = 5;
  ta.value = answers[q.id] || '';

  const counter = document.createElement('div');
  counter.className = 'notes-counter';
  counter.textContent = `${ta.value.length} / 300`;

  ta.oninput = () => {
    if (ta.value.length > 300) ta.value = ta.value.slice(0, 300);
    counter.textContent = `${ta.value.length} / 300`;
    answers[q.id] = ta.value.trim();
  };

  const optLabel = document.createElement('div');
  optLabel.className = 'notes-optional-label';
  optLabel.textContent = 'Optional — skip if nothing to add';

  taWrap.appendChild(ta);
  taWrap.appendChild(counter);
  taWrap.appendChild(optLabel);
  return taWrap;
}

/* ── NEXT BUTTON STATE ── */
function updateNextBtn(idx) {
  const btn = document.getElementById('next-btn');
  if (!btn) return;
  const q = QUESTIONS[idx];
  if (q.optional || q.type === 'textarea') { btn.disabled = false; return; }
  btn.disabled = (answers[q.id] || []).length === 0;
}

/* ============================================================
   ANSWER HELPERS
============================================================ */
function setAnswer(id, val) { answers[id] = [val]; }
function toggleAnswer(id, val) {
  answers[id] = answers[id] || [];
  const i = answers[id].indexOf(val);
  if (i === -1) answers[id].push(val); else answers[id].splice(i, 1);
}

/* ============================================================
   SHOW RESULTS — single async function, no duplicate
============================================================ */
async function showResults() {
  showScreen('screen-loading');

  // FIX #6 (medium — included for correctness): track real elapsed time
  const loadStart = Date.now();

  const stepIds = ['lstep-0', 'lstep-1', 'lstep-2', 'lstep-3'];
  let stepIdx = 0;
  const stepTimer = setInterval(() => {
    if (stepIdx > 0) {
      document.getElementById(stepIds[stepIdx - 1]).classList.remove('active');
      document.getElementById(stepIds[stepIdx - 1]).classList.add('done');
    }
    if (stepIdx < stepIds.length) {
      document.getElementById(stepIds[stepIdx]).classList.add('active');
      stepIdx++;
    } else {
      clearInterval(stepTimer);
    }
  }, 900);

  const style = (answers.style || ['Comfortable'])[0];

  // FIX #1 (HIGH): shownPlaces is already populated from previous renders,
  // so exclude list is correct even on the very first "Refine" call.
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
    exclude: shownPlaces,        // ← always up-to-date at call time
  };

  let recs = null;

  try {
    const response = await fetch(`${API_URL}/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!response.ok) throw new Error('Server error ' + response.status);
    const data = await response.json();
    recs = data.recommendations;
    console.log('✅ AI recommendations received:', recs);
  } catch (err) {
    const isConnRefused = err.message.includes('Failed to fetch') || err.message.includes('ERR_CONNECTION_REFUSED');
    if (isConnRefused) {
      console.error('❌ Cannot reach backend at', API_URL, '— is uvicorn running? (python -m uvicorn backend:app --reload)');
    } else {
      console.warn('⚠️ API error:', err.message);
    }
    recs = getLocalRecs(payload);
  }

  // FIX #6: use real elapsed time, not stepIdx approximation
  const minLoadTime = stepIds.length * 900;
  const elapsed = Date.now() - loadStart;
  const waitLeft = Math.max(0, minLoadTime - elapsed);

  setTimeout(() => {
    clearInterval(stepTimer);
    renderSoulPanel(payload, recs[0]);
    renderStyleBanner(style, answers.notes || '');
    renderResultCards(recs, style);  // shownPlaces updated here, ready for next call
    showScreen('screen-results');
  }, waitLeft + 400);
}

/* ── LOCAL SCORING FALLBACK ── */
// FIX #7/#8: uses shownPlaces (single source of truth) instead of removed prevShown
function getLocalRecs(payload) {
  const moods = payload.mood;
  const region = payload.region[0] || '';
  const seasons = payload.season;

  const scored = DESTINATIONS.map(d => {
    let score = 0;
    moods.forEach(m => { if (d.mood.includes(m)) score += 3; });
    if (d.region.includes(region) || d.region.includes('Anywhere')) score += 2;
    seasons.forEach(s => { if ((d.season || []).includes(s) || (d.season || []).includes('Any season')) score += 2; });
    score += Math.random() * 0.5;
    return { ...d, score };
  }).sort((a, b) => b.score - a.score);

  // Filter out already-shown places using the single shared list
  return scored.filter(d => !shownPlaces.includes(d.name)).slice(0, 3);
}

/* ============================================================
   SOUL PANEL — WOW FEATURE
============================================================ */
function renderSoulPanel(payload, topDest) {
  const mood = (payload.mood || [])[0] || '';
  const who = (payload.who || [])[0] || '';
  const pace = (payload.pace || [])[0] || '';
  const sc = (payload.scenery || [])[0] || '';

  // Trait chips
  const traits = [];
  if (mood) traits.push(mood + ' seeker');
  if (who) traits.push(who);
  if (pace) traits.push(pace + ' pace');
  if (sc) traits.push(sc + ' lover');

  document.getElementById('soul-traits').innerHTML = traits.map(t =>
    `<div class="soul-trait"><div class="trait-dot"></div>${t}</div>`
  ).join('');

  // Build explanation
  const destName = topDest ? (topDest.name || '') : 'your destination';
  const ml = MOOD_LINE[mood] || 'a sense of wanderlust';
  const pl = PACE_LINE[pace] || 'travelling your way';
  const wl = who ? `As someone where ${WHO_LINE[who] || 'on this journey'}, ` : '';
  const sl = sc ? `Your draw to ${sc.toLowerCase()} seals it — ` : '';

  const text = `You came in with ${ml}, and ${pl}. ${sl}${destName} offers exactly what you're looking for. ${wl}this is a trip that will stay with you.`;

  typewriter(document.getElementById('soul-explanation-text'), text, destName);
}

// FIX #12 (medium — included as it touches this function): escape regex special chars in highlight
function typewriter(el, text, highlight) {
  el.innerHTML = '';
  let i = 0;
  // Escape any regex special characters in the destination name
  const safeHighlight = highlight
    ? highlight.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    : null;

  function tick() {
    if (i < text.length) {
      const chunk = text.substring(0, i + 1);
      el.innerHTML = safeHighlight
        ? chunk.replace(new RegExp(`\\b${safeHighlight}\\b`, 'g'), `<span class="hl">${highlight}</span>`)
        : chunk;
      el.innerHTML += '<span class="typing-cursor"></span>';
      i++;
      setTimeout(tick, i < 30 ? 50 : 20);
    } else {
      el.innerHTML = safeHighlight
        ? text.replace(new RegExp(`\\b${safeHighlight}\\b`, 'g'), `<span class="hl">${highlight}</span>`)
        : text;
    }
  }
  tick();
}

/* ============================================================
   STYLE BANNER
============================================================ */
const STYLE_META = {
  Backpacker: { emoji: '🎒', colour: '#4CAF82' },
  Comfortable: { emoji: '💼', colour: '#E8A838' },
  Luxury: { emoji: '👑', colour: '#C8A0E8' },
};

function renderStyleBanner(style, notes) {
  // Remove old banners
  ['style-banner', 'notes-banner'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.remove();
  });

  const meta = STYLE_META[style] || STYLE_META['Comfortable'];
  const header = document.querySelector('.results-header');

  const banner = document.createElement('div');
  banner.id = 'style-banner';
  banner.className = 'style-banner';
  banner.style.cssText = `background: rgba(255,255,255,0.04); border: 1px solid ${meta.colour}44; color: ${meta.colour};`;
  banner.innerHTML = `${meta.emoji} Itinerary crafted for a <strong style="margin-left:4px">${style}</strong>&nbsp;experience`;
  header.querySelector('.results-eyebrow').after(banner);

  if (notes && notes.trim()) {
    const noteBanner = document.createElement('div');
    noteBanner.id = 'notes-banner';
    noteBanner.className = 'notes-banner';
    noteBanner.innerHTML = `<span style="font-size:1rem">📝</span><span><strong style="color:var(--gold);font-size:11px;letter-spacing:0.08em;text-transform:uppercase;display:block;margin-bottom:3px">We noted</strong>${notes}</span>`;
    banner.after(noteBanner);
  }
}

/* ============================================================
   DESTINATION CARDS
============================================================ */
function renderResultCards(destinations, style) {
  // FIX #1: Update shownPlaces HERE (after render), so next API call has the full list
  shownPlaces = [...new Set([...shownPlaces, ...destinations.map(d => d.name)])];

  const grid = document.getElementById('results-grid');
  grid.innerHTML = '';

  destinations.forEach((dest, i) => {
    const card = document.createElement('div');
    card.className = 'dest-card' + (i === 0 ? ' top-pick' : '');

    const imgHtml = dest.img
      ? `<div class="dest-card-img-bg" style="background-image:url('${dest.img}')"></div>`
      : `<div class="dest-card-img-placeholder">${dest.icon || '🗺️'}</div>`;

    const itinHtml = dest.itinerary_hint ? `
      <div class="dest-itinerary-hint">
        <div class="dest-itinerary-label">✨ AI Plan — ${style}</div>
        <div class="dest-itinerary-text">${dest.itinerary_hint}</div>
      </div>` : '';

    card.innerHTML = `
  <div class="dest-card-img">
    ${imgHtml}
    ${i === 0 ? '<div class="dest-card-badge">Top pick</div>' : ''}
  </div>
  <div class="dest-card-body">
    <div class="dest-card-state">${dest.state || ''}</div>
    <div class="dest-card-name">${dest.name}</div>
    <div class="dest-card-reason">${dest.reason}</div>
    ${itinHtml}
    <div class="dest-card-tags">
      ${(dest.tags || []).map(t => `<span class="dest-tag">${t}</span>`).join('')}
    </div>

 <button class="dest-card-explore" onclick="goToDestination('${dest.name.replace(/'/g, "\\'")}')">${i === 0 ? 'Explore ' + dest.name : 'Explore'}
  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
    <path d="M1 6h10M7 2l4 4-4 4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>
</button>
  </div>
`;

    grid.appendChild(card);
  });
}

/* ============================================================
   REFINE + PLAN
============================================================ */
function refineResults() { showResults(); }
function planTrip() { alert('🚂 Full itinerary planner — connect FastAPI backend to unlock.'); }

/* ============================================================
   HANDBOOK FEATURE — Destination Intelligence Panel
============================================================ */
async function openHandbook(destName) {
  // Create overlay
  const overlay = document.createElement('div');
  overlay.id = 'handbook-overlay';
  overlay.style.cssText = `
    position: fixed; inset: 0; z-index: 200;
    background: rgba(11,15,26,0.95);
    display: flex; align-items: flex-start; justify-content: center;
    padding: 2rem 1rem; overflow-y: auto;
    animation: fadeUp 0.3s ease;
  `;
  overlay.onclick = (e) => { if (e.target === overlay) closeHandbook(); };

  overlay.innerHTML = `
    <div style="
      background: var(--navy-light); border: 1px solid var(--navy-border);
      border-radius: var(--radius-lg); width: 100%; max-width: 680px;
      padding: 2rem; position: relative; margin: auto;
    ">
      <button onclick="closeHandbook()" style="
        position:absolute; top:1rem; right:1rem;
        background:none; border:none; color:var(--cream-dim);
        font-size:1.5rem; cursor:pointer; line-height:1;
      ">×</button>
      <div style="text-align:center; padding: 2rem 0;">
        <div class="loading-icon" style="margin: 0 auto 1rem;"></div>
        <div style="font-family:var(--font-display);font-size:1.2rem;color:var(--cream)">
          Building your ${destName} handbook…
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(overlay);

  try {
    const res = await fetch(`${API_URL}/handbook/${encodeURIComponent(destName)}`);
    if (!res.ok) throw new Error('Server error');
    const data = await res.json();
    renderHandbook(data, overlay);
  } catch (e) {
    overlay.querySelector('div').innerHTML = `
      <button onclick="closeHandbook()" style="position:absolute;top:1rem;right:1rem;background:none;border:none;color:var(--cream-dim);font-size:1.5rem;cursor:pointer">×</button>
      <div style="padding:2rem;text-align:center;color:var(--cream-dim)">
        Handbook unavailable — backend may be offline.<br/>
        <a href="https://www.google.com/search?q=${encodeURIComponent(destName + ' travel guide India')}"
           target="_blank" style="color:var(--gold);margin-top:1rem;display:inline-block">
          Search on Google instead →
        </a>
      </div>
    `;
  }
}

function renderHandbook(d, overlay) {
  const panel = overlay.querySelector('div');
  panel.innerHTML = `
    <button onclick="closeHandbook()" style="position:absolute;top:1rem;right:1rem;background:none;border:none;color:var(--cream-dim);font-size:1.5rem;cursor:pointer;line-height:1">×</button>

    <!-- Header -->
    <div style="margin-bottom:1.5rem">
      <div style="font-size:11px;letter-spacing:.15em;text-transform:uppercase;color:var(--gold);margin-bottom:4px">${d.state || ''}</div>
      <div style="font-family:var(--font-display);font-size:2rem;font-weight:700;color:var(--cream);line-height:1.1">${d.city}</div>
      <div style="font-size:14px;color:var(--cream-dim);margin-top:6px;font-style:italic">${d.tagline || ''}</div>
    </div>

    <!-- Safety + AQI row -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:1.25rem">
      <div style="background:rgba(76,175,130,0.1);border:1px solid rgba(76,175,130,0.25);border-radius:var(--radius-md);padding:1rem">
        <div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#4CAF82;margin-bottom:4px">Safety</div>
        <div style="font-size:1.5rem;font-weight:600;color:#4CAF82">${d.safety_score}/10</div>
        <div style="font-size:12px;color:var(--cream-dim);margin-top:4px">${d.safety_note || ''}</div>
      </div>
      <div style="background:rgba(232,168,56,0.08);border:1px solid rgba(232,168,56,0.2);border-radius:var(--radius-md);padding:1rem">
        <div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);margin-bottom:4px">AQI — ${d.aqi?.season || 'Current'}</div>
        <div style="font-size:1.5rem;font-weight:600;color:var(--gold)">${d.aqi?.value || 'N/A'}</div>
        <div style="font-size:12px;color:var(--cream-dim);margin-top:4px">${d.aqi?.advisory || ''}</div>
      </div>
    </div>

    <!-- Budget table -->
    <div style="margin-bottom:1.25rem">
      <div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);margin-bottom:8px">Daily budget per person</div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">
        ${Object.entries(d.budget_per_day || {}).map(([style, range]) => `
          <div style="background:var(--navy-mid);border-radius:var(--radius-sm);padding:10px;text-align:center">
            <div style="font-size:10px;color:var(--cream-dim);text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px">${style}</div>
            <div style="font-size:13px;font-weight:500;color:var(--gold)">${range}</div>
          </div>
        `).join('')}
      </div>
    </div>

    <!-- Connectivity -->
    <div style="margin-bottom:1.25rem;padding-bottom:1.25rem;border-bottom:1px solid var(--navy-border)">
      <div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);margin-bottom:6px">How to reach</div>
      <div style="font-size:13px;color:var(--cream-dim);line-height:1.6">${typeof d.connectivity === 'object' ? Object.entries(d.connectivity).map(([k, v]) => `<div style="margin-bottom:6px"><span style="color:var(--gold);font-size:11px;text-transform:uppercase;letter-spacing:.08em">${k}</span><br/>${v}</div>`).join('') : (d.connectivity || 'N/A')}</div>
    </div>

    <!-- Food -->
    <div style="margin-bottom:1.25rem;padding-bottom:1.25rem;border-bottom:1px solid var(--navy-border)">
      <div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);margin-bottom:8px">Food & dining</div>
      <div style="margin-bottom:8px">
        <div style="font-size:11px;color:var(--cream-dim);margin-bottom:6px">Must try</div>
        <div style="display:flex;flex-wrap:wrap;gap:6px">
          ${(d.must_try_food || []).map(f => `<span style="background:rgba(232,168,56,0.1);border:1px solid rgba(232,168,56,0.25);border-radius:999px;padding:4px 12px;font-size:12px;color:var(--gold)">${f}</span>`).join('')}
        </div>
      </div>
      ${d.fine_dining?.length ? `
        <div style="font-size:11px;color:var(--cream-dim);margin-bottom:4px;margin-top:8px">Fine dining</div>
        ${d.fine_dining.map(r => `<div style="font-size:13px;color:var(--cream);padding:3px 0">• ${r}</div>`).join('')}
      ` : ''}
      ${d.cafes?.length ? `
        <div style="font-size:11px;color:var(--cream-dim);margin-bottom:4px;margin-top:8px">Cafes</div>
        ${d.cafes.map(c => `<div style="font-size:13px;color:var(--cream);padding:3px 0">• ${c}</div>`).join('')}
      ` : ''}
    </div>

    <!-- Hidden tips -->
    <div style="margin-bottom:1.25rem;padding-bottom:1.25rem;border-bottom:1px solid var(--navy-border)">
      <div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);margin-bottom:8px">Hidden tips</div>
      ${(d.hidden_tips || []).map(tip => `
        <div style="display:flex;gap:8px;margin-bottom:6px;align-items:flex-start">
          <span style="color:var(--gold);flex-shrink:0">→</span>
          <span style="font-size:13px;color:var(--cream-dim);line-height:1.5">${tip}</span>
        </div>
      `).join('')}
    </div>

    <!-- Top experiences -->
    ${d.top_experiences?.length ? `
      <div style="margin-bottom:1.25rem;padding-bottom:1.25rem;border-bottom:1px solid var(--navy-border)">
        <div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);margin-bottom:8px">Top experiences</div>
        ${d.top_experiences.map(exp => `
          <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04)">
            <span style="font-size:13px;color:var(--cream)">${exp.name}</span>
            <div style="text-align:right">
              <span style="font-size:12px;color:var(--gold);display:block">${exp.cost || ''}</span>
              <span style="font-size:11px;color:var(--cream-dim)">${exp.duration || ''}</span>
            </div>
          </div>
        `).join('')}
      </div>
    ` : ''}

    <!-- Day trips -->
    ${d.nearby_day_trips?.length ? `
      <div style="margin-bottom:1.25rem;padding-bottom:1.25rem;border-bottom:1px solid var(--navy-border)">
        <div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);margin-bottom:8px">Nearby day trips</div>
        <div style="display:flex;flex-wrap:wrap;gap:6px">
          ${d.nearby_day_trips.map(t => `<span style="background:var(--navy-mid);border:1px solid var(--navy-border);border-radius:999px;padding:5px 12px;font-size:12px;color:var(--cream-dim)">${t}</span>`).join('')}
        </div>
      </div>
    ` : ''}

    <!-- Avoid -->
    ${d.avoid ? `
      <div style="background:rgba(224,92,92,0.08);border:1px solid rgba(224,92,92,0.2);border-radius:var(--radius-md);padding:1rem">
        <div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#E05C5C;margin-bottom:4px">Watch out</div>
        <div style="font-size:13px;color:var(--cream-dim)">${d.avoid}</div>
      </div>
    ` : ''}

    <!-- Best time -->
    <div style="margin-top:1.25rem;padding-top:1.25rem;border-top:1px solid var(--navy-border)">
      <div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);margin-bottom:4px">Best time to visit</div>
      <div style="font-size:13px;color:var(--cream-dim)">${d.best_time || 'N/A'}</div>
    </div>
  `;
}

function closeHandbook() {
  const overlay = document.getElementById('handbook-overlay');
  if (overlay) overlay.remove();
}

function goToDestination(cityName) {
  window.location.href = `destination.html?city=${encodeURIComponent(cityName)}`;
}