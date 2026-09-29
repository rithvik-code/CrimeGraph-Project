import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import Globe from 'react-globe.gl'
import { api } from '../utils/api'

function formatTime(dateStr) {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return ''
    const now = new Date()
    const diffMs = now - d
    const diffMins = Math.floor(diffMs / 60000)
    const diffHrs = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)
    if (diffMins < 1) return 'just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHrs < 24) return `${diffHrs}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  } catch {
    return ''
  }
}

function parseDate(dateStr) {
  if (!dateStr) return null
  try {
    const d = new Date(dateStr)
    return isNaN(d.getTime()) ? null : d.getTime()
  } catch {
    return null
  }
}

function formatSliderDate(ts) {
  const d = new Date(ts)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

// ── Dual Range Slider ────────────────────────────────
function DateRangeSlider({ min, max, rangeMin, rangeMax, onChange }) {
  const trackRef = useRef(null)
  const [dragging, setDragging] = useState(null) // 'min' | 'max' | null

  const pctMin = ((rangeMin - min) / (max - min)) * 100
  const pctMax = ((rangeMax - min) / (max - min)) * 100

  const handleMouseDown = (which) => (e) => {
    e.preventDefault()
    setDragging(which)
  }

  useEffect(() => {
    if (!dragging) return
    const handleMove = (e) => {
      if (!trackRef.current) return
      const rect = trackRef.current.getBoundingClientRect()
      const clientX = e.touches ? e.touches[0].clientX : e.clientX
      const pct = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width))
      const val = Math.round(min + pct * (max - min))
      if (dragging === 'min') {
        onChange(Math.min(val, rangeMax - 1), rangeMax)
      } else {
        onChange(rangeMin, Math.max(val, rangeMin + 1))
      }
    }
    const handleUp = () => setDragging(null)
    window.addEventListener('mousemove', handleMove)
    window.addEventListener('mouseup', handleUp)
    window.addEventListener('touchmove', handleMove, { passive: false })
    window.addEventListener('touchend', handleUp)
    return () => {
      window.removeEventListener('mousemove', handleMove)
      window.removeEventListener('mouseup', handleUp)
      window.removeEventListener('touchmove', handleMove)
      window.removeEventListener('touchend', handleUp)
    }
  }, [dragging, min, max, rangeMin, rangeMax, onChange])

  // Quick preset buttons
  const presets = [
    { label: '24h', ms: 24 * 60 * 60 * 1000 },
    { label: '3d', ms: 3 * 24 * 60 * 60 * 1000 },
    { label: '7d', ms: 7 * 24 * 60 * 60 * 1000 },
    { label: 'All', ms: max - min },
  ]

  return (
    <div className="date-range-slider">
      <div className="slider-header">
        <div className="slider-title">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
          </svg>
          <span>TIME FILTER</span>
        </div>
        <div className="slider-presets">
          {presets.map((p) => {
            const isActive = (p.label === '24h' && (rangeMax - rangeMin) <= p.ms + 60000) ||
              (p.label === '3d' && (rangeMax - rangeMin) <= p.ms + 60000 && (rangeMax - rangeMin) > 24*3600000) ||
              (p.label === '7d' && (rangeMax - rangeMin) <= p.ms + 60000 && (rangeMax - rangeMin) > 3*86400000) ||
              (p.label === 'All' && Math.abs((rangeMin - min) + (max - rangeMax)) < 60000)
            return (
              <button
                key={p.label}
                className={`preset-btn ${isActive ? 'active' : ''}`}
                onClick={() => {
                  if (p.label === 'All') {
                    onChange(min, max)
                  } else {
                    onChange(max - p.ms, max)
                  }
                }}
              >
                {p.label}
              </button>
            )
          })}
        </div>
      </div>
      <div className="slider-dates">
        <span className="slider-date-label">{formatSliderDate(rangeMin)}</span>
        <span className="slider-range-badge">{Math.ceil((rangeMax - rangeMin) / 86400000)}d range</span>
        <span className="slider-date-label">{formatSliderDate(rangeMax)}</span>
      </div>
      <div className="slider-track" ref={trackRef}>
        <div className="slider-track-bg" />
        <div
          className="slider-track-fill"
          style={{ left: `${pctMin}%`, width: `${pctMax - pctMin}%` }}
        />
        {/* Timeline dots for each news item */}
        {presets.length && (
          <div className="slider-dots">
            {/* We'll overlay news item positions */}
          </div>
        )}
        <div
          className={`slider-handle ${dragging === 'min' ? 'dragging' : ''}`}
          style={{ left: `${pctMin}%` }}
          onMouseDown={handleMouseDown('min')}
          onTouchStart={handleMouseDown('min')}
        >
          <div className="handle-glow" />
          <div className="handle-dot" />
          <div className="handle-tooltip">{formatSliderDate(rangeMin)}</div>
        </div>
        <div
          className={`slider-handle ${dragging === 'max' ? 'dragging' : ''}`}
          style={{ left: `${pctMax}%` }}
          onMouseDown={handleMouseDown('max')}
          onTouchStart={handleMouseDown('max')}
        >
          <div className="handle-glow" />
          <div className="handle-dot" />
          <div className="handle-tooltip">{formatSliderDate(rangeMax)}</div>
        </div>
      </div>
    </div>
  )
}


