import React, { useState, useRef, useEffect } from 'react'
import { api } from '../utils/api'

export default function SmartSearch({ onEntitySelect }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [isOpen, setIsOpen] = useState(false)
  const inputRef = useRef(null)
  const wrapperRef = useRef(null)

  useEffect(() => {
    const h = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); inputRef.current?.focus(); setIsOpen(true) }
      if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) { e.preventDefault(); inputRef.current?.focus(); setIsOpen(true) }
    }
    document.addEventListener('keydown', h)
    return () => document.removeEventListener('keydown', h)
  }, [])

  useEffect(() => {
    if (!query.trim()) { setResults([]); return }
    const t = setTimeout(async () => {
      try { setResults(await api.search(query)) } catch(e) {}
    }, 300)
    return () => clearTimeout(t)
  }, [query])

  useEffect(() => {
    const h = (e) => { if (wrapperRef.current && !wrapperRef.current.contains(e.target)) setIsOpen(false) }
    document.addEventListener('mousedown', h)
    return () => document.removeEventListener('mousedown', h)
  }, [])

  return (
    <div className="smart-search" ref={wrapperRef}>
      <div className="search-input-wrapper" onClick={() => setIsOpen(true)}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input ref={inputRef} type="text" placeholder="Search entities... (Ctrl+K)" value={query} onChange={e => setQuery(e.target.value)} onFocus={() => setIsOpen(true)} className="search-input" />
        <span className="search-shortcut">Ctrl+K</span>
      </div>
      {isOpen && results.length > 0 && (
        <div className="search-dropdown">
          {results.map((r, i) => (
            <div key={i} className="search-result" onClick={() => { onEntitySelect?.(r.id); setIsOpen(false); setQuery('') }}>
              <span className="search-result-dot" style={{ background: r.color }} />
              <span className="search-result-name">{r.id}</span>
              <span className="search-result-type">{r.type}</span>
              <span className="search-result-score">{Math.round(r.score * 100)}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
