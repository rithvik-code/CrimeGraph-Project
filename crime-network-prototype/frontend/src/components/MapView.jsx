import React, { useEffect, useState, useMemo } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, CircleMarker, Tooltip, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { api } from '../utils/api'

// Fix Leaflet default marker icon issue
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

const NODE_COLORS = {
  person: '#ef4444',
  phone: '#3b82f6',
  location: '#10b981',
  vehicle: '#f59e0b',
  financial: '#a78bfa',
  organization: '#ec4899',
  email: '#06b6d4',
  date: '#f472b6',
  ip_address: '#fb923c',
  address: '#84cc16',
}

const NODE_SIZES = {
  person: 10,
  phone: 7,
  location: 14,
  vehicle: 8,
  financial: 8,
  organization: 8,
  email: 7,
  date: 6,
  ip_address: 7,
  address: 8,
}

const NODE_ICONS = {
  person: '👤',
  phone: '📱',
  location: '📍',
  vehicle: '🚗',
  financial: '💰',
  organization: '🏢',
  email: '✉️',
  date: '📅',
  ip_address: '🌐',
  address: '🏠',
}

// Tile layer presets — real earth maps
const TILE_PRESETS = {
  satellite: {
    name: 'Satellite',
    tiles: [
      {
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
      },
    ],
  },
  hybrid: {
    name: 'Hybrid',
    tiles: [
      {
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attribution: 'Tiles &copy; Esri',
      },
      {
        url: 'https://stamen-tiles.a.ssl.fastly.net/toner-labels/{z}/{x}/{y}.png',
        attribution: 'Labels &copy; Stamen',
        opacity: 0.8,
      },
    ],
  },
  street: {
    name: 'Street',
    tiles: [
      {
        url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attribution: '&copy; OpenStreetMap contributors',
      },
    ],
  },
  dark: {
    name: 'Dark',
    tiles: [
      {
        url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
      },
    ],
  },
}

// Fit map to bounds component
function FitBounds({ bounds }) {
  const map = useMap()
  useEffect(() => {
    if (bounds) {
      const latLngBounds = L.latLngBounds(
        [bounds.south, bounds.west],
        [bounds.north, bounds.east]
      )
      map.fitBounds(latLngBounds, { padding: [40, 40] })
    }
  }, [bounds, map])
  return null
}

// Map click handler to deselect
function MapClickHandler({ onNodeSelect }) {
  const map = useMap()
  useEffect(() => {
    const handler = () => onNodeSelect(null)
    map.on('click', handler)
    return () => map.off('click', handler)
  }, [map, onNodeSelect])
  return null
}

