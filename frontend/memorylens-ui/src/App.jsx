import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import SearchBar from './SearchBar';
import UploadPanel from './UploadPanel';
import IndexPanel from './IndexPanel';
import ResultsGrid from './ResultsGrid';
import FaceGroups from './FaceGroups';
import './App.css';

const API_BASE = 'http://localhost:8000'; // Hardcoded for dev connectivity, relative paths fail when npm start is on p3000

// Cursor Trail
function CursorTrail() {
  const dotsRef = useRef([]);

  useEffect(() => {
    let mouse = { x: 0, y: 0 };
    let trail = Array(16).fill({ x: 0, y: 0 });

    const onMove = (e) => { mouse = { x: e.clientX, y: e.clientY }; };

    const animate = () => {
      trail = [mouse, ...trail.slice(0, 15)];
      trail.forEach((pos, i) => {
        const dot = dotsRef.current[i];
        if (dot) {
          dot.style.left = `${pos.x}px`;
          dot.style.top = `${pos.y}px`;
          dot.style.opacity = `${(1 - i / 16) * 0.6}`;
          dot.style.transform = `translate(-50%, -50%) scale(${1 - i / 20})`;
        }
      });
      requestAnimationFrame(animate);
    };

    window.addEventListener('mousemove', onMove);
    animate();
    return () => window.removeEventListener('mousemove', onMove);
  }, []);

  return (
    <div className="cursor-trail">
      {Array(16).fill(0).map((_, i) => (
        <div key={i} ref={el => dotsRef.current[i] = el} className="trail-dot" />
      ))}
    </div>
  );
}

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

// Typewriter
function Typewriter({ texts }) {
  const [display, setDisplay] = useState('');
  const [idx, setIdx] = useState(0);
  const [charIdx, setCharIdx] = useState(0);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const current = texts[idx];
    let timeout;
    if (!deleting && charIdx < current.length) {
      timeout = setTimeout(() => { setDisplay(current.slice(0, charIdx + 1)); setCharIdx(c => c + 1); }, 55);
    } else if (!deleting && charIdx === current.length) {
      timeout = setTimeout(() => setDeleting(true), 2000);
    } else if (deleting && charIdx > 0) {
      timeout = setTimeout(() => { setDisplay(current.slice(0, charIdx - 1)); setCharIdx(c => c - 1); }, 30);
    } else if (deleting && charIdx === 0) {
      setDeleting(false);
      setIdx(i => (i + 1) % texts.length);
    }
    return () => clearTimeout(timeout);
  }, [charIdx, deleting, idx, texts]);

  return (
    <span className="typewriter">
      {display}<span className="cursor-blink">|</span>
    </span>
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
  const [indexProgress, setIndexProgress] = useState(null);
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
        params: { q: query },
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
      addToast(`✅ Found ${res.data.results?.length || 0} matching faces`, 'success');
    } catch (e) {
      addToast('⚠️ Backend not connected. Is the server running?', 'warning');
    }
    setIsLoading(false);
  };



  return (
    <>
      <CursorTrail />
      <Particles />

      {/* Dark/Light Toggle */}
      <button id="theme-toggle" className="theme-btn" onClick={() => setDarkMode(!darkMode)}>
        {darkMode ? '☀️' : '🌙'}
      </button>

      <div className="app">
        <div className="header">
          <h1>🧠 MemoryLens</h1>
          <p>
            <Typewriter texts={[
              'Search your files by face or memory.',
              'Powered by AI. Built for humans.',
              'Find anything. Instantly.',
              'Your memory. Supercharged.',
            ]} />
          </p>
        </div>

        {/* Indexing Progress Bar */}
        <IndexProgress progress={indexProgress} />

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



        {!isLoading && results.length > 0 && mode === 'doc' && (
          <ResultsGrid results={results} mode={mode} />
        )}

        {/* Face Search results are now groups — show them using FaceGroups */}
        {!isLoading && results.length > 0 && mode === 'face' && (
          <FaceGroups searchResults={results} />
        )}

        {!isLoading && results.length === 0 && (
          <div className="empty">
            {mode === 'doc'
              ? '💬 Type what you remember to find your document'
              : '📸 Upload a photo to find matching faces'}
          </div>
        )}

        {/* Default Face Groups — shown on face tab when NOT searching */}
        {mode === 'face' && !isLoading && results.length === 0 && <FaceGroups />}
      </div>



      <Toast toasts={toasts} />
    </>
  );
}

export default App;