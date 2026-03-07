import { useState } from 'react';

function ResultsGrid({ results, mode }) {
  const [copiedPath, setCopiedPath] = useState(null);

  const handleCopyPath = (filePath) => {
    navigator.clipboard.writeText(filePath).then(() => {
      setCopiedPath(filePath);
      setTimeout(() => setCopiedPath(null), 2000);
    });
  };

  const getSimilarityBadgeClass = (similarity) => {
    if (similarity >= 90) return 'badge-green';
    if (similarity >= 80) return 'badge-yellow';
    return 'badge-orange';
  };

  const getMatchSourceLabel = (source) => {
    switch (source) {
      case 'semantic+keyword': return '🎯 Semantic + Keyword';
      case 'semantic': return '🧠 Semantic';
      case 'keyword': return '🔤 Keyword';
      default: return source;
    }
  };

  const getFileIcon = (fileType) => {
    switch (fileType) {
      case 'pdf': return '📕';
      case 'docx': return '📘';
      case 'txt': return '📄';
      case 'png': case 'jpg': case 'jpeg': case 'tiff': return '🖼️';
      default: return '📄';
    }
  };

  if (results.length === 0) {
    return (
      <div className="empty">
        No results found. Try indexing a folder first.
      </div>
    );
  }

  return (
    <div className="results-section">
      <h3>Found {results.length} result{results.length !== 1 ? 's' : ''}</h3>
      <div className="results-grid">
        {results.map((result, index) => (
          <div
            key={index}
            className="result-card"
            onClick={() => result.file_path && handleCopyPath(result.file_path)}
            style={{ cursor: mode === 'doc' ? 'pointer' : 'default' }}
            title={mode === 'doc' ? 'Click to copy file path' : ''}
          >
            {/* Header */}
            <div className="result-header">
              <span className="result-icon">
                {mode === 'face' ? '📸' : getFileIcon(result.file_type)}
              </span>
              <span className="result-filename">
                {result.file_path
                  ? result.file_path.split(/[/\\]/).pop()
                  : 'Unknown'}
              </span>

              {/* Face mode: similarity badge */}
              {mode === 'face' && result.similarity != null && (
                <span className={`similarity-badge ${getSimilarityBadgeClass(result.similarity)}`}>
                  {result.similarity}%
                </span>
              )}

              {/* Doc mode: match source badge */}
              {mode === 'doc' && result.match_source && (
                <span className="match-source-badge">
                  {getMatchSourceLabel(result.match_source)}
                </span>
              )}
            </div>

            {/* Snippet (doc mode) */}
            {mode === 'doc' && result.snippet && (
              <p className="result-snippet">"{result.snippet}"</p>
            )}

            {/* Score bar */}
            <div className="result-score">
              <div
                className="score-bar"
                style={{
                  width: `${Math.min(
                    mode === 'face'
                      ? (result.similarity || 0)
                      : (result.score || 0) * 100,
                    100
                  )}%`,
                }}
              />
              <span className="score-text">
                {mode === 'face'
                  ? `${result.similarity}% match`
                  : `${(result.score * 100).toFixed(1)}% relevance`}
              </span>
            </div>

            {/* Copy feedback */}
            {copiedPath === result.file_path && (
              <div className="copy-feedback">📋 Path copied!</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default ResultsGrid;