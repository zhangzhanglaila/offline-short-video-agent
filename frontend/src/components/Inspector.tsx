import React, { useState, useCallback } from 'react';
import { useTimelineStore } from '../store/timelineStore';

/** Scene property inspector with bidirectional editing. */
export const Inspector: React.FC = () => {
  const { selectedScene, updateSceneContent, resizeScene, undo, redo, undoStack, redoStack } = useTimelineStore();
  const scene = selectedScene();

  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const startEdit = useCallback((field: string, currentValue: string) => {
    setEditingField(field);
    setEditValue(currentValue);
  }, []);

  const commitEdit = useCallback(() => {
    if (editingField && scene) {
      updateSceneContent(scene.scene_id, editingField, editValue);
      setEditingField(null);
    }
  }, [editingField, editValue, scene, updateSceneContent]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      commitEdit();
    } else if (e.key === 'Escape') {
      setEditingField(null);
    }
  }, [commitEdit]);

  if (!scene) {
    return (
      <div className="inspector inspector--empty">
        <div className="inspector__placeholder">
          Select a scene to edit its properties
        </div>
        <div className="inspector__shortcuts">
          <h4>Keyboard Shortcuts</h4>
          <div className="shortcut-row"><kbd>Space</kbd> Play / Pause</div>
          <div className="shortcut-row"><kbd>&larr;</kbd><kbd>&rarr;</kbd> &plusmn;1 frame</div>
          <div className="shortcut-row"><kbd>Shift</kbd>+<kbd>&larr;</kbd><kbd>&rarr;</kbd> &plusmn;10 frames</div>
          <div className="shortcut-row"><kbd>Home</kbd><kbd>End</kbd> Jump start / end</div>
          <div className="shortcut-row"><kbd>Z</kbd><kbd>X</kbd> Zoom in / out</div>
          <div className="shortcut-row"><kbd>Ctrl+Z</kbd><kbd>Ctrl+Y</kbd> Undo / Redo</div>
          <div className="shortcut-row"><kbd>L</kbd> Toggle loop</div>
          <div className="shortcut-row"><kbd>Esc</kbd> Deselect</div>
        </div>
      </div>
    );
  }

  const durationFrames = scene.end_frame - scene.start_frame;
  const durationSec = (durationFrames / 30).toFixed(1);

  return (
    <div className="inspector">
      <div className="inspector__header">
        <h3>Scene: {scene.scene_id}</h3>
        <div className="inspector__actions">
          <button onClick={undo} disabled={undoStack.length === 0} title="Undo (Ctrl+Z)">Undo</button>
          <button onClick={redo} disabled={redoStack.length === 0} title="Redo (Ctrl+Y)">Redo</button>
        </div>
      </div>

      <div className="inspector__grid">
        {/* Type */}
        <div className="inspector-row">
          <label>Type</label>
          {editingField === 'scene_type' ? (
            <select
              value={editValue}
              onChange={(e) => { setEditValue(e.target.value); }}
              onBlur={commitEdit}
              onKeyDown={handleKeyDown}
              autoFocus
            >
              {['hook', 'graph', 'cards', 'reveal', 'cta', 'problem', 'explanation'].map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          ) : (
            <span
              className="editable"
              onClick={() => startEdit('scene_type', scene.scene_type)}
            >
              {scene.scene_type}
            </span>
          )}
        </div>

        {/* Text */}
        <div className="inspector-row inspector-row--text">
          <label>Text</label>
          {editingField === 'text' ? (
            <textarea
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onBlur={commitEdit}
              onKeyDown={handleKeyDown}
              autoFocus
              rows={3}
            />
          ) : (
            <span
              className="editable"
              onClick={() => startEdit('text', scene.text)}
            >
              {scene.text}
            </span>
          )}
        </div>

        {/* Frames */}
        <div className="inspector-row">
          <label>Frames</label>
          <span>{scene.start_frame} &rarr; {scene.end_frame} ({durationFrames}f)</span>
        </div>

        {/* Duration */}
        <div className="inspector-row">
          <label>Duration</label>
          <span>{durationSec}s</span>
        </div>

        {/* Layer */}
        <div className="inspector-row">
          <label>Layer</label>
          <span>{scene.layer}</span>
        </div>

        {/* Resize */}
        <div className="inspector-row">
          <label>Resize</label>
          <div className="inspector__resize">
            <input
              type="range"
              min={scene.start_frame + 10}
              max={scene.start_frame + 600}
              value={scene.end_frame}
              onChange={(e) => resizeScene(scene.scene_id, Number(e.target.value))}
            />
            <span className="resize-value">{durationFrames}f</span>
          </div>
        </div>
      </div>
    </div>
  );
};
