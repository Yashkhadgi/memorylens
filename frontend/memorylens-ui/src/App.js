import { useState, useEffect, useRef } from 'react';
import SearchBar from './SearchBar';
import UploadPanel from './UploadPanel';
import ResultsGrid from './ResultsGrid';
import './App.css';

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
  const [loading, setLoading] = useState(false);
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

  const handleDocSearch = async (query) => {
    setLoading(true);
    setResults([]);
    try {
      const res = await fetch(`http://localhost:8000/api/search/docs?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      setResults(data.results || []);
      addToast(`✅ Found ${data.results.length} results`, 'success');
    } catch (e) {
      addToast('⚠️ Backend not connected — showing dummy results', 'warning');
      setResults([
        { filename: 'project_budget.pdf', snippet: 'Project Alpha Budget 9195...', score: 95.2 },
        { filename: 'meeting_notes.docx', snippet: 'Discussion about Q3 targets...', score: 87.1 },
        { filename: 'report.txt', snippet: 'Annual report summary...', score: 76.5 },
      ]);
    }
    setLoading(false);
  };

  const handleFaceSearch = async (file) => {
    setLoading(true);
    setResults([]);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('http://localhost:8000/api/search/faces', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setResults(data.results || []);
      addToast(`✅ Found ${data.results.length} matching faces`, 'success');
    } catch (e) {
      addToast('⚠️ Backend not connected — showing dummy results', 'warning');
      setResults([
        { filename: 'photo_001.jpg', score: 98.5 },
        { filename: 'photo_045.jpg', score: 94.2 },
        { filename: 'photo_112.jpg', score: 88.7 },
      ]);
    }
    setLoading(false);
  };

  return (
    <>
      <Particles />

      {/* Dark/Light Toggle */}
      <button className="theme-btn" onClick={() => setDarkMode(!darkMode)}>
        {darkMode ? '☀️' : '🌙'}
      </button>

      <div className="app">
        <div className="header">
          <h1>🧠 MemoryLens</h1>
          <p>Search your files by face or memory</p>
        </div>

        <div className="toggle">
          <button
            className={mode === 'doc' ? 'active' : ''}
            onClick={() => { setMode('doc'); setResults([]); }}
          >
            📄 Document Search
          </button>
          <button
            className={mode === 'face' ? 'active' : ''}
            onClick={() => { setMode('face'); setResults([]); }}
          >
            📸 Face Search
          </button>
        </div>

        <div className="search-panel">
          {mode === 'doc'
            ? <SearchBar onSearch={handleDocSearch} />
            : <UploadPanel onSearch={handleFaceSearch} />
          }
        </div>

        {loading && (
          <div className="loading">
            <div className="spinner" />
            Searching...
          </div>
        )}

        {!loading && results.length > 0 && (
          <ResultsGrid results={results} mode={mode} />
        )}

        {!loading && results.length === 0 && (
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