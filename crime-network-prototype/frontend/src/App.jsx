import React from 'react'
import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import Dashboard from './components/Dashboard'
import GraphView from './components/GraphView'
import CaseReports from './components/CaseReports'
import Analytics from './components/Analytics'

export default function App() {
  return (
    <div className="app">
      <nav className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <div className="logo-mark">CG</div>
            <div>
              <h1>CrimeGraph</h1>
              <span className="logo-badge">AI</span>
            </div>
          </div>
        </div>
        <div className="nav-links">
          <NavLink to="/cases" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><path d="M9 14l2 2 4-4"/></svg>
            Case Intake
          </NavLink>
          <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
            Dashboard
          </NavLink>
          <NavLink to="/graph" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M8.5 8.5l7 7M15.5 8.5l-7 7"/></svg>
            Network Graph
          </NavLink>
          <NavLink to="/analytics" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 20V10M12 20V4M6 20v-6"/></svg>
            Analytics
          </NavLink>
        </div>
        <div className="sidebar-footer">
          <div className="tech-stack">
            <span className="tech-badge">FastAPI</span>
            <span className="tech-badge">Neo4j</span>
            <span className="tech-badge">spaCy</span>
            <span className="tech-badge">React</span>
          </div>
        </div>
      </nav>
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to="/cases" replace />} />
          <Route path="/cases" element={<CaseReports />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/graph" element={<GraphView />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </main>
    </div>
  )
}
