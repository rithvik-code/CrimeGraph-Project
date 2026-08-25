import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useGraphData } from '../hooks/useGraphData'

const StatCard = ({ label, value, color, icon }) => (
  <div className="stat-card">
    <div className="stat-icon-wrap" style={{ background: `${color}15` }}>
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2">{icon}</svg>
    </div>
    <div className="stat-info">
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  </div>
)

const icons = {
  persons: <><circle cx="9" cy="7" r="4"/><path d="M3 21v-2a4 4 0 014-4h4a4 4 0 014 4v2"/><path d="M16 3.13a4 4 0 010 7.75M21 21v-2a4 4 0 00-3-3.87"/></>,
  vehicles: <><rect x="1" y="3" width="15" height="13" rx="2"/><path d="M16 8l4 3v5a1 1 0 01-1 1h-1M3 18h16M5 18V8l3-5h6l3 5"/></>,
  locations: <><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></>,
  phones: <><rect x="5" y="2" width="14" height="20" rx="3"/><line x1="12" y1="18" x2="12" y2="18.01"/></>,
  financial: <><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></>,
  connections: <><path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4M10 17l5-5-5-5M13.8 12H3"/></>,
  risk: <><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></>,
}

export default function Dashboard() {
  const { stats, connections, loading, error } = useGraphData()
  const navigate = useNavigate()

  if (loading) return <div className="loading"><div className="spinner" /><p>Loading...</p></div>
  if (error) return <div className="error-state"><p>{error}</p></div>

  const hasData = stats?.total_entities > 0

  const statCards = [
    { label: 'Persons', value: stats?.persons_identified || 0, color: '#ef4444', icon: icons.persons },
    { label: 'Vehicles', value: stats?.vehicles_tracked || 0, color: '#f59e0b', icon: icons.vehicles },
    { label: 'Locations', value: stats?.locations_mapped || 0, color: '#10b981', icon: icons.locations },
    { label: 'Phones', value: stats?.phones_traced || 0, color: '#3b82f6', icon: icons.phones },
    { label: 'Financial', value: stats?.financial_links || 0, color: '#a78bfa', icon: icons.financial },
    { label: 'Connections', value: stats?.connections || 0, color: '#6366f1', icon: icons.connections },
    { label: 'High Risk', value: stats?.high_risk_connections || 0, color: '#ef4444', icon: icons.risk },
  ]

  return (
    <div className="dashboard">
      <div className="page-header">
        <div>
          <h2>Dashboard</h2>
          <p>Network intelligence overview</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-ghost" onClick={() => navigate('/cases')}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            Add Data
          </button>
          {hasData && (
            <button className="btn btn-primary" onClick={() => navigate('/graph')}>
              View Graph
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </button>
          )}
        </div>
      </div>

      {!hasData ? (
        <div className="empty-dashboard">
          <div className="empty-visual">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="0.8" opacity="0.2"><circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M8.5 8.5l7 7M15.5 8.5l-7 7"/></svg>
          </div>
          <h3>No data loaded</h3>
          <p>Upload case documents or paste reports to start building the intelligence graph.</p>
          <button className="btn btn-primary" onClick={() => navigate('/cases')}>
            Go to Case Intake
          </button>
        </div>
      ) : (
        <>
          <div className="stats-grid">
            {statCards.map((card) => (
              <StatCard key={card.label} {...card} />
            ))}
          </div>

          {connections.length > 0 && (
            <div className="section">
              <div className="section-header">
                <h3>Connections</h3>
                <button className="btn btn-ghost btn-sm" onClick={() => navigate('/graph')}>View Graph</button>
              </div>
              <div className="connections-table">
                <table>
                  <thead>
                    <tr>
                      <th>Source</th>
                      <th>Target</th>
                      <th>Relations</th>
                      <th>Confidence</th>
                      <th>Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {connections.map((conn, i) => (
                      <tr key={i}>
                        <td><span className="tag tag-person">{conn.source}</span></td>
                        <td><span className="tag tag-person">{conn.target}</span></td>
                        <td>
                          <div className="relation-tags">
                            {conn.relations.map((r, j) => (
                              <span key={j} className="tag tag-relation">{r}</span>
                            ))}
                          </div>
                        </td>
                        <td>
                          <div className="confidence-bar-container">
                            <div className="confidence-bar" style={{
                              width: `${conn.confidence}%`,
                              background: conn.confidence >= 80 ? '#ef4444' : conn.confidence >= 60 ? '#f59e0b' : '#10b981',
                            }} />
                            <span className="confidence-text">{conn.confidence}%</span>
                          </div>
                        </td>
                        <td>
                          <span className={`risk-badge ${conn.high_risk ? 'high' : 'low'}`}>
                            {conn.high_risk ? 'HIGH' : 'Normal'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