export default function CrimeGlobe() {
  const globeRef = useRef()
  const containerRef = useRef()
  const [globeSize, setGlobeSize] = useState({ width: 800, height: 600 })
  const [news, setNews] = useState([])
  const [stats, setStats] = useState({ total: 0, crime_count: 0, sources: [] })
  const [activeNews, setActiveNews] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)

  // Date range state
  const [dateRange, setDateRange] = useState({ min: 0, max: 0, rangeMin: 0, rangeMax: 0 })

  // Search & filter state
  const [searchQuery, setSearchQuery] = useState('')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all') // 'all' | 'crime' | 'world'

  const fetchNews = useCallback(async () => {
    try {
      const data = await api.getCrimeNews()
      const items = data.items || []
      setNews(items)
      setStats({
        total: data.total || 0,
        crime_count: data.crime_count || 0,
        sources: data.sources || [],
      })
      // Compute date range from news items
      const timestamps = items.map(i => parseDate(i.pubDate)).filter(Boolean)
      if (timestamps.length > 0) {
        const minT = Math.min(...timestamps)
        const maxT = Math.max(...timestamps)
        setDateRange(prev => {
          // Only reset if this is first load or range expanded
          if (prev.min === 0 || minT < prev.min || maxT > prev.max) {
            return { min: minT, max: maxT, rangeMin: minT, rangeMax: maxT }
          }
          return { ...prev, min: Math.min(minT, prev.min), max: Math.max(maxT, prev.max) }
        })
      }
      setLastUpdated(new Date())
      setLoading(false)
    } catch (err) {
      console.error('Failed to fetch crime news:', err)
      setLoading(false)
    }
  }, [])

  // Available sources for filter pills
  const availableSources = useMemo(() => {
    const srcs = [...new Set(news.map(n => n.source))].filter(Boolean)
    return srcs.sort()
  }, [news])

  // Filtered news based on date range + search + source + type
  const filteredNews = useMemo(() => {
    let result = news
    // Date filter
    if (dateRange.min > 0) {
      result = result.filter(item => {
        const ts = parseDate(item.pubDate)
        if (!ts) return true
        return ts >= dateRange.rangeMin && ts <= dateRange.rangeMax
      })
    }
    // Crime type filter
    if (typeFilter === 'crime') {
      result = result.filter(item => item.is_crime)
    } else if (typeFilter === 'world') {
      result = result.filter(item => !item.is_crime)
    }
    // Source filter
    if (sourceFilter !== 'all') {
      result = result.filter(item => item.source === sourceFilter)
    }
    // Keyword search
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim()
      result = result.filter(item =>
        (item.title && item.title.toLowerCase().includes(q)) ||
        (item.description && item.description.toLowerCase().includes(q)) ||
        (item.source && item.source.toLowerCase().includes(q))
      )
    }
    return result
  }, [news, dateRange.rangeMin, dateRange.rangeMax, dateRange.min, typeFilter, sourceFilter, searchQuery])

  const filteredStats = useMemo(() => ({
    total: filteredNews.length,
    crime_count: filteredNews.filter(n => n.is_crime).length,
  }), [filteredNews])

  // Measure container size
  useEffect(() => {
    const measure = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect()
        setGlobeSize({ width: rect.width, height: rect.height })
      }
    }
    measure()
    window.addEventListener('resize', measure)
    return () => window.removeEventListener('resize', measure)
  }, [])

  useEffect(() => {
    fetchNews()
    const interval = setInterval(fetchNews, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [fetchNews])

  // Auto-rotate globe
  useEffect(() => {
    if (globeRef.current) {
      const globe = globeRef.current
      globe.controls().autoRotate = true
      globe.controls().autoRotateSpeed = 0.4
      globe.controls().enableZoom = true
      globe.controls().minDistance = 180
      globe.controls().maxDistance = 400
    }
  }, [loading])

  // Auto-cycle through news items
  useEffect(() => {
    if (filteredNews.length === 0) return
    let idx = 0
    const timer = setInterval(() => {
      setActiveNews(filteredNews[idx % filteredNews.length])
      idx++
    }, 4000)
    return () => clearInterval(timer)
  }, [filteredNews])

  const pointsData = useMemo(() => filteredNews.map((item) => ({
    lat: item.lat,
    lng: item.lng,
    size: item.is_crime ? 0.35 : 0.2,
    color: item.is_crime ? '#ff3355' : '#00f0ff',
    glow: item.is_crime,
    ...item,
  })), [filteredNews])

  // Arcs connecting crime points
  const arcsData = useMemo(() => {
    const arcs = []
    const crimePoints = filteredNews.filter((n) => n.is_crime)
    for (let i = 0; i < Math.min(crimePoints.length - 1, 15); i++) {
      arcs.push({
        startLat: crimePoints[i].lat,
        startLng: crimePoints[i].lng,
        endLat: crimePoints[i + 1].lat,
        endLng: crimePoints[i + 1].lng,
        color: ['rgba(0,240,255,0.4)', 'rgba(255,51,85,0.6)'],
      })
    }
    return arcs
  }, [filteredNews])

  const handleRangeChange = useCallback((newMin, newMax) => {
    setDateRange(prev => ({ ...prev, rangeMin: newMin, rangeMax: newMax }))
  }, [])

  if (loading) {
    return (
      <div className="globe-container">
        <div className="globe-loading">
          <div className="spinner" />
          <span>Fetching global intelligence...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="globe-container">
      {/* 3D Globe */}
      <div className="globe-canvas" ref={containerRef}>
        <Globe
          ref={globeRef}
          width={globeSize.width}
          height={globeSize.height}
          globeImageUrl="https://unpkg.com/three-globe/example/img/earth-dark.jpg"
          bumpImageUrl="https://unpkg.com/three-globe/example/img/earth-topology.png"
          backgroundImageUrl=""
          backgroundColor="rgba(0,0,0,0)"
          atmosphereColor="#00f0ff"
          atmosphereAltitude={0.25}
          pointsData={pointsData}
          pointLat="lat"
          pointLng="lng"
          pointColor="color"
          pointAltitude={0.01}
          pointRadius="size"
          pointEmissive={0.8}
          pointEmissiveIntensity={1.5}
          pointsMerge={false}
          arcsData={arcsData}
          arcColor="color"
          arcDashLength={0.4}
          arcDashGap={0.2}
          arcDashAnimateTime={2000}
          arcStroke={0.5}
          onPointClick={(point) => setActiveNews(point)}
        />
      </div>

      {/* Overlay — Brand */}
      <div className="globe-overlay-top">
        <div className="hero-badge">
          <span className="hero-badge-dot" />
          AI-Powered Investigation Platform
        </div>
        <h1 className="hero-title">
          <span className="hero-title-line">Crime</span>
          <span className="hero-title-line accent">Graph</span>
          <span className="hero-title-line small">AI</span>
        </h1>
        <p className="hero-subtitle">
          Extract entities, map criminal networks, detect anomalies, and analyze
          intelligence graphs — powered by NLP, graph databases, and real-time analytics.
        </p>
      </div>

      {/* Overlay — News Ticker */}
      <div className="globe-news-ticker">
        <div className="ticker-header">
          <div className="ticker-pulse" />
          <span className="ticker-label">LIVE INTELLIGENCE FEED</span>
          <span className="ticker-count">{filteredStats.crime_count}/{filteredStats.total} reports</span>
        </div>

        {/* Search & Filter Bar */}
        <div className="ticker-filter-bar">
          <div className="ticker-search">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            <input
              type="text"
              placeholder="Search news..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button className="search-clear" onClick={() => setSearchQuery('')}>&times;</button>
            )}
          </div>
          <div className="ticker-type-pills">
            <button className={`type-pill ${typeFilter === 'all' ? 'active' : ''}`} onClick={() => setTypeFilter('all')}>All</button>
            <button className={`type-pill crime ${typeFilter === 'crime' ? 'active' : ''}`} onClick={() => setTypeFilter('crime')}>Crime</button>
            <button className={`type-pill world ${typeFilter === 'world' ? 'active' : ''}`} onClick={() => setTypeFilter('world')}>World</button>
          </div>
          <div className="ticker-source-pills">
            <button className={`source-pill ${sourceFilter === 'all' ? 'active' : ''}`} onClick={() => setSourceFilter('all')}>All Sources</button>
            {availableSources.slice(0, 3).map(src => (
              <button
                key={src}
                className={`source-pill ${sourceFilter === src ? 'active' : ''}`}
                onClick={() => setSourceFilter(sourceFilter === src ? 'all' : src)}
              >
                {src}
              </button>
            ))}
          </div>
        </div>

        <div className="ticker-scroll">
          {filteredNews.slice(0, 12).map((item, i) => (
            <div
              key={item.id || i}
              className={`ticker-item ${item.is_crime ? 'crime' : 'world'} ${activeNews?.id === item.id ? 'active' : ''}`}
              onClick={() => setActiveNews(item)}
            >
              <span className="ticker-dot" />
              <div className="ticker-text">
                <span className="ticker-title">{item.title}</span>
                <div className="ticker-meta-row">
                  <span className="ticker-source">{item.source}</span>
                  {item.pubDate && <span className="ticker-time">{formatTime(item.pubDate)}</span>}
                </div>
              </div>
            </div>
          ))}
          {filteredNews.length === 0 && (
            <div className="ticker-empty">No reports in selected time range</div>
          )}
        </div>
      </div>

      {/* Overlay — Active News Detail */}
      {activeNews && (
        <div className="globe-news-detail">
          <button className="detail-close" onClick={() => setActiveNews(null)}>×</button>
          <div className={`detail-badge ${activeNews.is_crime ? 'crime' : 'world'}`}>
            {activeNews.is_crime ? '🔴 CRIME' : '🔵 WORLD'}
          </div>
          <h3>{activeNews.title}</h3>
          <p>{activeNews.description}</p>
          <div className="detail-meta">
            <span>{activeNews.source}</span>
            {activeNews.pubDate && <span>{activeNews.pubDate}</span>}
          </div>
          {activeNews.link && activeNews.link !== '#' && (
            <a href={activeNews.link} target="_blank" rel="noopener noreferrer" className="detail-link">
              Read Full Report →
            </a>
          )}
        </div>
      )}

      {/* Overlay — Stats + Date Range Slider */}
      <div className="globe-bottom-area">
        <div className="globe-stats-bar">
          <div className="globe-stat">
            <span className="globe-stat-value">{filteredStats.total}</span>
            <span className="globe-stat-label">Reports</span>
          </div>
          <div className="globe-stat-divider" />
          <div className="globe-stat">
            <span className="globe-stat-value">{filteredStats.crime_count}</span>
            <span className="globe-stat-label">Crime</span>
          </div>
          <div className="globe-stat-divider" />
          <div className="globe-stat">
            <span className="globe-stat-value">{stats.sources?.length || 0}</span>
            <span className="globe-stat-label">Sources</span>
          </div>
          <div className="globe-stat-divider" />
          <div className="globe-stat">
            <span className="globe-stat-value">Live</span>
            <span className="globe-stat-label">Status</span>
          </div>
        </div>

        {/* Date Range Slider */}
        {dateRange.min > 0 && (
          <DateRangeSlider
            min={dateRange.min}
            max={dateRange.max}
            rangeMin={dateRange.rangeMin}
            rangeMax={dateRange.rangeMax}
            onChange={handleRangeChange}
          />
        )}
      </div>

      {/* Overlay — Actions */}
      <div className="hero-actions">
        <button className="btn-hero-primary" onClick={() => document.getElementById('intake')?.scrollIntoView({ behavior: 'smooth' })}>
          Start Investigation
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </button>
        <button className="btn-hero-ghost" onClick={() => document.getElementById('graph')?.scrollIntoView({ behavior: 'smooth' })}>
          View Network Graph
        </button>
      </div>

      {/* Overlay — Scroll Hint */}
      <div className="hero-scroll-hint" onClick={() => document.getElementById('intake')?.scrollIntoView({ behavior: 'smooth' })}>
        <span>Scroll to explore</span>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 5v14M5 12l7 7 7-7"/></svg>
      </div>

      {/* Overlay — Last Updated */}
      {lastUpdated && (
        <div className="globe-updated">
          Last updated: {lastUpdated.toLocaleTimeString()}
        </div>
      )}
    </div>
  )
}
