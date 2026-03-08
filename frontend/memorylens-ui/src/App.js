import { useState, useEffect, useRef } from 'react';
import SearchBar from './SearchBar';
import UploadPanel from './UploadPanel';
import ResultsGrid from './ResultsGrid';
import IndexPanel from './IndexPanel';
import './App.css';

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

function App() {
  const [mode, setMode] = useState('doc');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [darkMode, setDarkMode] = useState(true);
  const [query, setQuery] = useState('');  // ← NEW
  const toastId = useRef(0);

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

  const handleDocSearch = async (q) => {
    setQuery(q);  // ← NEW
    setLoading(true);
    setResults([]);
    try {
      const res = await fetch(`http://localhost:8000/api/search/docs?q=${encodeURIComponent(q)}`);
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
    setQuery(file.name);  // ← NEW
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
      <CursorTrail />
      <Particles />

      <button className="theme-btn" onClick={() => setDarkMode(!darkMode)}>
        {darkMode ? '☀️' : '🌙'}
      </button>

      <div className="app">
        <div className="header">
          <h1>MemoryLens</h1>
          <p>
            <Typewriter texts={[
              'Search your files by face or memory.',
              'Powered by AI. Built for humans.',
              'Find anything. Instantly.',
              'Your memory. Supercharged.',
            ]} />
          </p>
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
            : (
              <>
                <IndexPanel onIndexComplete={() => addToast('✅ Photos indexed! Face search is ready.', 'success')} />
                <UploadPanel onSearch={handleFaceSearch} />
              </>
            )
          }
        </div>

        {loading && (
          <div className="loading">
            <div className="ai-scanner">
              <div className="scanner-ring" />
              <div className="scanner-ring" style={{ animationDelay: '0.3s' }} />
              <div className="scanner-ring" style={{ animationDelay: '0.6s' }} />
              <div className="scanner-core">🧠</div>
            </div>
            <p className="scanning-text">AI is scanning...</p>
          </div>
        )}

        {!loading && results.length > 0 && (
          <ResultsGrid results={results} mode={mode} query={query} />  // ← query prop added
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