function ResultsGrid({ results, mode }) {
  return (
    <div className="results-section">
      <h3>Found {results.length} result{results.length !== 1 ? 's' : ''}</h3>
      <div className="results-grid">
        {results.map((result, index) => (
          <div key={index} className="result-card">
            <div className="result-header">
              <span className="result-icon">
                {mode === 'face' ? '📸' : '📄'}
              </span>
              <span className="result-filename">{result.filename}</span>
            </div>
            {result.snippet && (
              <p className="result-snippet">"{result.snippet}"</p>
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