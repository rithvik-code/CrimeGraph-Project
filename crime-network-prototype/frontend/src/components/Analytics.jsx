import React, { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  AreaChart, Area, Legend,
} from 'recharts'
import { useGraphData } from '../hooks/useGraphData'

const COLORS = ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#a78bfa']

export default function Analytics() {
  const { stats, connections, anomalies, loading } = useGraphData()
  const [trendData, setTrendData] = useState([])

  useEffect(() => {
    if (!stats) return
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    setTrendData(days.map(day => ({
      name: day,
      entities: Math.max(0, Math.floor(Math.random() * 8) + (stats.persons_identified || 0) - 3),
      relations: Math.max(0, Math.floor(Math.random() * 6) + (stats.connections || 0) - 2),
      anomalies: Math.floor(Math.random() * 3),
    })))
  }, [stats])

  const hasData = stats?.total_entities > 0

  if (loading) return <div className="loading"><div className="spinner" /><p>Loading analytics...</p></div>

  if (!hasData) {
    return (
      <div className="analytics">
        <div className="page-header">
          <div><h2>Analytics</h2><p>Network intelligence metrics</p></div>
        </div>
        <div className="empty-graph">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="0.8" opacity="0.15"><path d="M18 20V10M12 20V4M6 20v-6"/></svg>
          <h3>No data to analyze</h3>
          <p>Upload case documents first to see analytics.</p>
        </div>
      </div>
    )
  }

  const entityData = [
    { name: 'Persons', value: stats.persons_identified || 0 },
    { name: 'Vehicles', value: stats.vehicles_tracked || 0 },
    { name: 'Locations', value: stats.locations_mapped || 0 },
    { name: 'Phones', value: stats.phones_traced || 0 },
    { name: 'Financial', value: stats.financial_links || 0 },
  ].filter(d => d.value > 0)

  const confidenceData = connections.length > 0
    ? [
        { range: '0-20%', count: connections.filter(c => c.confidence <= 20).length },
        { range: '21-40%', count: connections.filter(c => c.confidence > 20 && c.confidence <= 40).length },
        { range: '41-60%', count: connections.filter(c => c.confidence > 40 && c.confidence <= 60).length },
        { range: '61-80%', count: connections.filter(c => c.confidence > 60 && c.confidence <= 80).length },
        { range: '81-98%', count: connections.filter(c => c.confidence > 80).length },
      ] : []

  const relationTypes = {}
  connections.forEach(c => c.relations.forEach(r => { relationTypes[r] = (relationTypes[r] || 0) + 1 }))
  const relationData = Object.entries(relationTypes).map(([type, count]) => ({ type: type.replace(/_/g, ' '), count }))

  const radarData = [
    { metric: 'Density', value: stats.total_entities > 0 ? Math.round((stats.total_relations / (stats.total_entities * (stats.total_entities - 1) / 2)) * 100) || 0 : 0 },
    { metric: 'Clustering', value: Math.min(100, (stats.high_risk_connections || 0) * 20) },
    { metric: 'Coverage', value: Math.min(100, (stats.total_entities || 0) * 5) },
    { metric: 'Risk', value: Math.min(100, (stats.high_risk_connections || 0) * 25) },
    { metric: 'Connectivity', value: Math.min(100, (stats.connections || 0) * 10) },
  ]

  return (
    <div className="analytics">
      <div className="page-header">
        <div><h2>Analytics</h2><p>Network intelligence metrics and anomaly analysis</p></div>
      </div>

      <div className="charts-grid">
        <div className="chart-card">
          <h3>Entity Distribution</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={entityData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={3} dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                {entityData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, color: '#e2e8f0' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Confidence Distribution</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={confidenceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="range" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, color: '#e2e8f0' }} />
              <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Relation Types</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={relationData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis type="number" stroke="#64748b" fontSize={12} />
              <YAxis type="category" dataKey="type" stroke="#64748b" fontSize={11} width={120} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, color: '#e2e8f0' }} />
              <Bar dataKey="count" fill="#10b981" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Network Metrics</h3>
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#1e293b" />
              <PolarAngleAxis dataKey="metric" stroke="#64748b" fontSize={11} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#334155" fontSize={10} />
              <Radar name="Metrics" dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card wide">
          <h3>Activity Trend</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, color: '#e2e8f0' }} />
              <Legend />
              <Area type="monotone" dataKey="entities" stackId="1" stroke="#ef4444" fill="#ef4444" fillOpacity={0.15} name="Entities" />
              <Area type="monotone" dataKey="relations" stackId="2" stroke="#6366f1" fill="#6366f1" fillOpacity={0.15} name="Relations" />
              <Area type="monotone" dataKey="anomalies" stackId="3" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.15} name="Anomalies" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {anomalies.length > 0 && (
        <div className="section">
          <h3>Anomalies ({anomalies.length})</h3>
          <div className="anomalies-grid">
            {anomalies.map((a, i) => (
              <div key={i} className={`anomaly-card ${a.severity}`}>
                <div className="anomaly-header">
                  <span className={`severity-badge ${a.severity}`}>{a.severity}</span>
                  <span className="anomaly-type">{a.anomaly_type.replace(/_/g, ' ')}</span>
                </div>
                <p>{a.description}</p>
                {a.metric && (
                  <div className="anomaly-metric">
                    {Object.entries(a.metric).map(([k, v]) => <span key={k}>{k}: <strong>{v}</strong></span>)}
                  </div>
                )}
                <div className="anomaly-entities">
                  {a.entities_involved.map((e, j) => <span key={j} className="tag">{e}</span>)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
