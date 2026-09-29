import React, { useEffect, useRef, useState, useCallback } from 'react'
import cytoscape from 'cytoscape'
import { useGraphData } from '../hooks/useGraphData'
import { api } from '../utils/api'
import MapView from './MapView'

const LAYOUTS = {
  cose: { name: 'cose', animate: true, animationDuration: 800, nodeRepulsion: 8000, idealEdgeLength: 120, gravity: 0.3 },
  breadthfirst: { name: 'breadthfirst', animate: true, spacingFactor: 1.5 },
  circle: { name: 'circle', animate: true },
  concentric: { name: 'concentric', animate: true },
}

const NODE_COLORS = {
  person: '#ef4444',
  phone: '#3b82f6',
  location: '#10b981',
  vehicle: '#f59e0b',
  financial: '#a78bfa',
  email: '#06b6d4',
  date: '#f472b6',
  ip_address: '#fb923c',
  address: '#84cc16',
}

export default function GraphView() {
  const { graphData, loading } = useGraphData()
  const cyRef = useRef(null)
  const containerRef = useRef(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedLayout, setSelectedLayout] = useState('cose')
  const [highlightPath, setHighlightPath] = useState([])
  const [pathSource, setPathSource] = useState('')
  const [pathTarget, setPathTarget] = useState('')
  const [personNodes, setPersonNodes] = useState([])
  const [viewMode, setViewMode] = useState('network') // 'network' or 'map'

  useEffect(() => {
    if (viewMode !== 'network') return
    if (!containerRef.current || graphData.length === 0) return
    if (cyRef.current) cyRef.current.destroy()

    const persons = graphData.filter(n => n.data?.nodeType === 'person').map(n => n.data.id)
    setPersonNodes(persons)

    const cy = cytoscape({
      container: containerRef.current,
      elements: graphData,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'font-size': '11px',
            'font-family': 'Inter, sans-serif',
            'font-weight': '500',
            'color': '#cbd5e1',
            'text-margin-y': 6,
            'text-outline-color': '#0f172a',
            'text-outline-width': 2,
            'width': 42,
            'height': 42,
            'background-color': 'data(color)',
            'border-width': 2,
            'border-color': '#1e293b',
          },
        },
        { selector: 'node.person', style: { 'shape': 'ellipse', 'width': 48, 'height': 48 } },
        { selector: 'node.vehicle', style: { 'shape': 'diamond', 'width': 50, 'height': 38 } },
        { selector: 'node.location', style: { 'shape': 'rectangle', 'width': 56, 'height': 32 } },
        { selector: 'node.phone', style: { 'shape': 'round-rectangle', 'width': 46, 'height': 28 } },
        { selector: 'node.financial', style: { 'shape': 'round-hexagon', 'width': 50, 'height': 38 } },
        { selector: 'node.email', style: { 'shape': 'round-rectangle', 'width': 44, 'height': 26 } },
        { selector: 'node.date', style: { 'shape': 'cut-rectangle', 'width': 48, 'height': 28 } },
        { selector: 'node.ip_address', style: { 'shape': 'barrel', 'width': 44, 'height': 30 } },
        { selector: 'node.address', style: { 'shape': 'rectangle', 'width': 52, 'height': 28 } },
        {
          selector: 'edge',
          style: {
            'width': 1.5,
            'line-color': '#334155',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '8px',
            'font-family': 'Inter, sans-serif',
            'color': '#64748b',
            'text-rotation': 'autorotate',
            'text-margin-y': -8,
            'text-outline-color': '#0f172a',
            'text-outline-width': 1.5,
          },
        },
        { selector: 'edge.high', style: { 'line-color': '#ef4444', 'width': 2.5, 'z-index': 10 } },
        { selector: '.faded', style: { 'opacity': 0.1 } },
        { selector: '.highlighted', style: { 'border-color': '#facc15', 'border-width': 3 } },
        { selector: 'edge.highlighted', style: { 'line-color': '#facc15', 'width': 3 } },
        { selector: ':selected', style: { 'border-color': '#60a5fa', 'border-width': 3 } },
      ],
      layout: LAYOUTS[selectedLayout],
      minZoom: 0.3,
      maxZoom: 3,
      wheelSensitivity: 0.2,
    })

    cy.on('tap', 'node', async (evt) => {
      const nodeId = evt.target.id()
      try {
        const details = await api.getNodeDetails(nodeId)
        setSelectedNode(details)
      } catch {
        setSelectedNode({ id: nodeId, name: nodeId, type: 'unknown', neighbors: [], degree: 0 })
      }
    })

    cy.on('tap', (evt) => { if (evt.target === cy) setSelectedNode(null) })
    cyRef.current = cy
    return () => { if (cyRef.current) cyRef.current.destroy() }
  }, [graphData, viewMode])

  const handleHighlightPath = useCallback(async () => {
    if (!pathSource || !pathTarget || !cyRef.current) return
    try {
      const result = await api.getPath(pathSource, pathTarget)
      if (result.found) {
        setHighlightPath(result.path)
        const cy = cyRef.current
        cy.elements().addClass('faded').removeClass('highlighted')
        const pathNodes = cy.nodes().filter(n => result.path.includes(n.id()))
        const pathEdges = pathNodes.connectedEdges().filter(e => {
          const src = e.source().id(), tgt = e.target().id()
          const idx = result.path.indexOf(src)
          return idx >= 0 && result.path[idx + 1] === tgt
        })
        pathNodes.removeClass('faded').addClass('highlighted')
        pathEdges.removeClass('faded').addClass('highlighted')
        cy.fit(cy.elements('.highlighted'), 50)
      }
    } catch (e) { console.error(e) }
  }, [pathSource, pathTarget])

  const resetHighlight = () => {
    if (cyRef.current) {
      cyRef.current.elements().removeClass('faded highlighted').fit(undefined, 30)
    }
    setHighlightPath([])
  }

  const applyLayout = (name) => {
    setSelectedLayout(name)
    if (cyRef.current) cyRef.current.layout(LAYOUTS[name]).run()
  }

  const hasData = graphData.length > 0

  return (
    <div className="graph-view">
      <div className="graph-header">
        <div>
          <h2>Network Analysis</h2>
          <p>{hasData ? `${graphData.filter(n => n.data?.nodeType === 'person').length} persons, ${graphData.filter(n => 'source' in (n.data || {})).length} edges` : 'No data loaded'}</p>
        </div>
        <div className="graph-controls">
          <div className="view-toggle">
            <button
              className={`toggle-btn ${viewMode === 'network' ? 'active' : ''}`}
              onClick={() => setViewMode('network')}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><circle cx="18" cy="6" r="3"/>
                <path d="M8.5 8.5l7 7M15.5 8.5l-7 7"/>
              </svg>
              Network
            </button>
            <button
              className={`toggle-btn ${viewMode === 'map' ? 'active' : ''}`}
              onClick={() => setViewMode('map')}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
              </svg>
              Geographic
            </button>
          </div>
          {viewMode === 'network' && (
            <>
              <select value={selectedLayout} onChange={(e) => applyLayout(e.target.value)}>
                <option value="cose">Force-Directed</option>
                <option value="breadthfirst">Hierarchy</option>
                <option value="circle">Circle</option>
                <option value="concentric">Concentric</option>
              </select>
              <button className="btn btn-ghost btn-sm" onClick={resetHighlight}>Reset</button>
            </>
          )}
        </div>
      </div>

      {viewMode === 'map' ? (
        <MapView />
      ) : !hasData ? (
        <div className="empty-graph">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="0.6" opacity="0.15">
            <circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><circle cx="18" cy="6" r="3"/>
            <path d="M8.5 8.5l7 7M15.5 8.5l-7 7"/>
          </svg>
          <h3>No graph data</h3>
          <p>Upload case documents to generate the network graph.</p>
        </div>
      ) : (
        <div className="graph-layout">
          <div className="graph-main">
            <div ref={containerRef} className="cytoscape-container" />
            <div className="graph-legend">
              <h4>Legend</h4>
              <div className="legend-items">
                {Object.entries(NODE_COLORS).map(([type, color]) => (
                  <div key={type} className="legend-item">
                    <span className="legend-dot" style={{ background: color }} />
                    <span>{type.charAt(0).toUpperCase() + type.slice(1)}</span>
                  </div>
                ))}
                <div className="legend-divider" />
                <div className="legend-item"><span className="legend-line high" /><span>High priority</span></div>
                <div className="legend-item"><span className="legend-line supporting" /><span>Supporting</span></div>
              </div>
            </div>
          </div>

          <div className="graph-sidebar">
            <div className="sidebar-section">
              <h4>Path Finder</h4>
              <select value={pathSource} onChange={(e) => setPathSource(e.target.value)}>
                <option value="">Source</option>
                {personNodes.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
              <select value={pathTarget} onChange={(e) => setPathTarget(e.target.value)}>
                <option value="">Target</option>
                {personNodes.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
              <div className="path-buttons">
                <button className="btn btn-primary btn-sm" onClick={handleHighlightPath} disabled={!pathSource || !pathTarget}>
                  Find Path
                </button>
                <button className="btn btn-ghost btn-sm" onClick={resetHighlight}>Clear</button>
              </div>
              {highlightPath.length > 0 && (
                <div className="path-result">
                  <p className="path-hops">{highlightPath.length - 1} hop{highlightPath.length - 1 !== 1 ? 's' : ''}</p>
                  <div className="path-chain">
                    {highlightPath.map((node, i) => (
                      <React.Fragment key={i}>
                        <span className="path-node">{node}</span>
                        {i < highlightPath.length - 1 && <span className="path-arrow">&rarr;</span>}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {selectedNode && (
              <div className="sidebar-section">
                <h4>Entity Detail</h4>
                <div className="detail-header">
                  <span className={`detail-type-badge ${selectedNode.type}`}>{selectedNode.type}</span>
                  <h3>{selectedNode.name}</h3>
                </div>
                <p className="detail-meta">{selectedNode.degree} connection{selectedNode.degree !== 1 ? 's' : ''}</p>
                {selectedNode.neighbors?.length > 0 && (
                  <div className="neighbors-list">
                    <h5>Connected</h5>
                    {selectedNode.neighbors.map((n, i) => (
                      <div key={i} className="neighbor-item">
                        <span className={`tag tag-${n.type}`}>{n.name}</span>
                        <div className="neighbor-meta">
                          {n.relations.slice(0, 2).map((r, j) => (
                            <span key={j} className="tag tag-relation">{r}</span>
                          ))}
                          <span className="confidence-text">{n.confidence}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
