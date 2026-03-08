import { useState, useEffect } from 'react';

const placeholders = [
  "Type what you remember... e.g. 'Project budget 9195'",
  "Try 'Meeting notes from last Monday'...",
  "Try 'Invoice from November'...",
  "Try 'Report about Q3 targets'...",
  "Try 'Email about the new feature'...",
];

function SearchBar({ onSearch }) {
  const [query, setQuery] = useState('');
  const [placeholder, setPlaceholder] = useState('');
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [charIndex, setCharIndex] = useState(0);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const current = placeholders[phraseIndex];
    let timeout;

    if (!deleting && charIndex < current.length) {
      // Typing
      timeout = setTimeout(() => {
        setPlaceholder(current.slice(0, charIndex + 1));
        setCharIndex(c => c + 1);
      }, 45);
    } else if (!deleting && charIndex === current.length) {
      // Pause at end
      timeout = setTimeout(() => setDeleting(true), 1800);
    } else if (deleting && charIndex > 0) {
      // Deleting
      timeout = setTimeout(() => {
        setPlaceholder(current.slice(0, charIndex - 1));
        setCharIndex(c => c - 1);
      }, 25);
    } else if (deleting && charIndex === 0) {
      // Move to next phrase
      setDeleting(false);
      setPhraseIndex(i => (i + 1) % placeholders.length);
    }

    return () => clearTimeout(timeout);
  }, [charIndex, deleting, phraseIndex]);

  const handleSubmit = () => {
    if (query.trim()) onSearch(query.trim());
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') handleSubmit();
  };

  return (
    <div className="search-bar">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder={placeholder}
        className="search-input"
      />
      <button onClick={handleSubmit} className="search-btn">
        🔍 Search
      </button>
    </div>
  );
}

export default SearchBar;