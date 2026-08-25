const API_BASE = '/api';

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || 'API request failed');
  }
  return res.json();
}

export const api = {
  // Dashboard
  getStats: () => request('/stats'),

  // Graph
  getGraphData: () => request('/graph-data'),
  getConnections: () => request('/connections'),
  getAnomalies: () => request('/anomalies'),
  getNodeDetails: (id) => request(`/node/${encodeURIComponent(id)}`),
  getPath: (source, target) =>
    request(`/path?source=${encodeURIComponent(source)}&target=${encodeURIComponent(target)}`),

  // Extraction
  uploadText: (text, sourceName = 'pasted_text') =>
    request('/upload-text', { method: 'POST', body: JSON.stringify({ text, source_name: sourceName }) }),

  uploadFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/upload-file`, { method: 'POST', body: formData });
    if (!res.ok) throw new Error('Upload failed');
    return res.json();
  },

  // Case management
  loadCases: (cases) =>
    request('/load-cases', { method: 'POST', body: JSON.stringify({ cases }) }),

  reset: () => request('/reset', { method: 'POST' }),
};
