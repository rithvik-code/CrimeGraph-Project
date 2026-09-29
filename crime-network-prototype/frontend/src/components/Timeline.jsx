import React, { useState, useEffect, useRef } from 'react'
import { api } from '../utils/api'

export default function Timeline() {
  const [events, setEvents] = useState([])
  const [filtered, setFiltered] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => { api.getTimeline().then(d => { setEvents(d); setFiltered(d) }).catch(console.error).finally(() => setLoading(false)) }, [])

  useEffect(() => {
    let result = events
    if (filter !== 'all') result = result.filter(e => e.entity_type === filter)
    if (searchTerm) result = result.filter(e => e.entity.toLowerCase().includes(searchTerm.toLowerCase()) || e.date.toLowerCase().includes(searchTerm.toLowerCase()))
    setFiltered(result)
  }, [filter, searchTerm, events])

  const entityTypes = [...new Set(events.map(e => e.entity_type))]
  const typeColors = { person: '#ef4444', location: '#10b981', phone: '#3b82f6', vehicle: '#f59e0b', financial: '#a78bfa', email: '#06b6d4', date: '#f472b6', ip_address: '#fb923c', address: '#84cc16' }

  if (loading) return <div className="loading"><div className="spinner" /><p>Loading timeline...</p></div>

  return (
    <div className="timeline-section">
      <div className="timeline-header">
        <h3>INVESTIGATION TIMELINE</h3>
        <div className="timeline-controls">
          <input type="text" placeholder="Search events..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} className="timeline-search" />
          <div className="timeline-filters">
            <button className={'filter-btn ' + (filter === 'all' ? 'active' : '')} onClick={() => setFilter('all')}>All ({events.length})</button>
            {entityTypes.map(t => (
              <button key={t} className={'filter-btn ' + (filter === t ? 'active' : '')} onClick={() => setFilter(t)}>
                {t.replace(/_/g, ' ')} ({events.filter(e => e.entity_type === t).length})
              </button>
            ))}
          </div>
        </div>
      </div>
      <div className="timeline-container">
        <div className="timeline-line" />
        {filtered.length === 0 && <div className="empty-timeline">No events found. Extract data from case reports first.</div>}
        {filtered.map((event, i) => (
          <div key={event.id || i} className={'timeline-event ' + (i % 2 === 0 ? 'left' : 'right')}>
            <div className="timeline-dot" style={{ background: typeColors[event.entity_type] || '#666' }} />
            <div className="timeline-card">
              <div className="timeline-date">{event.date}</div>
              <div className="timeline-entity" style={{ color: typeColors[event.entity_type] }}>{event.entity}</div>
              <div className="timeline-type"><span className="type-badge" style={{ background: (typeColors[event.entity_type] || '#666') + '22', color: typeColors[event.entity_type], border: '1px solid ' + (typeColors[event.entity_type] || '#666') + '44' }}>{event.entity_type.replace(/_/g, ' ')}</span></div>
              <div className="timeline-desc">{event.description}</div>
              {event.relations && event.relations.length > 0 && <div className="timeline-rels">Relations: {event.relations.join(', ')}</div>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
