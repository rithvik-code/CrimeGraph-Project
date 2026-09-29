import React, { useState, useRef, useCallback } from 'react'
import { api } from '../utils/api'

export default function ReportExport() {
  const [generating, setGenerating] = useState(false)
  const [title, setTitle] = useState('CrimeGraph AI Investigation Report')
  const [html, setHtml] = useState(null)
  const [includeGraph, setIncludeGraph] = useState(true)
  const [exportingPdf, setExportingPdf] = useState(false)
  const iframeRef = useRef(null)

  const captureGraph = useCallback(() => {
    const cyEl = document.querySelector('.cytoscape-container canvas')
    if (!cyEl) return null
    try {
      const dataUrl = cyEl.toDataURL('image/png')
      return dataUrl
    } catch {
      return null
    }
  }, [])

  const generate = async () => {
    setGenerating(true)
    try {
      const result = await api.generateReport({ title })
      let reportHtml = result.html

      // Inject graph screenshot if available
      if (includeGraph) {
        const graphImg = captureGraph()
        if (graphImg) {
          const graphSection = `
            <div class="section">
              <div class="section-title"><span class="icon">&#127760;</span> Network Graph Visualization</div>
              <div style="text-align:center;margin:16px 0">
                <img src="${graphImg}" style="max-width:100%;border-radius:12px;border:1px solid rgba(0,240,255,0.15);box-shadow:0 0 30px rgba(0,240,255,0.1)" alt="Network Graph" />
              </div>
            </div>`
          reportHtml = reportHtml.replace(
            '<div class="section"><div class="section-title"><span class="icon">&#128269;</span> Extracted Entities</div>',
            graphSection + '\n<div class="section"><div class="section-title"><span class="icon">&#128269;</span> Extracted Entities</div>'
          )
        }
      }

      setHtml(reportHtml)
    } catch (e) {
      console.error('Report generation failed:', e)
    }
    setGenerating(false)
  }

  const downloadHtml = () => {
    if (!html) return
    const blob = new Blob([html], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = title.replace(/[^a-z0-9]/gi, '_') + '.html'
    a.click()
    URL.revokeObjectURL(url)
  }

  const downloadPdf = async () => {
    if (!html) return
    setExportingPdf(true)
    try {
      const html2pdf = (await import('html2pdf.js')).default
      const container = document.createElement('div')
      container.innerHTML = html
      container.style.background = '#05070e'
      document.body.appendChild(container)

      await html2pdf()
        .set({
          margin: [10, 10],
          filename: title.replace(/[^a-z0-9]/gi, '_') + '.pdf',
          image: { type: 'jpeg', quality: 0.95 },
          html2canvas: { scale: 2, backgroundColor: '#05070e', useCORS: true },
          jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
          pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
        })
        .from(container)
        .save()

      document.body.removeChild(container)
    } catch (e) {
      console.error('PDF export failed:', e)
      // Fallback: open in new tab for print-to-PDF
      const win = window.open('', '_blank')
      if (win) {
        win.document.write(html)
        win.document.close()
      }
    }
    setExportingPdf(false)
  }

  return (
    <div className="report-export">
      <h3>REPORT EXPORT</h3>
      <div className="report-form">
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="report-title-input"
          placeholder="Report title..."
        />
        <label className="report-checkbox">
          <input
            type="checkbox"
            checked={includeGraph}
            onChange={(e) => setIncludeGraph(e.target.checked)}
          />
          <span>Include network graph screenshot</span>
        </label>
        <div className="report-actions">
          <button className="btn btn-primary" onClick={generate} disabled={generating}>
            {generating ? (
              <><span className="spinner-sm" /> Generating...</>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/></svg>
                Generate Report
              </>
            )}
          </button>
          {html && (
            <>
              <button className="btn" onClick={downloadHtml}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5"/><path d="M12 15V3"/></svg>
                Download HTML
              </button>
              <button className="btn btn-primary" onClick={downloadPdf} disabled={exportingPdf}>
                {exportingPdf ? (
                  <><span className="spinner-sm" /> Exporting...</>
                ) : (
                  <>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>
                    Export PDF
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>
      {html && (
        <div className="report-preview">
          <h4>Preview</h4>
          <iframe
            ref={iframeRef}
            srcDoc={html}
            title="Report Preview"
            className="report-iframe"
          />
        </div>
      )}
    </div>
  )
}
