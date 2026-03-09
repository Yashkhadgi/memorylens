import { useState } from 'react';

const API_BASE = 'http://localhost:8000';

function ResultsGrid({ results, mode, query }) {
  const [selectedImage, setSelectedImage] = useState(null);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [copyFeedback, setCopyFeedback] = useState(false);

  // Open file via backend
  const handleOpen = async (filepath) => {
    if (!filepath) return;
    try {
      await fetch(`${API_BASE}/api/open-file?path=${encodeURIComponent(filepath)}`);
    } catch (e) {
      console.log('Backend not connected');
    }
  };

  // Copy path to clipboard
  const handleCopyPath = async (filepath) => {
    if (!filepath) return;
    try {
      await navigator.clipboard.writeText(filepath);
      setCopyFeedback(true);
      setTimeout(() => setCopyFeedback(false), 1500);
    } catch (e) {
      console.log('Failed to copy');
    }
  };

  // Get filename from path
  const getFilename = (filepath) => {
    if (!filepath) return 'Unknown';
    return filepath.split(/[/\\]/).pop();
  };

  // Bold highlight for doc search
  const highlight = (text, q) => {
    if (!q || !text) return text;
    const parts = text.split(new RegExp(`(${q})`, 'gi'));
    return parts.map((p, i) =>
      p.toLowerCase() === q.toLowerCase()
        ? <strong key={i} style={{ color: '#ffffff' }}>{p}</strong>
        : p
    );
  };

  // ── Face Results: 4×4 Image Grid ──────────────────────
  if (mode === 'face') {
    return (
      <div className="results-section">
        <h3>Found {results.length} matching face{results.length !== 1 ? 's' : ''}</h3>

        <div className="face-grid">
          {results.map((result, index) => (
            <div
              key={index}
              className="face-card"
              onClick={() => setSelectedImage(result)}
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              <div className="face-img-wrapper">
                <img
                  src={`${API_BASE}/api/image?path=${encodeURIComponent(result.file_path)}`}
                  alt={getFilename(result.file_path)}
                  className="face-img"
                  loading="lazy"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.parentElement.classList.add('img-error');
                  }}
                />
                <div className="face-similarity">{result.similarity}%</div>
              </div>
              <p className="face-name" title={getFilename(result.file_path)}>
                {getFilename(result.file_path)}
              </p>
            </div>
          ))}
        </div>

        {/* ── Image Popup ── */}
        {selectedImage && (
          <div className="image-popup-overlay" onClick={() => setSelectedImage(null)}>
            <div className="image-popup" onClick={(e) => e.stopPropagation()}>
              <button className="popup-close" onClick={() => setSelectedImage(null)}>✕</button>
              <img
                src={`${API_BASE}/api/image?path=${encodeURIComponent(selectedImage.file_path)}`}
                alt={getFilename(selectedImage.file_path)}
                className="popup-img"
              />
              <div className="popup-info">
                <p className="popup-filename">{getFilename(selectedImage.file_path)}</p>
                <p className="popup-similarity">{selectedImage.similarity}% match</p>
              </div>
              <div className="popup-actions">
                <button
                  className="popup-btn open-btn"
                  onClick={() => handleOpen(selectedImage.file_path)}
                >
                  📂 Open File
                </button>
                <button
                  className="popup-btn copy-btn"
                  onClick={() => handleCopyPath(selectedImage.file_path)}
                >
                  {copyFeedback ? '✅ Copied!' : '📋 Copy Path'}
                </button>
              </div>
              <p className="popup-path" title={selectedImage.file_path}>
                {selectedImage.file_path}
              </p>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ── Document Results ──────────────────────────────────

  return (
    <div className="results-section">
      <h3>Found {results.length} result{results.length !== 1 ? 's' : ''}</h3>
      <div className="results-grid">
        {results.map((result, index) => (
          <div
            key={index}
            className="result-card clickable"
            onClick={() => setSelectedDoc(result)}
          >
            <div className="result-header">
              <span className="result-icon">📄</span>
              <span className="result-filename">{result.filename}</span>
              <span className="open-hint">↗</span>
            </div>

            {result.snippet && (
              <p className="result-snippet">"{highlight(result.snippet, query)}"</p>
            )}

            <div className="result-score">
              <div
                className="score-bar"
                style={{ width: `${Math.min(result.score, 100)}%` }}
              />
              <span className="score-text">{result.score}% match</span>
            </div>
          </div>
        ))}
      </div>

      {/* ── Doc Popup ── */}
      {selectedDoc && (
        <div className="image-popup-overlay" onClick={() => setSelectedDoc(null)}>
          <div className="image-popup" onClick={(e) => e.stopPropagation()}>
            <button className="popup-close" onClick={() => setSelectedDoc(null)}>✕</button>

            <div className="doc-popup-icon">📄</div>

            <div className="popup-info">
              <p className="popup-filename">{selectedDoc.filename}</p>
              <p className="popup-similarity">{selectedDoc.score}% match</p>
            </div>

            {selectedDoc.snippet && (
              <p className="doc-popup-snippet">"{selectedDoc.snippet}"</p>
            )}

            <div className="popup-actions">
              <button
                className="popup-btn open-btn"
                onClick={() => handleOpen(selectedDoc.path)}
              >
                📂 Open File
              </button>
              <button
                className="popup-btn copy-btn"
                onClick={() => handleCopyPath(selectedDoc.path)}
              >
                {copyFeedback ? '✅ Copied!' : '📋 Copy Path'}
              </button>
            </div>

            <p className="popup-path" title={selectedDoc.path}>
              {selectedDoc.path}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default ResultsGrid;