const API_BASE = '/api';

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const isFormData = options.body instanceof FormData;
  const headers = isFormData ? options.headers : { 'Content-Type': 'application/json', ...options.headers };
  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || 'API request failed');
  }
  return res.json();
}

export const api = {
  getStats: () => request('/stats'),
  getGraphData: () => request('/graph-data'),
  getGeoData: () => request('/geo-data'),
  getConnections: () => request('/connections'),
  getAllEdges: () => request('/all-edges'),
  getAnomalies: () => request('/anomalies'),
  getNodeDetails: (id) => request(`/node/${encodeURIComponent(id)}`),
  getPath: (source, target) => request(`/path?source=${encodeURIComponent(source)}&target=${encodeURIComponent(target)}`),
  uploadText: (text, sourceName = 'pasted_text') =>
    request('/upload-text', { method: 'POST', body: JSON.stringify({ text, source_name: sourceName }) }),
  uploadFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/upload-file`, { method: 'POST', body: formData });
    if (!res.ok) throw new Error('Upload failed');
    return res.json();
  },
  loadCases: (cases) => request('/load-cases', { method: 'POST', body: JSON.stringify({ cases }) }),
  reset: () => request('/reset', { method: 'POST' }),

  // Investigator Productivity Suite
  getTimeline: () => request('/timeline'),
  addNote: (data) => request('/notes', { method: 'POST', body: JSON.stringify(data) }),
  getNotes: (entityId) => request(entityId ? '/notes?entity_id=' + encodeURIComponent(entityId) : '/notes'),
  deleteNote: (id) => fetch(`${API_BASE}/notes/${id}`, { method: 'DELETE' }).then(r => r.json()),
  search: (q, limit) => request('/search?q=' + encodeURIComponent(q) + '&limit=' + (limit || 20)),
  getEntityProfile: (id) => request('/entity/' + encodeURIComponent(id) + '/profile'),
  getRiskScores: () => request('/risk-scores'),
  generateReport: (data) => request('/generate-report', { method: 'POST', body: JSON.stringify(data) }),
  compareCases: (reports) => request('/compare-cases', { method: 'POST', body: JSON.stringify({ reports }) }),
  addWatchlist: (data) => request('/watchlist', { method: 'POST', body: JSON.stringify(data) }),
  getWatchlist: () => request('/watchlist'),
  removeWatchlist: (id) => fetch(`${API_BASE}/watchlist/${id}`, { method: 'DELETE' }).then(r => r.json()),
  checkWatchlist: () => request('/check-watchlist'),

  // Crime News Globe
  getCrimeNews: () => request('/crime-news'),
};
