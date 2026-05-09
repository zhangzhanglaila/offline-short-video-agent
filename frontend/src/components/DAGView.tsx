import React, { useEffect, useState, useCallback } from 'react';

interface DAGNode {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'done' | 'error' | 'skipped';
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
  depends_on: string[];
  error: string | null;
  cache_hit: boolean;
  started_at: number | null;
  completed_at: number | null;
  duration: number | null;
  metadata: Record<string, unknown>;
}

interface DAGData {
  name: string;
  total_duration: number;
  is_complete: boolean;
  nodes: Record<string, DAGNode>;
  edges: Array<{ from: string; to: string }>;
  stats: Record<string, number>;
}

const STATUS_COLORS: Record<string, string> = {
  pending: '#484f58',
  running: '#58a6ff',
  done: '#3fb950',
  error: '#f85149',
  skipped: '#8b949e',
};

const STATUS_ICONS: Record<string, string> = {
  pending: '○',
  running: '◉',
  done: '●',
  error: '✕',
  skipped: '◌',
};

/** DAG visualization component for the rendering pipeline. */
export const DAGView: React.FC<{ sessionId: string | null; apiUrl?: string }> = ({
  sessionId,
  apiUrl = 'http://localhost:8000',
}) => {
  const [dag, setDag] = useState<DAGData | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDAG = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${apiUrl}/api/timeline/${sessionId}/dag`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setDag(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load DAG');
    } finally {
      setLoading(false);
    }
  }, [sessionId, apiUrl]);

  useEffect(() => {
    fetchDAG();
    // Auto-refresh while pipeline is running
    if (dag && !dag.is_complete) {
      const timer = setInterval(fetchDAG, 2000);
      return () => clearInterval(timer);
    }
  }, [fetchDAG, dag?.is_complete]);

  if (!sessionId) {
    return <div className="dag-view dag-view--empty">No session</div>;
  }

  if (loading && !dag) {
    return <div className="dag-view dag-view--loading">Loading DAG...</div>;
  }

  if (error) {
    return <div className="dag-view dag-view--error">{error}</div>;
  }

  if (!dag) return null;

  const nodeEntries = Object.values(dag.nodes);
  const selected = selectedNode ? dag.nodes[selectedNode] : null;

  return (
    <div className="dag-view">
      <div className="dag-view__header">
        <h3>Pipeline: {dag.name}</h3>
        <div className="dag-view__stats">
          {Object.entries(dag.stats).map(([status, count]) => (
            <span key={status} className="dag-stat" style={{ color: STATUS_COLORS[status] || '#8b949e' }}>
              {STATUS_ICONS[status] || '?'} {count} {status}
            </span>
          ))}
          <span className="dag-stat">⏱ {dag.total_duration.toFixed(1)}s</span>
        </div>
      </div>

      <div className="dag-view__body">
        {/* Node list */}
        <div className="dag-nodes">
          {nodeEntries.map((node) => (
            <div
              key={node.id}
              className={`dag-node dag-node--${node.status} ${selectedNode === node.id ? 'dag-node--selected' : ''}`}
              onClick={() => setSelectedNode(node.id === selectedNode ? null : node.id)}
            >
              <div className="dag-node__status" style={{ color: STATUS_COLORS[node.status] }}>
                {STATUS_ICONS[node.status]}
              </div>
              <div className="dag-node__info">
                <span className="dag-node__name">{node.name}</span>
                <span className="dag-node__id">{node.id}</span>
              </div>
              <div className="dag-node__timing">
                {node.duration != null && (
                  <span className="dag-node__duration">{(node.duration * 1000).toFixed(0)}ms</span>
                )}
                {node.cache_hit && <span className="dag-node__cache">⚡cache</span>}
              </div>
            </div>
          ))}
        </div>

        {/* Node detail panel */}
        {selected && (
          <div className="dag-detail">
            <h4>{selected.name}</h4>
            <div className="dag-detail__grid">
              <div className="dag-detail__row">
                <label>Status</label>
                <span style={{ color: STATUS_COLORS[selected.status] }}>
                  {STATUS_ICONS[selected.status]} {selected.status}
                </span>
              </div>
              {selected.error && (
                <div className="dag-detail__row dag-detail__row--error">
                  <label>Error</label>
                  <span>{selected.error}</span>
                </div>
              )}
              {selected.depends_on.length > 0 && (
                <div className="dag-detail__row">
                  <label>Dependencies</label>
                  <span>{selected.depends_on.join(', ')}</span>
                </div>
              )}
              {selected.duration != null && (
                <div className="dag-detail__row">
                  <label>Duration</label>
                  <span>{(selected.duration * 1000).toFixed(1)}ms</span>
                </div>
              )}
              {Object.keys(selected.inputs).length > 0 && (
                <div className="dag-detail__row">
                  <label>Inputs</label>
                  <pre>{JSON.stringify(selected.inputs, null, 2)}</pre>
                </div>
              )}
              {Object.keys(selected.outputs).length > 0 && (
                <div className="dag-detail__row">
                  <label>Outputs</label>
                  <pre>{JSON.stringify(selected.outputs, null, 2)}</pre>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
