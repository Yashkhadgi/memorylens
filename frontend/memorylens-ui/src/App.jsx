import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import SearchBar from './SearchBar';
import UploadPanel from './UploadPanel';
import IndexPanel from './IndexPanel';
import ResultsGrid from './ResultsGrid';
import './App.css';

const API_BASE = 'http://localhost:8000';

// Particles
function Particles() {
  const particles = Array.from({ length: 18 }, (_, i) => ({
    id: i,
    size: Math.random() * 60 + 20,
    left: Math.random() * 100,
    duration: Math.random() * 15 + 8,
    delay: Math.random() * 10,
  }));

  return (
    <div className="particles">
      {particles.map(p => (
        <div
          key={p.id}
          className="particle"
          style={{
            width: p.size,
            height: p.size,
            left: `${p.left}%`,
            animationDuration: `${p.duration}s`,
            animationDelay: `${p.delay}s`,
          }}
        />
      ))}
    </div>
  );
}

// Toast
function Toast({ toasts }) {
  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast ${t.type}`}>
          {t.message}
        </div>
      ))}
    </div>
  );
}

// Progress Bar
function IndexProgress({ progress }) {
  if (!progress || (!progress.is_running && !progress.done)) return null;

  const percent = progress.total > 0
    ? Math.round((progress.processed / progress.total) * 100)
    : 0;

  return (
    <div className="index-progress">
      <div className="progress-header">
        <span className="progress-title">
          {progress.done ? '✅ Indexing Complete' : '📸 Indexing Photos...'}
        </span>
        <span className="progress-count">
          {progress.processed} / {progress.total} photos
        </span>
      </div>

      <div className="progress-bar-track">
        <div
          className={`progress-bar-fill ${progress.done ? 'done' : ''}`}
          style={{ width: `${percent}%` }}
        />
      </div>

      <div className="progress-details">
        <span className="progress-percent">{percent}%</span>
        {progress.done && (
          <span className="progress-stats">
            ✅ {progress.indexed} indexed · ⏭️ {progress.skipped} skipped · ❌ {progress.errors} errors
          </span>
        )}
      </div>

      {progress.message && (
        <p className="progress-message">{progress.message}</p>
      )}
    </div>
  );
}

function App() {
  const [mode, setMode] = useState('doc');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [indexProgress, setIndexProgress] = useState(null);
  const [searchStats, setSearchStats] = useState(null);
  const [toasts, setToasts] = useState([]);
  const [darkMode, setDarkMode] = useState(true);
  const toastId = useRef(0);
  const pollRef = useRef(null);

  // Apply dark/light mode to body
  useEffect(() => {
    document.body.classList.toggle('light', !darkMode);
  }, [darkMode]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const addToast = (message, type = 'warning') => {
    const id = toastId.current++;
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3500);
  };

  // ── Poll indexing progress ──────────────────────────
  const startPolling = () => {
    if (pollRef.current) clearInterval(pollRef.current);

    pollRef.current = setInterval(async () => {
      try {
        const res = await axios.get(`${API_BASE}/api/index/progress`);
        const data = res.data;
        setIndexProgress(data);

        // Stop polling when done
        if (data.done) {
          clearInterval(pollRef.current);
          pollRef.current = null;
          setIsIndexing(false);
          addToast(
            `✅ Indexed ${data.indexed} photos (${data.skipped} skipped, ${data.errors} errors)`,
            'success'
          );
        }
      } catch {
        // Backend might not be ready yet, keep polling
      }
    }, 500); // Poll every 500ms
  };

  // ── Document Search ─────────────────────────────────
  const handleDocSearch = async (query) => {
    setIsLoading(true);
    setResults([]);
    setSearchStats(null);
    try {
      const res = await axios.get(`${API_BASE}/api/search/docs`, {
        params: { query },
      });
      setResults(res.data.results || []);
      addToast(`✅ Found ${res.data.results.length} results`, 'success');
    } catch (e) {
      if (e.response?.status === 503) {
        addToast('⚠️ Index not built yet. Please index a folder first.', 'warning');
      } else {
        addToast('⚠️ Backend not connected. Is the server running?', 'warning');
      }
    }
    setIsLoading(false);
  };

  // ── Face Search ─────────────────────────────────────
  const handleFaceSearch = async (file) => {
    setIsLoading(true);
    setResults([]);
    setSearchStats(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await axios.post(`${API_BASE}/api/search/faces`, formData);
      setResults(res.data.results || []);
      setSearchStats(res.data.stats || null);
      addToast(`✅ Found ${res.data.results?.length || 0} matching faces`, 'success');
    } catch (e) {
      addToast('⚠️ Backend not connected. Is the server running?', 'warning');
    }
    setIsLoading(false);
  };

  // ── Index Folder ────────────────────────────────────
  const handleIndexFolder = async () => {
    addToast('🗂️ Please select a folder in the popup window...', 'info');

    try {
      // 1. Ask backend to open native folder picker
      const dialogRes = await axios.get(`${API_BASE}/api/select-folder`);
      const folderPath = dialogRes.data.folder_path;

      if (!folderPath) {
        addToast('Selection canceled.', 'info');
        return;
      }

      setIsIndexing(true);
      setIndexProgress({ is_running: true, processed: 0, total: 0, done: false, message: 'Starting...' });

      // 2. Start indexing with the selected path
      await axios.post(`${API_BASE}/api/index`, {
        folder_path: folderPath.trim(),
      });
      // Start polling for progress
      startPolling();
    } catch (e) {
      setIsIndexing(false);
      setIndexProgress(null);
      if (e.response?.status === 409) {
        addToast('⚠️ Indexing already in progress!', 'warning');
      } else {
        addToast('⚠️ Failed to start indexing.', 'warning');
      }
    }
  };

  return (
    <>
      <Particles />

      {/* Dark/Light Toggle */}
      <button id="theme-toggle" className="theme-btn" onClick={() => setDarkMode(!darkMode)}>
        {darkMode ? '☀️' : '🌙'}
      </button>

      <div className="app">
        <div className="header">
          <h1>🧠 MemoryLens</h1>
          <p>Search your files by face or memory</p>
        </div>

        {/* Indexing Progress Bar */}
        <IndexProgress progress={indexProgress} />

        <div className="toggle">
          <button
            id="doc-search-tab"
            className={mode === 'doc' ? 'active' : ''}
            onClick={() => { setMode('doc'); setResults([]); setSearchStats(null); }}
          >
            📄 Document Search
          </button>
          <button
            id="face-search-tab"
            className={mode === 'face' ? 'active' : ''}
            onClick={() => { setMode('face'); setResults([]); setSearchStats(null); }}
          >
            📸 Face Search
          </button>
        </div>

        {/* Index Panel — paste/browse folder to index */}
        <IndexPanel onIndexComplete={() => addToast('✅ Indexing complete!', 'success')} />

        <div className="search-panel">
          {mode === 'doc'
            ? <SearchBar onSearch={handleDocSearch} isLoading={isLoading} />
            : <UploadPanel onSearch={handleFaceSearch} isLoading={isLoading} />
          }
        </div>

        {isLoading && (
          <div className="loading">
            <div className="spinner" />
            Searching...
          </div>
        )}

        {!isLoading && searchStats && mode === 'face' && (
          <div className="search-stats-container">
            <div className="stat-card">
              <span className="stat-value">{searchStats.total_indexed}</span>
              <span className="stat-label">Total Indexed</span>
            </div>
            <div className="stat-card match">
              <span className="stat-value">{searchStats.found}</span>
              <span className="stat-label">Matches Found</span>
            </div>
            <div className="stat-card no-match">
              <span className="stat-value">{searchStats.not_match}</span>
              <span className="stat-label">Did Not Match</span>
            </div>
          </div>
        )}

        {!isLoading && results.length > 0 && (
          <ResultsGrid results={results} mode={mode} />
        )}

        {!isLoading && results.length === 0 && (
          <div className="empty">
            {mode === 'doc'
              ? '💬 Type what you remember to find your document'
              : '📸 Upload a photo to find matching faces'}
          </div>
        )}
      </div>



      <Toast toasts={toasts} />
    </>
  );
}

export default App;