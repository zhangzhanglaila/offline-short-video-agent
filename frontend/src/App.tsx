import { useEffect } from 'react';
import { Timeline } from './components/Timeline';
import { useTimelineStore } from './store/timelineStore';
import { useKeyboard } from './hooks/useKeyboard';
import './App.css';

/** Demo data: 3 scenes with video, subtitle (word timings), and audio tracks. */
function loadDemoData() {
  const { setTracks } = useTimelineStore.getState();

  const tracks = [
    // Video tracks
    { track_id: 'v_hook', track_type: 'video' as const, layer: 0, start_frame: 0, end_frame: 90, scene_id: 'hook', content: { scene_type: 'hook', text: 'Redis为什么这么快？' } },
    { track_id: 'v_graph', track_type: 'video' as const, layer: 0, start_frame: 82, end_frame: 210, scene_id: 'graph', content: { scene_type: 'graph', text: '单线程+内存模型' } },
    { track_id: 'v_cards', track_type: 'video' as const, layer: 0, start_frame: 202, end_frame: 330, scene_id: 'cards', content: { scene_type: 'cards', text: '关键总结' } },

    // Subtitle tracks with word timings
    { track_id: 's_hook', track_type: 'subtitle' as const, layer: 1, start_frame: 0, end_frame: 90, scene_id: 'hook', content: { text: 'Redis为什么这么快？', word_timings: [
      { word: 'Redis', start: 0.0, end: 0.4, start_frame: 0, end_frame: 12 },
      { word: '为什么', start: 0.4, end: 0.9, start_frame: 12, end_frame: 27 },
      { word: '这么快', start: 0.9, end: 1.5, start_frame: 27, end_frame: 45 },
      { word: '？', start: 1.5, end: 2.0, start_frame: 45, end_frame: 60 },
    ] } },
    { track_id: 's_graph', track_type: 'subtitle' as const, layer: 1, start_frame: 82, end_frame: 210, scene_id: 'graph', content: { text: '单线程加内存模型是关键', word_timings: [
      { word: '单线程', start: 0.0, end: 0.6, start_frame: 82, end_frame: 100 },
      { word: '加', start: 0.6, end: 0.8, start_frame: 100, end_frame: 106 },
      { word: '内存模型', start: 0.8, end: 1.5, start_frame: 106, end_frame: 127 },
      { word: '是关键', start: 1.5, end: 2.2, start_frame: 127, end_frame: 148 },
    ] } },
    { track_id: 's_cards', track_type: 'subtitle' as const, layer: 1, start_frame: 202, end_frame: 330, scene_id: 'cards', content: { text: '关注学习更多技术', word_timings: [
      { word: '关注', start: 0.0, end: 0.4, start_frame: 202, end_frame: 214 },
      { word: '学习', start: 0.4, end: 0.8, start_frame: 214, end_frame: 226 },
      { word: '更多', start: 0.8, end: 1.2, start_frame: 226, end_frame: 238 },
      { word: '技术', start: 1.2, end: 1.8, start_frame: 238, end_frame: 256 },
    ] } },

    // Audio tracks
    { track_id: 'a_hook', track_type: 'audio' as const, layer: 2, start_frame: 0, end_frame: 90, scene_id: 'hook', content: { audio_path: 'tts_hook.mp3' } },
    { track_id: 'a_graph', track_type: 'audio' as const, layer: 2, start_frame: 82, end_frame: 210, scene_id: 'graph', content: { audio_path: 'tts_graph.mp3' } },
    { track_id: 'a_cards', track_type: 'audio' as const, layer: 2, start_frame: 202, end_frame: 330, scene_id: 'cards', content: { audio_path: 'tts_cards.mp3' } },
  ];

  setTracks(tracks, 330);
}

function App() {
  useKeyboard();

  useEffect(() => {
    loadDemoData();
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Offline Short Video Agent</h1>
        <span className="app-subtitle">Timeline Editor</span>
      </header>
      <main className="app-main">
        <Timeline />
      </main>
    </div>
  );
}

export default App;
