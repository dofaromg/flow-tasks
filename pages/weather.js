/**
 * Weather Dashboard Page — /weather
 *
 * Features:
 * - City search with keyboard support
 * - Current weather: temperature, feels-like, condition, humidity, wind, UV index
 * - 3-day forecast summary
 * - Loading, empty, and error states
 * - Responsive layout (mobile + desktop)
 * - Accessible: labels, semantic HTML, ARIA roles
 *
 * Data source: wttr.in (keyless, no API key required)
 */

import Head from 'next/head';
import Link from 'next/link';
import { useState, useCallback, useRef } from 'react';

// ─── Colour tokens ────────────────────────────────────────────────────────────
const C = {
  bg: '#f0f9ff',
  surface: '#ffffff',
  border: '#e2e8f0',
  primary: '#0ea5e9',
  primaryDark: '#0284c7',
  textMain: '#0f172a',
  textMuted: '#64748b',
  textLight: '#94a3b8',
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  errorBg: '#fef2f2',
  errorBorder: '#fecaca',
  cardBg: '#f8fafc',
  cardBgHover: '#f1f5f9',
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatDay(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr + 'T12:00:00Z');
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

function windLabel(kmph) {
  if (kmph < 1) return 'Calm';
  if (kmph < 20) return 'Light';
  if (kmph < 40) return 'Moderate';
  if (kmph < 62) return 'Fresh';
  if (kmph < 88) return 'Strong';
  return 'Storm';
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatCard({ label, value, icon }) {
  return (
    <div
      style={{
        background: C.cardBg,
        border: `1px solid ${C.border}`,
        borderRadius: 12,
        padding: '1rem',
        display: 'flex',
        flexDirection: 'column',
        gap: 4,
        minWidth: 0,
      }}
      role="group"
      aria-label={label}
    >
      <span style={{ fontSize: '1.3rem' }} aria-hidden="true">{icon}</span>
      <span style={{ fontSize: '0.75rem', color: C.textMuted, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </span>
      <span style={{ fontSize: '1.1rem', fontWeight: 700, color: C.textMain }}>{value}</span>
    </div>
  );
}

function ForecastCard({ day }) {
  return (
    <div
      style={{
        background: C.surface,
        border: `1px solid ${C.border}`,
        borderRadius: 12,
        padding: '1rem 0.75rem',
        textAlign: 'center',
        flex: '1 1 0',
        minWidth: 0,
      }}
    >
      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: C.textMuted, marginBottom: 4 }}>
        {formatDay(day.date)}
      </div>
      <div style={{ fontSize: '2rem', margin: '6px 0' }} aria-label={day.description}>{day.emoji}</div>
      <div style={{ fontSize: '0.8rem', color: C.textMuted, marginBottom: 8 }}>{day.description}</div>
      <div style={{ fontWeight: 700, color: C.textMain }}>
        {day.maxTempC}°<span style={{ color: C.textMuted, fontWeight: 400 }}> / {day.minTempC}°</span>
      </div>
      <div style={{ fontSize: '0.75rem', color: C.textMuted, marginTop: 4 }}>
        💧 {day.avgHumidity}%
      </div>
      {day.sunrise && (
        <div style={{ fontSize: '0.7rem', color: C.textLight, marginTop: 6 }}>
          🌅 {day.sunrise} &nbsp; 🌇 {day.sunset}
        </div>
      )}
    </div>
  );
}

function LoadingSpinner() {
  return (
    <div role="status" aria-live="polite" style={{ textAlign: 'center', padding: '3rem 0', color: C.textMuted }}>
      <div
        style={{
          display: 'inline-block',
          width: 40,
          height: 40,
          border: `4px solid ${C.border}`,
          borderTopColor: C.primary,
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
          marginBottom: 12,
        }}
      />
      <p style={{ margin: 0, fontWeight: 600 }}>Fetching weather data…</p>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

function ErrorMessage({ message }) {
  return (
    <div
      role="alert"
      style={{
        background: C.errorBg,
        border: `1px solid ${C.errorBorder}`,
        borderRadius: 12,
        padding: '1rem 1.25rem',
        color: C.error,
        fontWeight: 600,
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        marginTop: '1.5rem',
      }}
    >
      <span style={{ fontSize: '1.3rem' }}>⚠️</span>
      <span>{message}</span>
    </div>
  );
}

function EmptyState() {
  return (
    <div style={{ textAlign: 'center', padding: '3rem 0', color: C.textMuted }}>
      <div style={{ fontSize: '4rem', marginBottom: 16 }}>🌍</div>
      <p style={{ margin: 0, fontWeight: 600, fontSize: '1.1rem', color: C.textMain }}>Search for a city to see weather</p>
          <p style={{ margin: '8px 0 0', fontSize: '0.9rem' }}>
            Try &ldquo;Tokyo&rdquo;, &ldquo;London&rdquo;, &ldquo;New York&rdquo;, or &ldquo;Taipei&rdquo;
          </p>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function WeatherDashboard() {
  const [query, setQuery] = useState('');
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef(null);

  const search = useCallback(async (city) => {
    const trimmed = city.trim();
    if (!trimmed) return;

    setLoading(true);
    setError('');
    setWeather(null);

    try {
      const res = await fetch(`/api/weather?city=${encodeURIComponent(trimmed)}`);
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Something went wrong. Please try again.');
      } else {
        setWeather(data);
      }
    } catch {
      setError('Network error. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    search(query);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') search(query);
  };

  return (
    <>
      <Head>
        <title>Weather Dashboard — MRLiou</title>
        <meta name="description" content="Real-time weather dashboard powered by wttr.in. Search any city for current conditions and a 3-day forecast." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div
        style={{
          minHeight: '100vh',
          background: `radial-gradient(circle at 10% 10%, #bae6fd 0, transparent 35%),
                       radial-gradient(circle at 90% 5%, #e0f2fe 0, transparent 30%),
                       ${C.bg}`,
          fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
          color: C.textMain,
          padding: '2rem 1rem',
        }}
      >
        {/* ── Header ── */}
        <header style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <Link
            href="/"
            style={{
              display: 'inline-block',
              fontSize: '0.8rem',
              color: C.textMuted,
              textDecoration: 'none',
              marginBottom: 12,
              fontWeight: 600,
            }}
          >
            ← Back to MRLiou
          </Link>
          <h1 style={{ margin: '0 0 0.5rem', fontSize: 'clamp(1.75rem, 5vw, 2.5rem)' }}>
            🌤️ Weather Dashboard
          </h1>
          <p style={{ margin: 0, color: C.textMuted, fontSize: '1rem' }}>
            Real-time conditions &amp; forecast · Powered by{' '}
            <a href="https://wttr.in" target="_blank" rel="noopener noreferrer" style={{ color: C.primary }}>
              wttr.in
            </a>
          </p>
        </header>

        {/* ── Search bar ── */}
        <main>
          <form
            onSubmit={handleSubmit}
            role="search"
            aria-label="Weather search"
            style={{
              display: 'flex',
              gap: 8,
              maxWidth: 560,
              margin: '0 auto 2rem',
            }}
          >
            <label htmlFor="city-input" style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0,0,0,0)' }}>
              City or location
            </label>
            <input
              id="city-input"
              ref={inputRef}
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter city, e.g. Tokyo, Paris, Taipei&#8230;"
              autoComplete="off"
              spellCheck={false}
              disabled={loading}
              style={{
                flex: 1,
                padding: '0.85rem 1rem',
                borderRadius: 12,
                border: `2px solid ${C.border}`,
                fontSize: '1rem',
                outline: 'none',
                transition: 'border-color 0.15s',
                color: C.textMain,
                background: C.surface,
              }}
              onFocus={(e) => (e.currentTarget.style.borderColor = C.primary)}
              onBlur={(e) => (e.currentTarget.style.borderColor = C.border)}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              aria-label="Search weather"
              style={{
                padding: '0.85rem 1.4rem',
                borderRadius: 12,
                border: 'none',
                background: loading || !query.trim() ? C.textLight : C.primary,
                color: '#fff',
                fontWeight: 700,
                fontSize: '1rem',
                cursor: loading || !query.trim() ? 'not-allowed' : 'pointer',
                transition: 'background 0.15s',
                whiteSpace: 'nowrap',
              }}
              onMouseEnter={(e) => { if (!loading && query.trim()) e.currentTarget.style.background = C.primaryDark; }}
              onMouseLeave={(e) => { if (!loading && query.trim()) e.currentTarget.style.background = C.primary; }}
            >
              🔍 Search
            </button>
          </form>

          {/* ── States ── */}
          <div style={{ maxWidth: 760, margin: '0 auto' }}>
            {loading && <LoadingSpinner />}
            {error && <ErrorMessage message={error} />}
            {!loading && !error && !weather && <EmptyState />}

            {/* ── Weather result ── */}
            {!loading && !error && weather && (
              <section aria-label={`Weather for ${weather.location.name}`}>
                {/* Location heading */}
                <div
                  style={{
                    background: C.surface,
                    border: `1px solid ${C.border}`,
                    borderRadius: 16,
                    padding: '1.5rem',
                    marginBottom: '1.25rem',
                    boxShadow: '0 4px 24px rgba(15,23,42,0.06)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                    {/* Left: location + emoji + temp */}
                    <div>
                      <h2 style={{ margin: '0 0 4px', fontSize: 'clamp(1.25rem, 4vw, 1.75rem)' }}>
                        {weather.location.name}
                        {weather.location.country && (
                          <span style={{ fontWeight: 400, color: C.textMuted, fontSize: '0.85em' }}>
                            {' · '}{weather.location.country}
                          </span>
                        )}
                      </h2>
                      <p style={{ margin: '0 0 1rem', fontSize: '0.85rem', color: C.textMuted }}>
                        Observed at {weather.current.observedAt} UTC
                      </p>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                        <span style={{ fontSize: 'clamp(3rem, 10vw, 4.5rem)' }} aria-label={weather.current.description}>
                          {weather.current.emoji}
                        </span>
                        <div>
                          <div style={{ fontSize: 'clamp(2.5rem, 8vw, 3.5rem)', fontWeight: 800, lineHeight: 1 }}>
                            {weather.current.tempC}°C
                          </div>
                          <div style={{ color: C.textMuted, fontWeight: 600, fontSize: '1rem' }}>
                            {weather.current.tempF}°F
                          </div>
                        </div>
                      </div>
                      <div style={{ marginTop: 8, fontWeight: 600, fontSize: '1.1rem' }}>
                        {weather.current.description}
                      </div>
                      <div style={{ marginTop: 4, color: C.textMuted, fontSize: '0.9rem' }}>
                        Feels like {weather.current.feelsLikeC}°C
                      </div>
                    </div>
                  </div>
                </div>

                {/* Stat grid */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))',
                    gap: 12,
                    marginBottom: '1.25rem',
                  }}
                  aria-label="Current conditions"
                >
                  <StatCard label="Humidity" value={`${weather.current.humidity}%`} icon="💧" />
                  <StatCard
                    label="Wind"
                    value={`${weather.current.windSpeedKmph} km/h ${weather.current.windDir}`}
                    icon="💨"
                  />
                  <StatCard
                    label="Wind strength"
                    value={windLabel(weather.current.windSpeedKmph)}
                    icon="🏁"
                  />
                  <StatCard label="Visibility" value={`${weather.current.visibilityKm} km`} icon="👁️" />
                  <StatCard label="UV Index" value={weather.current.uvIndex} icon="☀️" />
                  <StatCard label="Cloud Cover" value={`${weather.current.cloudCover}%`} icon="☁️" />
                </div>

                {/* 3-day forecast */}
                <div
                  style={{
                    background: C.surface,
                    border: `1px solid ${C.border}`,
                    borderRadius: 16,
                    padding: '1.25rem',
                    boxShadow: '0 4px 24px rgba(15,23,42,0.06)',
                  }}
                >
                  <h3 style={{ margin: '0 0 1rem', fontWeight: 700, color: C.textMain, fontSize: '1rem' }}>
                    3-Day Forecast
                  </h3>
                  <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                    {weather.forecast.map((day) => (
                      <ForecastCard key={day.date} day={day} />
                    ))}
                  </div>
                </div>

                {/* Attribution */}
                <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.75rem', color: C.textLight }}>
                  Data from{' '}
                  <a href="https://wttr.in" target="_blank" rel="noopener noreferrer" style={{ color: C.primary }}>
                    wttr.in
                  </a>{' '}
                  · Refreshes every 5 min
                </p>
              </section>
            )}
          </div>
        </main>
      </div>
    </>
  );
}
