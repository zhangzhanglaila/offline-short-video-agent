import React, { useEffect, useState, useCallback } from 'react';
import { fetchAssets } from '../api/backend';

interface Asset {
  id?: string;
  content_hash?: string;
  asset_type?: string;
  path?: string;
  metadata?: Record<string, unknown>;
}

/** Side panel for browsing and selecting assets from the AssetStore. */
export const AssetPanel: React.FC<{ sessionId: string | null }> = ({ sessionId }) => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const loadAssets = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchAssets(sessionId, filter || undefined);
      setAssets(resp.assets);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load assets');
      setAssets([]);
    } finally {
      setLoading(false);
    }
  }, [sessionId, filter]);

  useEffect(() => {
    loadAssets();
  }, [loadAssets]);

  if (!sessionId) {
    return (
      <div className="asset-panel asset-panel--empty">
        <div className="asset-panel__placeholder">
          No session connected
        </div>
      </div>
    );
  }

  return (
    <div className="asset-panel">
      <div className="asset-panel__header">
        <h3>Assets</h3>
        <div className="asset-panel__filters">
          {['', 'image', 'video', 'music', 'sfx'].map((type) => (
            <button
              key={type}
              className={`asset-filter-btn ${filter === type ? 'asset-filter-btn--active' : ''}`}
              onClick={() => setFilter(type)}
            >
              {type || 'all'}
            </button>
          ))}
        </div>
      </div>

      {loading && <div className="asset-panel__loading">Loading...</div>}
      {error && <div className="asset-panel__error">{error}</div>}

      <div className="asset-panel__grid">
        {assets.length === 0 && !loading && (
          <div className="asset-panel__empty">No assets found</div>
        )}
        {assets.map((asset, i) => (
          <AssetCard key={asset.content_hash || asset.id || i} asset={asset} />
        ))}
      </div>
    </div>
  );
};

const AssetCard: React.FC<{ asset: Asset }> = ({ asset }) => {
  const type = asset.asset_type || 'unknown';
  const name = (asset.metadata?.name as string) || asset.id || asset.content_hash?.slice(0, 8) || 'asset';
  const source = (asset.metadata?.source as string) || '';

  return (
    <div
      className={`asset-card asset-card--${type}`}
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData('application/json', JSON.stringify(asset));
        e.dataTransfer.effectAllowed = 'copy';
      }}
      title={`${name}\n${source}`}
    >
      <div className="asset-card__icon">
        {type === 'image' ? '🖼' : type === 'video' ? '🎬' : type === 'music' ? '🎵' : '📁'}
      </div>
      <div className="asset-card__info">
        <span className="asset-card__name">{name.slice(0, 20)}</span>
        <span className="asset-card__type">{type}</span>
      </div>
    </div>
  );
};