export default function MapView() {
  const [geoData, setGeoData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [showLabels, setShowLabels] = useState(true)
  const [filterType, setFilterType] = useState('all')
  const [mapStyle, setMapStyle] = useState('satellite')

  useEffect(() => {
    loadGeoData()
  }, [])

  const loadGeoData = async () => {
    try {
      setLoading(true)
      const data = await api.getGeoData()
      setGeoData(data)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Separate nodes and edges
  const { nodes, edges, geocodedLocations } = useMemo(() => {
    if (!geoData) return { nodes: [], edges: [], geocodedLocations: {} }

    const n = []
    const e = []
    for (const item of geoData.elements) {
      if ('source' in (item.data || {})) {
        e.push(item)
      } else {
        n.push(item)
      }
    }
    return { nodes: n, edges: e, geocodedLocations: geoData.geocoded_locations || {} }
  }, [geoData])

  // Filter nodes by type
  const filteredNodes = useMemo(() => {
    if (filterType === 'all') return nodes
    return nodes.filter(n => n.data.nodeType === filterType)
  }, [nodes, filterType])

  // Get only geocoded nodes with coordinates
  const visibleNodes = useMemo(() => {
    return filteredNodes.filter(n => n.data.lat && n.data.lng)
  }, [filteredNodes])

  // Build edges that connect two visible nodes
  const visibleEdges = useMemo(() => {
    const visibleIds = new Set(visibleNodes.map(n => n.data.id))
    return edges.filter(e => visibleIds.has(e.data.source) && visibleIds.has(e.data.target))
  }, [edges, visibleNodes])

  // Build a position lookup for edge drawing
  const posLookup = useMemo(() => {
    const lookup = {}
    for (const n of visibleNodes) {
      lookup[n.data.id] = [n.data.lat, n.data.lng]
    }
    return lookup
  }, [visibleNodes])

  // Count nodes by type
  const nodeCounts = useMemo(() => {
    const counts = {}
    for (const n of visibleNodes) {
      const t = n.data.nodeType || 'unknown'
      counts[t] = (counts[t] || 0) + 1
    }
    return counts
  }, [visibleNodes])

  // Center of map
  const center = useMemo(() => {
    if (geoData?.bounds) {
      return [
        (geoData.bounds.north + geoData.bounds.south) / 2,
        (geoData.bounds.east + geoData.bounds.west) / 2,
      ]
    }
    return [20.5937, 78.9629] // Center of India
  }, [geoData])

  if (loading) {
    return (
      <div className="map-loading">
        <div className="spinner" />
        <p>Loading geographic data...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="map-error">
        <p>Error loading map data: {error}</p>
        <button className="btn btn-primary" onClick={loadGeoData}>Retry</button>
      </div>
    )
  }

  if (!geoData || visibleNodes.length === 0) {
    return (
      <div className="empty-graph">
        <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="0.6" opacity="0.15">
          <circle cx="12" cy="12" r="10" />
          <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
        </svg>
        <h3>No geographic data available</h3>
        <p>Upload case documents with location names to see them on the map.</p>
      </div>
    )
  }

  const currentTiles = TILE_PRESETS[mapStyle] || TILE_PRESETS.satellite

  return (
    <div className="map-view">
      <div className="map-header">
        <div>
          <h2>Geographic Intelligence Map</h2>
          <p>{visibleNodes.length} entities mapped across {Object.keys(geocodedLocations).length} locations</p>
        </div>
        <div className="map-controls">
          <div className="map-filter-group">
            <label>Entities:</label>
            <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
              <option value="all">All ({visibleNodes.length})</option>
              {nodeCounts.person && <option value="person">Persons ({nodeCounts.person})</option>}
              {nodeCounts.location && <option value="location">Locations ({nodeCounts.location})</option>}
              {nodeCounts.vehicle && <option value="vehicle">Vehicles ({nodeCounts.vehicle})</option>}
              {nodeCounts.phone && <option value="phone">Phones ({nodeCounts.phone})</option>}
              {nodeCounts.financial && <option value="financial">Financial ({nodeCounts.financial})</option>}
              {nodeCounts.email && <option value="email">Emails ({nodeCounts.email})</option>}
              {nodeCounts.date && <option value="date">Dates ({nodeCounts.date})</option>}
              {nodeCounts.ip_address && <option value="ip_address">IPs ({nodeCounts.ip_address})</option>}
              {nodeCounts.address && <option value="address">Addresses ({nodeCounts.address})</option>}
            </select>
          </div>
          <div className="map-filter-group">
            <label>Map:</label>
            <select value={mapStyle} onChange={(e) => setMapStyle(e.target.value)}>
              <option value="satellite">Satellite</option>
              <option value="hybrid">Hybrid</option>
              <option value="street">Street</option>
              <option value="dark">Dark</option>
            </select>
          </div>
          <label className="map-toggle">
            <input type="checkbox" checked={showLabels} onChange={(e) => setShowLabels(e.target.checked)} />
            Labels
          </label>
          <button className="btn btn-ghost btn-sm" onClick={loadGeoData}>Refresh</button>
        </div>
      </div>

      <div className="map-container">
        <MapContainer
          center={center}
          zoom={5}
          style={{ height: '100%', width: '100%' }}
          zoomControl={true}
          scrollWheelZoom={true}
        >
          {/* Main tile layer */}
          {currentTiles.tiles.map((tile, i) => (
            <TileLayer
              key={`${mapStyle}-${i}`}
              attribution={tile.attribution}
              url={tile.url}
              opacity={tile.opacity ?? 1}
              maxZoom={19}
            />
          ))}

          <FitBounds bounds={geoData.bounds} />
          <MapClickHandler onNodeSelect={setSelectedNode} />

          {/* Draw edges as polylines */}
          {visibleEdges.map((edge, i) => {
            const start = posLookup[edge.data.source]
            const end = posLookup[edge.data.target]
            if (!start || !end) return null

            const isHigh = edge.data.priority === 'high' || edge.classes?.includes('high')
            return (
              <Polyline
                key={`edge-${i}`}
                positions={[start, end]}
                pathOptions={{
                  color: isHigh ? '#ef4444' : '#60a5fa',
                  weight: isHigh ? 3 : 1.5,
                  opacity: isHigh ? 0.9 : 0.5,
                  dashArray: isHigh ? null : '8 4',
                }}
              >
                <Tooltip direction="top" offset={[0, -10]}>
                  <div className="edge-tooltip">
                    <strong>{edge.data.source}</strong> &rarr; <strong>{edge.data.target}</strong>
                    <br />
                    {edge.data.label}
                    {edge.data.confidence > 0 && <span className="confidence-badge"> {edge.data.confidence}%</span>}
                  </div>
                </Tooltip>
              </Polyline>
            )
          })}

          {/* Draw nodes */}
          {visibleNodes.map((node) => {
            const pos = [node.data.lat, node.data.lng]
            const type = node.data.nodeType
            const color = NODE_COLORS[type] || '#999'
            const size = NODE_SIZES[type] || 8
            const isSelected = selectedNode?.id === node.data.id

            return (
              <CircleMarker
                key={node.data.id}
                center={pos}
                radius={isSelected ? size + 4 : size}
                pathOptions={{
                  color: isSelected ? '#ffffff' : color,
                  fillColor: color,
                  fillOpacity: 0.9,
                  weight: isSelected ? 3 : 2,
                  opacity: 1,
                }}
                eventHandlers={{
                  click: () => setSelectedNode(selectedNode?.id === node.data.id ? null : node.data),
                }}
              >
                {showLabels && (
                  <Tooltip permanent direction="bottom" offset={[0, 8]} className="node-label-tooltip">
                    <span style={{ color: color, fontWeight: 600 }}>{node.data.label}</span>
                  </Tooltip>
                )}
                <Popup>
                  <div className="map-popup">
                    <div className="popup-header">
                      <span className="popup-type" style={{ background: color }}>{NODE_ICONS[type] || ''} {type}</span>
                      <h4>{node.data.label}</h4>
                    </div>
                    {node.data.geocoded && (
                      <p className="popup-coords">
                        {node.data.lat.toFixed(4)}, {node.data.lng.toFixed(4)}
                      </p>
                    )}
                    <button className="btn btn-primary btn-sm" onClick={() => setSelectedNode(node.data)}>
                      View Details
                    </button>
                  </div>
                </Popup>
              </CircleMarker>
            )
          })}
        </MapContainer>

        {/* Legend overlay */}
        <div className="map-legend">
          <h4>Legend</h4>
          <div className="legend-items">
            {Object.entries(NODE_COLORS).map(([type, color]) => (
              <div key={type} className="legend-item">
                <span className="legend-dot" style={{ background: color }} />
                <span>{NODE_ICONS[type]} {type.charAt(0).toUpperCase() + type.slice(1)}</span>
              </div>
            ))}
            <div className="legend-divider" />
            <div className="legend-item">
              <span className="legend-line" style={{ background: '#ef4444', height: 3, width: 20 }} />
              <span>High Priority</span>
            </div>
            <div className="legend-item">
              <span className="legend-line" style={{ background: '#60a5fa', height: 2, width: 20 }} />
              <span>Supporting</span>
            </div>
          </div>
        </div>

        {/* Geocoded locations list */}
        {Object.keys(geocodedLocations).length > 0 && (
          <div className="map-locations-list">
            <h4>Geocoded Locations ({Object.keys(geocodedLocations).length})</h4>
            {Object.entries(geocodedLocations).map(([name, coords]) => (
              <div key={name} className="location-item">
                <span className="location-dot" style={{ background: NODE_COLORS.location }} />
                <div>
                  <span className="location-name">{name}</span>
                  <span className="location-coords">{coords.lat.toFixed(2)}, {coords.lng.toFixed(2)}</span>
                  {coords.state && <span className="location-state">{coords.state}, {coords.country}</span>}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Selected node details panel */}
        {selectedNode && (
          <div className="map-details-panel">
            <div className="panel-header">
              <span className="panel-type" style={{ background: NODE_COLORS[selectedNode.nodeType] }}>
                {NODE_ICONS[selectedNode.nodeType]} {selectedNode.nodeType}
              </span>
              <h3>{selectedNode.label}</h3>
              <button className="panel-close" onClick={() => setSelectedNode(null)}>&times;</button>
            </div>
            {selectedNode.geocoded && (
              <div className="panel-coords">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                  <circle cx="12" cy="10" r="3" />
                </svg>
                <span>{selectedNode.lat.toFixed(4)}, {selectedNode.lng.toFixed(4)}</span>
              </div>
            )}
            <div className="panel-connections">
              <h4>Connected Entities</h4>
              {visibleEdges
                .filter(e => e.data.source === selectedNode.id || e.data.target === selectedNode.id)
                .map((edge, i) => {
                  const otherId = edge.data.source === selectedNode.id ? edge.data.target : edge.data.source
                  const otherNode = nodes.find(n => n.data.id === otherId)
                  return (
                    <div key={i} className="panel-connection">
                      <span className="conn-dot" style={{ background: NODE_COLORS[otherNode?.data.nodeType] || '#999' }} />
                      <span className="conn-name">{otherId}</span>
                      <span className="conn-rel">{edge.data.label}</span>
                      {edge.data.confidence > 0 && <span className="conn-conf">{edge.data.confidence}%</span>}
                    </div>
                  )
                })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
