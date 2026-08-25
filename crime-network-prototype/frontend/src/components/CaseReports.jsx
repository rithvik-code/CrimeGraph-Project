import React, { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../utils/api'
import { useGraphData } from '../hooks/useGraphData'

export default function CaseReports() {
  const { stats, refresh } = useGraphData()
  const navigate = useNavigate()
  const fileInputRef = useRef(null)
  const [text, setText] = useState('')
  const [uploading, setUploading] = useState(false)
  const [results, setResults] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [uploadHistory, setUploadHistory] = useState([])

  const handleExtract = async () => {
    if (!text.trim()) return
    setUploading(true)
    try {
      const res = await api.uploadText(text)
      setResults(res)
      setUploadHistory(prev => [{ type: 'text', label: 'Pasted report', time: new Date().toLocaleTimeString(), entities: Object.values(res.results?.[0]?.entities || {}).flat().length }, ...prev])
      await refresh()
    } catch (e) {
      setResults({ success: false, message: e.message })
    } finally {
      setUploading(false)
    }
  }

  const handleFileDrop = async (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0] || e.target.files?.[0]
    if (!file) return

    setUploading(true)
    try {
      const res = await api.uploadFile(file)
      setResults(res)
      const count = res.results?.reduce((acc, r) => acc + (r.count || Object.values(r.entities || {}).flat().length || 0), 0) || 0
      setUploadHistory(prev => [{ type: 'file', label: file.name, time: new Date().toLocaleTimeString(), entities: count }, ...prev])
      await refresh()
    } catch (err) {
      setResults({ success: false, message: err.message })
    } finally {
      setUploading(false)
    }
  }

  const handleReset = async () => {
    try {
      await api.reset()
      setResults(null)
      setText('')
      setUploadHistory([])
      await refresh()
    } catch (e) {
      console.error(e)
    }
  }

  const hasData = stats?.total_entities > 0

  return (
    <div className="case-reports">
      {/* Hero Header */}
      <div className="intake-hero">
        <div className="intake-hero-text">
          <h2>Case Intake</h2>
          <p>Upload case documents, paste reports, or enter notes. The AI extracts entities and builds the intelligence graph automatically.</p>
        </div>
        {hasData && (
          <div className="intake-hero-actions">
            <button className="btn btn-primary" onClick={() => navigate('/graph')}>
              View Network Graph
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </button>
          </div>
        )}
      </div>

      <div className="intake-grid">
        {/* Left: Input */}
        <div className="intake-input-col">
          {/* Upload Zone */}
          <div
            className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleFileDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.json,.csv"
              onChange={handleFileDrop}
              style={{ display: 'none' }}
            />
            <div className="upload-zone-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            </div>
            <h3>Drop files here</h3>
            <p>.txt, .json, or .csv</p>
          </div>

          {/* Divider */}
          <div className="intake-divider"><span>or paste text</span></div>

          {/* Text Input */}
          <div className="text-input-section">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste an investigator report, case notes, or intelligence summary..."
              rows={10}
            />
            <div className="text-input-actions">
              <button className="btn btn-primary" onClick={handleExtract} disabled={!text.trim() || uploading}>
                {uploading ? (
                  <><span className="spinner-sm" /> Analyzing...</>
                ) : (
                  <>Extract &amp; Analyze</>
                )}
              </button>
              {hasData && (
                <button className="btn btn-ghost" onClick={handleReset}>
                  Clear All Data
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Right: Status & Results */}
        <div className="intake-status-col">
          {/* Upload History */}
          {uploadHistory.length > 0 && (
            <div className="status-card">
              <h4>Upload History</h4>
              <div className="upload-history">
                {uploadHistory.map((item, i) => (
                  <div key={i} className="history-item">
                    <div className="history-dot" />
                    <div className="history-info">
                      <span className="history-label">{item.label}</span>
                      <span className="history-meta">{item.type} &middot; {item.time} &middot; {item.entities} entities</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Extraction Results */}
          {results && results.success !== false && (
            <div className="status-card">
              <h4>Extraction Results</h4>
              {results.results?.map((r, i) => (
                <div key={i} className="result-section">
                  {r.entities && Object.entries(r.entities).map(([type, items]) => (
                    items?.length > 0 && (
                      <div key={type} className="entity-group">
                        <h5>{type.charAt(0).toUpperCase() + type.slice(1)} ({items.length})</h5>
                        <div className="entity-tags">
                          {items.map((item, j) => (
                            <span key={j} className={`tag tag-${type === 'people' ? 'person' : type}`}>{item}</span>
                          ))}
                        </div>
                      </div>
                    )
                  ))}
                  {r.relations?.length > 0 && (
                    <div className="entity-group">
                      <h5>Relations ({r.relations.length})</h5>
                      <div className="relations-list">
                        {r.relations.map((rel, j) => (
                          <div key={j} className="relation-line">
                            <span className="tag tag-person">{rel.source || rel.a}</span>
                            <span className="relation-type">{rel.relation_type || rel.relation}</span>
                            <span className="tag tag-person">{rel.target || rel.b}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
              {results.anomalies?.length > 0 && (
                <div className="anomaly-results">
                  <h5>Anomalies ({results.anomalies.length})</h5>
                  {results.anomalies.map((a, i) => (
                    <div key={i} className={`anomaly-line ${a.severity}`}>
                      <span className={`severity-dot ${a.severity}`} />
                      <span>{a.description}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Current Graph Stats */}
          {hasData && (
            <div className="status-card">
              <h4>Current Graph</h4>
              <div className="stat-bars">
                {[
                  { label: 'Persons', value: stats.persons_identified, max: 20, color: '#ef4444' },
                  { label: 'Vehicles', value: stats.vehicles_tracked, max: 10, color: '#f59e0b' },
                  { label: 'Locations', value: stats.locations_mapped, max: 15, color: '#10b981' },
                  { label: 'Phones', value: stats.phones_traced, max: 15, color: '#3b82f6' },
                  { label: 'Financial', value: stats.financial_links, max: 10, color: '#a78bfa' },
                ].map(s => (
                  <div key={s.label} className="stat-bar-row">
                    <span className="stat-bar-label">{s.label}</span>
                    <div className="stat-bar-track">
                      <div className="stat-bar-fill" style={{ width: `${Math.min(100, (s.value / s.max) * 100)}%`, background: s.color }} />
                    </div>
                    <span className="stat-bar-value">{s.value}</span>
                  </div>
                ))}
              </div>
              <div className="stat-summary">
                <span>{stats.connections} connections</span>
                <span className="separator">|</span>
                <span>{stats.high_risk_connections} high risk</span>
              </div>
            </div>
          )}

          {/* Empty State */}
          {!hasData && !results && (
            <div className="status-card empty-state">
              <div className="empty-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.3"><circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M8.5 8.5l7 7M15.5 8.5l-7 7"/></svg>
              </div>
              <p>No data loaded yet. Upload a file or paste a report to begin analysis.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
