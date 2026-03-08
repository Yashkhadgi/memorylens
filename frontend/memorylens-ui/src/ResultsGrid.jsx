function ResultsGrid({ results, mode, query }) {

  // F1 — unchanged
  const handleOpen = async (filepath) => {
    if (!filepath) return;
    try {
      await fetch(`http://localhost:8000/api/open-file?path=${encodeURIComponent(filepath)}`);
    } catch (e) {
      console.log('Backend not connected');
    }
  };

  // F3 — Bold highlight
  const highlight = (text, q) => {
    if (!q || !text) return text;
    const parts = text.split(new RegExp(`(${q})`, 'gi'));
    return parts.map((p, i) =>
      p.toLowerCase() === q.toLowerCase()
        ? <strong key={i} style={{ color: '#ffffff' }}>{p}</strong>
        : p
    );
  };

  // F2/F5 — Spotlight links
  const docLinks = [
    { icon: '🔍', label: 'Google',    url: `https://google.com/search?q=${encodeURIComponent(query || '')}` },
    { icon: '📖', label: 'Wikipedia', url: `https://en.wikipedia.org/wiki/Special:Search?search=${encodeURIComponent(query || '')}` },
    { icon: '🤖', label: 'ChatGPT',   url: `https://chatgpt.com/?q=${encodeURIComponent(query || '')}` },
  ];
  const faceLinks = [
    { icon: '🔍', label: 'Google Images', url: `https://images.google.com/search?tbm=isch&q=${encodeURIComponent(query || '')}` },
    { icon: '🤖', label: 'ChatGPT',       url: `https://chatgpt.com/?q=${encodeURIComponent(query || '')}` },
    { icon: '📸', label: 'Pinterest',     url: `https://pinterest.com/search/pins/?q=${encodeURIComponent(query || '')}` },
  ];
  const links = mode === 'face' ? faceLinks : docLinks;

  return (
    <div className="results-section">

      {/* F2/F5 — Spotlight Panel (NEW) */}
      <div className="spotlight-panel">
        {links.map((l, i) => (
          <a key={i} href={l.url} target="_blank" rel="noreferrer" className="spotlight-link">
            <span className="spotlight-icon">{l.icon}</span>
            <span>{l.label}</span>
          </a>
        ))}
      </div>

      {/* unchanged */}
      <h3>Found {results.length} result{results.length !== 1 ? 's' : ''}</h3>
      <div className="results-grid">
        {results.map((result, index) => (
          <div
            key={index}
            className="result-card clickable"
            onClick={() => handleOpen(result.filepath || result.filename)}
          >
            <div className="result-header">
              <span className="result-icon">
                {mode === 'face' ? '📸' : '📄'}
              </span>
              <span className="result-filename">{result.filename}</span>
              <span className="open-hint">↗</span>
            </div>

            {/* F3 — highlight added, rest unchanged */}
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
    </div>
  );
}

export default ResultsGrid;