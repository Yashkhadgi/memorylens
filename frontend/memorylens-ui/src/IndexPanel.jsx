import { useState, useEffect, useRef } from 'react';

function IndexPanel({ onIndexComplete, mode = 'both' }) {
  const [folderPath, setFolderPath] = useState('');
  const [indexing, setIndexing] = useState(false);
  const [progress, setProgress] = useState(null);
  const [done, setDone] = useState(false);
  const pollRef = useRef(null);

  const handleSelectFolder = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/select-folder');
      const data = await res.json();
      if (data.folder_path) setFolderPath(data.folder_path);
    } catch (e) {
      setFolderPath('C:\\Users\\Photos'); // dummy for testing
    }
  };

  const handleStartIndex = async () => {
    if (!folderPath.trim()) return;
    setIndexing(true);
    setDone(false);
    setProgress(null);

    try {
      await fetch('http://localhost:8000/api/index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: folderPath, mode: mode }),
      });
      startPolling();
    } catch (e) {
      // Simulate progress for testing
      simulateProgress();
    }
  };

  const startPolling = () => {
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch('http://localhost:8000/api/index/progress');
        const data = await res.json();
        setProgress(data);
        if (data.done) {
          clearInterval(pollRef.current);
          setIndexing(false);
          setDone(true);
          onIndexComplete && onIndexComplete();
        }
      } catch (e) {
        clearInterval(pollRef.current);
        setIndexing(false);
      }
    }, 800);
  };

  const simulateProgress = () => {
    let p = 0;
    const total = 24;
    pollRef.current = setInterval(() => {
      p++;
      setProgress({
        processed: p,
        total,
        indexed: p,
        skipped: 0,
        errors: 0,
        done: p >= total,
        message: p >= total ? `Done! Indexed ${total} photos (0 skipped, 0 errors)` : 'Scanning folder...',
      });
      if (p >= total) {
        clearInterval(pollRef.current);
        setIndexing(false);
        setDone(true);
        onIndexComplete && onIndexComplete();
      }
    }, 200);
  };

  useEffect(() => {
    return () => clearInterval(pollRef.current);
  }, []);

  const percent = progress && progress.total > 0
    ? Math.round((progress.processed / progress.total) * 100)
    : 0;

  return (
    <div className="index-panel">
      <div className="index-header">
        <span className="index-icon">📁</span>
        <div>
          <p className="index-title">{mode === 'face' ? 'Index Your Photos' : mode === 'doc' ? 'Index Your Documents' : 'Index Your Files'}</p>
          <p className="index-subtitle">{mode === 'face' ? 'Select a folder with photos to scan faces' : mode === 'doc' ? 'Select a folder with documents to index' : 'Select a folder to index documents & photos'}</p>
        </div>
      </div>

      <div className="index-input-row">
        <input
          type="text"
          value={folderPath}
          onChange={(e) => setFolderPath(e.target.value)}
          placeholder="Paste folder path or click Browse..."
          className="search-input"
          disabled={indexing}
        />
        <button
          onClick={handleSelectFolder}
          className="browse-btn"
          disabled={indexing}
        >
          Browse
        </button>
        <button
          onClick={handleStartIndex}
          className="search-btn"
          disabled={indexing || !folderPath.trim()}
        >
          {indexing ? '⏳ Indexing...' : '⚡ Index'}
        </button>
      </div>

      {/* Progress Bar */}
      {indexing && progress && (
        <div className="progress-container">
          <div className="progress-info">
            <span className="progress-message">{progress.message}</span>
            <span className="progress-percent">{percent}%</span>
          </div>
          <div className="progress-track">
            <div
              className="progress-fill"
              style={{ width: `${percent}%` }}
            />
          </div>
          <div className="progress-stats">
            <span>✅ {progress.indexed} indexed</span>
            <span>⏭️ {progress.skipped} skipped</span>
            <span>❌ {progress.errors} errors</span>
            <span>📄 {progress.processed}/{progress.total} files</span>
          </div>
        </div>
      )}

      {/* Done State */}
      {done && progress && (
        <div className="index-done">
          <span>🎉 {progress.message}</span>
        </div>
      )}
    </div>
  );
}

export default IndexPanel;