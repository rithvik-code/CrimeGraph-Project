import React, { useState } from 'react'
import { api } from '../utils/api'
export default function CaseComparison() {
  const [reports, setReports] = useState([{ label: 'Report 1', text: '' }, { label: 'Report 2', text: '' }])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const add = () => setReports([...reports, { label: 'Report ' + (reports.length + 1), text: '' }])
  const upd = (i, f, v) => { const r = [...reports]; r[i][f] = v; setReports(r) }
  const cmp = async () => { const v = reports.filter(r => r.text.trim()); if (v.length < 2) return; setLoading(true); try { setResult(await api.compareCases(v)) } catch(e){} setLoading(false) }
  return (<div className="case-comparison"><h3>CASE COMPARISON</h3>
    <p>Paste multiple reports to find shared entities across cases.</p>
    <div className="compare-inputs">{reports.map((r, i) => <div key={i} className="compare-report"><input type="text" value={r.label} onChange={e => upd(i, 'label', e.target.value)} className="compare-label" /><textarea value={r.text} onChange={e => upd(i, 'text', e.target.value)} placeholder="Paste report..." rows={5} /></div>)}</div>
    <div className="compare-actions"><button className="btn btn-ghost" onClick={add}>+ Add Report</button><button className="btn btn-primary" onClick={cmp} disabled={loading}>{loading ? 'Comparing...' : 'Compare'}</button></div>
    {result && <div className="compare-results"><h4>{result.total_shared} shared entities found</h4>
      {result.shared_entities.map((e, i) => <div key={i} className="shared-entity"><span className="shared-name">{e.name}</span><span className="shared-type">{e.type}</span><span>in: {e.found_in.join(', ')}</span></div>)}</div>}
  </div>)
}
