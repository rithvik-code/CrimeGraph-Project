import React, { useState, useEffect } from 'react'
import { api } from '../utils/api'
export default function RiskPanel() {
  const [scores, setScores] = useState([])
  const [loading, setLoading] = useState(true)
  useEffect(() => { api.getRiskScores().then(setScores).catch(console.error).finally(() => setLoading(false)) }, [])
  if (loading) return <div className="loading"><div className="spinner" /><p>Calculating risk...</p></div>
  if (!scores.length) return <div className="empty-graph"><p>No persons to assess.</p></div>
  const lc = { critical: '#ff3355', high: '#f59e0b', medium: '#3b82f6', low: '#10b981' }
  return (<div className="risk-panel"><h3>RISK ASSESSMENT</h3><div className="risk-grid">
    {scores.map((s, i) => (<div key={i} className="risk-card"><div className="risk-card-header"><span className="risk-entity">{s.entity}</span><span className={'risk-level risk-' + s.level}>{s.level.toUpperCase()}</span></div>
    <div className="risk-gauge"><div className="risk-gauge-track"><div className="risk-gauge-fill" style={{ width: s.risk_score + '%', background: lc[s.level] }} /></div><span className="risk-score" style={{ color: lc[s.level] }}>{s.risk_score}</span></div>
    <div className="risk-breakdown">{Object.entries(s.breakdown).map(([k, v]) => <div key={k} className="risk-factor"><span>{k.replace(/_/g, ' ')}</span><div className="risk-factor-bar"><div className="risk-factor-fill" style={{ width: (v / 25 * 100) + '%', background: lc[s.level] }} /></div><span>{v}</span></div>)}</div></div>))}
  </div></div>)
}
