import React, { useState, useEffect, useRef } from 'react'
import Dashboard from './components/Dashboard'
import GraphView from './components/GraphView'
import CaseReports from './components/CaseReports'
import Analytics from './components/Analytics'
import SmartSearch from './components/SmartSearch'
import Timeline from './components/Timeline'
import RiskPanel from './components/RiskPanel'
import ReportExport from './components/ReportExport'
import CaseComparison from './components/CaseComparison'
import Watchlist from './components/Watchlist'
import CrimeGlobe from './components/CrimeGlobe'

const sections = [
  { id: 'intake', label: 'Case Intake', icon: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><path d="M9 14l2 2 4-4"/></svg>
  )},
  { id: 'dashboard', label: 'Dashboard', icon: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
  )},
  { id: 'graph', label: 'Network Graph', icon: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M8.5 8.5l7 7M15.5 8.5l-7 7"/></svg>
  )},
  { id: 'analytics', label: 'Analytics', icon: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 20V10M12 20V4M6 20v-6"/></svg>
  )},
  { id: 'timeline', label: 'Timeline', icon: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
  )},
  { id: 'tools', label: 'Tools', icon: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
  )},
]

function ScrollSection({ id, children }) {
  const ref = useRef(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
        }
      },
      { threshold: 0.08 }
    )
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])

  return (
    <section
      id={id}
      ref={ref}
      className={`scroll-section ${visible ? 'section-visible' : ''}`}
    >
      {children}
    </section>
  )
}

export default function App() {
  const [activeSection, setActiveSection] = useState('intake')
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 40)

      // Determine active section based on scroll position
      const sectionEls = sections.map(s => document.getElementById(s.id))
      for (let i = sectionEls.length - 1; i >= 0; i--) {
        const el = sectionEls[i]
        if (el && el.getBoundingClientRect().top <= 200) {
          setActiveSection(sections[i].id)
          break
        }
      }
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const scrollTo = (id) => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  return (
    <div className="scroll-app">
      {/* ── Floating Nav Bar ──────────────────────────── */}
      <nav className={`floating-nav ${scrolled ? 'scrolled' : ''}`}>
        <div className="nav-inner">
          <div className="nav-brand" onClick={() => scrollTo('intake')}>
            <div className="logo-mark-sm">CG</div>
            <span className="nav-brand-text">CrimeGraph</span>
            <span className="logo-badge-sm">AI</span>
          </div>
          <div className="nav-links-row">
            {sections.map((s) => (
              <button
                key={s.id}
                className={`nav-pill ${activeSection === s.id ? 'active' : ''}`}
                onClick={() => scrollTo(s.id)}
              >
                {s.icon}
                <span>{s.label}</span>
              </button>
            ))}
          </div>
          <div className="nav-search-row"><SmartSearch /></div>
          <div className="nav-tech-row">
            <span className="tech-badge-sm">FastAPI</span>
            <span className="tech-badge-sm">Neo4j</span>
            <span className="tech-badge-sm">spaCy</span>
            <span className="tech-badge-sm">React</span>
          </div>
        </div>
      </nav>

      {/* ── Hero Section with 3D Crime Globe ──────────── */}
      <header className="hero-section" id="hero">
        <CrimeGlobe />
      </header>

      {/* ── Sections ──────────────────────────────────── */}
      <ScrollSection id="intake">
        <CaseReports embedded />
      </ScrollSection>

      <div className="section-divider">
        <div className="divider-line" />
        <div className="divider-dot" />
        <div className="divider-line" />
      </div>

      <ScrollSection id="dashboard">
        <Dashboard embedded />
      </ScrollSection>

      <div className="section-divider">
        <div className="divider-line" />
        <div className="divider-dot" />
        <div className="divider-line" />
      </div>

      <ScrollSection id="graph">
        <GraphView embedded />
      </ScrollSection>

      <div className="section-divider">
        <div className="divider-line" />
        <div className="divider-dot" />
        <div className="divider-line" />
      </div>

      <ScrollSection id="analytics">
        <Analytics embedded />
      </ScrollSection>

      <div className="section-divider"><div className="divider-line" /><div className="divider-dot" /><div className="divider-line" /></div>

      <ScrollSection id="timeline">
        <Timeline embedded />
      </ScrollSection>

      <div className="section-divider"><div className="divider-line" /><div className="divider-dot" /><div className="divider-line" /></div>

      <ScrollSection id="tools">
        <div className="tools-grid">
          <RiskPanel />
          <ReportExport />
          <CaseComparison />
          <Watchlist />
        </div>
      </ScrollSection>

      {/* ── Footer ────────────────────────────────────── */}
      <footer className="scroll-footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <div className="logo-mark-sm">CG</div>
            <span>CrimeGraph AI</span>
          </div>
          <p className="footer-text">
            AI-powered criminal network analysis platform.
            Built with FastAPI, React, spaCy NER, Neo4j GDS, PostgreSQL, and Cytoscape.js.
          </p>
          <div className="footer-tech">
            <span className="tech-badge-sm">FastAPI</span>
            <span className="tech-badge-sm">React</span>
            <span className="tech-badge-sm">spaCy</span>
            <span className="tech-badge-sm">Neo4j</span>
            <span className="tech-badge-sm">PostgreSQL</span>
            <span className="tech-badge-sm">Cytoscape.js</span>
            <span className="tech-badge-sm">Recharts</span>
            <span className="tech-badge-sm">Leaflet</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
