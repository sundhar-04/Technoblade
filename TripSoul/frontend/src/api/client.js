/**
 * TripSoul API Client — Centralized fetch wrapper with error handling.
 */
const BASE_URL = '/api';

async function request(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${BASE_URL}${endpoint}`;
  const config = {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  };

  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body);
  }

  const res = await fetch(url, config);
  if (!res.ok) {
    const error = await res.text().catch(() => 'Unknown error');
    throw new Error(`API Error ${res.status}: ${error}`);
  }
  return res.json();
}

// ── Planner ──
export const searchFlights = (data) =>
  request('/planner/search-flights', { method: 'POST', body: data });

export const searchHotels = (data) =>
  request('/planner/search-hotels', { method: 'POST', body: data });

export const generateItinerary = (data) =>
  request('/planner/generate', { method: 'POST', body: data });

export const replanItinerary = (data) =>
  request('/planner/replan', { method: 'POST', body: data });

// ── Optimization ──
export const optimizeBudget = (data) =>
  request('/optimization/budget', { method: 'POST', body: data });

// ── Personalization ──
export const trackFeedback = (data) =>
  request('/personalization/track', { method: 'POST', body: data });

export const getRecommendations = (userId, city = 'nyc') =>
  request(`/personalization/recommendations/${userId}?city=${city}`);

// ── Prediction ──
export const getDelays = (city, baseTime = 20) =>
  request(`/prediction/delays/${city}?base_time=${baseTime}`);

export const getConditions = (city) =>
  request(`/prediction/conditions/${city}`);

// ── Adaptation ──
export const getAdaptationStatus = () => request('/adaptation/status');

export const simulateDisruption = (data) =>
  request('/adaptation/simulate', { method: 'POST', body: data });

// ── Recommend (AI-powered destination discovery) ──
export const recommend = (prefs) =>
  request('/recommend/destinations', { method: 'POST', body: prefs });

export const getHandbook = (city) =>
  request(`/recommend/handbook/${encodeURIComponent(city)}`);

// ── Cities ──
export const getCities = () => request('/cities');

// ── SSE ──
export function connectSSE(onEvent) {
  const evtSource = new EventSource(`${BASE_URL}/adaptation/events`);

  evtSource.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.type !== 'ping') onEvent(data);
    } catch { /* ignore parse errors */ }
  };

  evtSource.onerror = () => {
    console.warn('[SSE] Connection lost, reconnecting in 3s...');
    evtSource.close();
    setTimeout(() => connectSSE(onEvent), 3000);
  };

  return evtSource;
}
