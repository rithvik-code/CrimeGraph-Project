import React, { useState, useEffect } from 'react'
import { api } from '../utils/api'
export default function Watchlist() {
  const [items, setItems] = useState([])
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [name, setName] = useState('')
  const [etype, setEtype] = useState('person')
  const load = async () => { try { const [wl, ch] = await Promise.all([api.getWatchlist(), api.checkWatchlist()]); setItems(wl); setMatches(ch.matches || []) } catch(e){} setLoading(false) }
  useEffect(() => { load() }, [])
  const add = async () => { if (!name.trim()) return; await api.addWatchlist({ name, entity_type: etype }); setName(''); load() }
  const rm = async (id) => { await api.removeWatchlist(id); load() }
  if (loading) return <div className="loading"><div className="spinner" /></div>
  return (<div className="watchlist-section"><h3>WATCHLIST</h3>
    {matches.length > 0 && <div className="watchlist-alerts"><h4>ALERTS - {matches.length} Matches</h4>
      {matches.map((m, i) => <div key={i} className="watchlist-match"><span className="match-icon">!</span> {m.watchlist_entry} <span className="match-type">{m.entity_type}</span> matches <span className="match-entity">{m.matched_graph_entity}</span></div>)}</div>}
    <div className="watchlist-add"><input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Add to watchlist..." className="watchlist-input" />
      <select value={etype} onChange={e => setEtype(e.target.value)}><option value="person">Person</option><option value="phone">Phone</option><option value="vehicle">Vehicle</option><option value="email">Email</option><option value="ip_address">IP</option><option value="financial">Financial</option><option value="location">Location</option></select>
      <button className="btn btn-primary btn-sm" onClick={add} disabled={!name.trim()}>Add</button></div>
    <div className="watchlist-list">{items.length === 0 && <p>No watchlist entries.</p>}
      {items.map(item => <div key={item.id} className="watchlist-item"><span className="wl-name">{item.name}</span><span className="wl-type">{item.entity_type}</span><button className="btn-remove" onClick={() => rm(item.id)}>X</button></div>)}</div>
  </div>)
}
