import { useState, useEffect, useCallback } from 'react';
import { api } from '../utils/api';

export function useGraphData() {
  const [stats, setStats] = useState(null);
  const [graphData, setGraphData] = useState([]);
  const [connections, setConnections] = useState([]);
  const [allEdges, setAllEdges] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      const [s, g, c, ae, a] = await Promise.all([
        api.getStats(),
        api.getGraphData(),
        api.getConnections(),
        api.getAllEdges(),
        api.getAnomalies(),
      ]);
      setStats(s);
      setGraphData(g);
      setConnections(c);
      setAllEdges(ae);
      setAnomalies(a);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return { stats, graphData, connections, allEdges, anomalies, loading, error, refresh };
}
