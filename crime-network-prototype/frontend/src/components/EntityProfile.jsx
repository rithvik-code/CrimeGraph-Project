import React, { useState, useEffect } from 'react'
import { api } from '../utils/api'

export default function EntityProfile({ entityId, onClose }) {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [noteText, setNoteText] = useState('')
  const [noteTag, setNoteTag] = useState('general')

  useEffect(() => {
    if (!entityId) return
    setLoading(true)
    api.getEntityProfile(entityId).then(setProfile).catch(console.error).finally(() => setLoading(false))
  }, [entityId])

  const addNote = async () => {
    if (!noteText.trim()) return
    await api.addNote({ entity_id: entityId, entity_type: profile?.type || 'unknown', content: noteText, tag: noteTag })
    setNoteText('')
    const p = await api.getEntityProfile(entityId)
    setProfile(p)
  }

  const tc = { person: '#ef4444', location: '#10b981', phone: '#3b82f6', vehicle: '#f59e0b', financial: '#a78bfa', email: '#06b6d4', date: '#f472b6', ip_address: '#fb923c', address: '#84cc16' }
  if (!entityId) return null
  if (loading) return <div className="profile-panel"><div className="loading"><div className="spinner" /></div></div>
  if (!profile) return <div className="profile-panel"><p>Not found</p></div>

  return (
    <div className="profile-panel">
      <div className="profile-header">
        <div className="profile-title"><span className="profile-dot" style={{ background: tc[profile.type] }} /><h3>{profile.id}</h3><span className="profile-type">{profile.type}</span></div>
        <button className="btn-close" onClick={onClose}>X</button>
      </div>
      <div className="profile-stats">
        <div className="pstat"><span className="pstat-num">{profile.degree}</span><span className="pstat-label">Connections</span></div>
        <div className="pstat"><span className="pstat-num">{profile.note_count}</span><span className="pstat-label">Notes</span></div>
        <div className="pstat"><span className="pstat-num">{profile.timeline.length}</span><span className="pstat-label">Dates</span></div>
      </div>
      <div className="profile-section"><h4>Add Note</h4>
        <div className="note-form">
          <textarea value={noteText} onChange={e => setNoteText(e.target.value)} placeholder="Add note..." rows={2} />
          <div className="note-form-actions">
            <select value={noteTag} onChange={e => setNoteTag(e.target.value)}>
              <option value="general">General</option><option value="suspicious">Suspicious</option><option value="confirmed">Confirmed</option><option value="needs-review">Needs Review</option>
            </select>
            <button className="btn btn-primary btn-sm" onClick={addNote} disabled={!noteText.trim()}>Add</button>
          </div>
        </div>
      </div>
      {profile.notes.length > 0 && <div className="profile-section"><h4>Notes ({profile.notes.length})</h4>
        {profile.notes.map(n => <div key={n.id} className={'note-item note-' + n.tag}><div className="note-meta"><span className="note-tag">{n.tag}</span> {n.author}</div><p>{n.content}</p></div>)}
      </div>}
      {Object.entries(profile.connections).map(([type, items]) => <div key={type} className="profile-section"><h4>{type} ({items.length})</h4>
        {items.slice(0, 8).map(c => <div key={c.name} className="connection-item"><span className="conn-dot" style={{ background: tc[type] }} /><span className="conn-name">{c.name}</span><span className="conn-rels">{c.relations.join(', ')}</span></div>)}
      </div>)}
    </div>
  )
}
