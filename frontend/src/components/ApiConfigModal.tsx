import { useState, useEffect } from 'react';
import { fetchConfig, saveConfig, type ApiConfig } from '../api/backend';

interface Props {
  open: boolean;
  onClose: () => void;
  onConfirm?: (config: ApiConfig) => void;
}

export function ApiConfigModal({ open, onClose, onConfirm }: Props) {
  const [cfg, setCfg] = useState<ApiConfig>({ api_key: '', api_base: '', api_model: '' });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    setError(null);
    setSaved(false);
    fetchConfig()
      .then(setCfg)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [open]);

  if (!open) return null;

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const result = await saveConfig(cfg);
      if (result.success) {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
      } else {
        setError(result.error || 'Save failed');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handleConfirm = async () => {
    await handleSave();
    onConfirm?.(cfg);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>API 配置</h3>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
          {loading ? (
            <div className="config-loading">加载配置中...</div>
          ) : (
            <div className="config-form">
              <label>
                <span>API Base URL</span>
                <input
                  type="text"
                  value={cfg.api_base}
                  onChange={(e) => setCfg({ ...cfg, api_base: e.target.value })}
                  placeholder="https://api.minimax.chat/v1"
                />
              </label>
              <label>
                <span>API Key</span>
                <input
                  type="password"
                  value={cfg.api_key}
                  onChange={(e) => setCfg({ ...cfg, api_key: e.target.value })}
                  placeholder="sk-..."
                />
              </label>
              <label>
                <span>Model</span>
                <input
                  type="text"
                  value={cfg.api_model}
                  onChange={(e) => setCfg({ ...cfg, api_model: e.target.value })}
                  placeholder="minimax-m2.7-latest"
                />
              </label>
              {error && <div className="config-error">{error}</div>}
              {saved && <div className="config-saved">配置已保存</div>}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>取消</button>
          <button className="btn-secondary" onClick={handleSave} disabled={saving}>
            {saving ? '保存中...' : '仅保存'}
          </button>
          <button className="btn-primary" onClick={handleConfirm} disabled={saving || loading}>
            保存并继续
          </button>
        </div>
      </div>

      <style>{`
        .modal-overlay {
          position: fixed; inset: 0; background: rgba(0,0,0,0.5);
          display: flex; align-items: center; justify-content: center; z-index: 9999;
        }
        .modal-content {
          background: #1a1a2e; border-radius: 12px; width: 480px; max-width: 90vw;
          box-shadow: 0 8px 32px rgba(0,0,0,0.4); color: #e0e0e0;
        }
        .modal-header {
          display: flex; justify-content: space-between; align-items: center;
          padding: 16px 20px; border-bottom: 1px solid #2a2a4a;
        }
        .modal-header h3 { margin: 0; font-size: 16px; }
        .modal-close {
          background: none; border: none; color: #888; font-size: 22px; cursor: pointer;
        }
        .modal-body { padding: 20px; }
        .config-form label {
          display: flex; flex-direction: column; gap: 4px; margin-bottom: 14px;
        }
        .config-form label span { font-size: 12px; color: #aaa; }
        .config-form input {
          background: #0d0d1a; border: 1px solid #3a3a5a; border-radius: 6px;
          padding: 8px 12px; color: #e0e0e0; font-size: 13px; outline: none;
        }
        .config-form input:focus { border-color: #6c5ce7; }
        .config-error { color: #ff6b6b; font-size: 12px; margin-top: 8px; }
        .config-saved { color: #51cf66; font-size: 12px; margin-top: 8px; }
        .config-loading { text-align: center; padding: 20px; color: #888; }
        .modal-footer {
          display: flex; gap: 8px; justify-content: flex-end;
          padding: 12px 20px; border-top: 1px solid #2a2a4a;
        }
        .btn-primary, .btn-secondary {
          padding: 8px 16px; border-radius: 6px; border: none;
          font-size: 13px; cursor: pointer;
        }
        .btn-primary { background: #6c5ce7; color: white; }
        .btn-primary:hover { background: #5b4bd5; }
        .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-secondary { background: #2a2a4a; color: #ccc; }
        .btn-secondary:hover { background: #3a3a5a; }
        .btn-secondary:disabled { opacity: 0.5; cursor: not-allowed; }
      `}</style>
    </div>
  );
}
