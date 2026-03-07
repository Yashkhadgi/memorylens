import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import SearchBar from './SearchBar';
import UploadPanel from './UploadPanel';
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

function App() {
  const [mode, setMode] = useState('doc');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [darkMode, setDarkMode] = useState(true);
  const toastId = useRef(0);

  // Apply dark/light mode to body
  useEffect(() => {
    document.body.classList.toggle('light', !darkMode);
  }, [darkMode]);

  const addToast = (message, type = 'warning') => {
    const id = toastId.current++;
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3500);
  };

  // ── Document Search ─────────────────────────────────
  const handleDocSearch = async (query) => {
    setIsLoading(true);
    setResults([]);
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
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await axios.post(`${API_BASE}/api/search/faces`, formData);
      setResults(res.data.results || []);
      addToast(`✅ Found ${res.data.results.length} matching faces`, 'success');
    } catch (e) {
      addToast('⚠️ Backend not connected. Is the server running?', 'warning');
    }
    setIsLoading(false);
  };

  // ── Index Folder ────────────────────────────────────
  const handleIndexFolder = async () => {
    const folderPath = prompt('Enter the full path to the folder to index:');
    if (!folderPath || !folderPath.trim()) return;

    setIsIndexing(true);
    addToast('📂 Indexing started...', 'info');
    try {
      const res = await axios.post(`${API_BASE}/api/index`, {
        folder_path: folderPath.trim(),
      });
      addToast(
        `✅ Indexed ${res.data.photos_indexed} photos & ${res.data.docs_indexed} docs`,
        'success'
      );
    } catch (e) {
      addToast('⚠️ Indexing failed. Check the folder path.', 'warning');
    }
    setIsIndexing(false);
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

        <div className="toggle">
          <button
            id="doc-search-tab"
            className={mode === 'doc' ? 'active' : ''}
            onClick={() => { setMode('doc'); setResults([]); }}
          >
            📄 Document Search
          </button>
          <button
            id="face-search-tab"
            className={mode === 'face' ? 'active' : ''}
            onClick={() => { setMode('face'); setResults([]); }}
          >
            📸 Face Search
          </button>
        </div>

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

      {/* Index Folder FAB */}
      <button
        id="index-folder-btn"
        className="fab"
        onClick={handleIndexFolder}
        disabled={isIndexing}
      >
        {isIndexing ? '⏳' : '📁'} {isIndexing ? 'Indexing...' : 'Index Folder'}
      </button>

      <Toast toasts={toasts} />
    </>
  );
}

export default App;