import { useState, useEffect, useRef, useCallback } from 'react';

const placeholders = [
  "Type what you remember... e.g. 'Project budget 9195'",
  "Try 'Meeting notes from last Monday'...",
  "Try 'Invoice from November'...",
  "Try 'Report about Q3 targets'...",
  "Try 'Email about the new feature'...",
];

function SearchBar({ onSearch, isLoading }) {
  const [query, setQuery] = useState('');
  const [placeholder, setPlaceholder] = useState('');
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [charIndex, setCharIndex] = useState(0);
  const [deleting, setDeleting] = useState(false);
  const debounceTimer = useRef(null);

  // Typewriter effect for placeholder
  useEffect(() => {
    const current = placeholders[phraseIndex];
    let timeout;

    if (!deleting && charIndex < current.length) {
      timeout = setTimeout(() => {
        setPlaceholder(current.slice(0, charIndex + 1));
        setCharIndex(c => c + 1);
      }, 45);
    } else if (!deleting && charIndex === current.length) {
      timeout = setTimeout(() => setDeleting(true), 1800);
    } else if (deleting && charIndex > 0) {
      timeout = setTimeout(() => {
        setPlaceholder(current.slice(0, charIndex - 1));
        setCharIndex(c => c - 1);
      }, 25);
    } else if (deleting && charIndex === 0) {
      setDeleting(false);
      setPhraseIndex(i => (i + 1) % placeholders.length);
    }

    return () => clearTimeout(timeout);
  }, [charIndex, deleting, phraseIndex]);

  // Debounced search trigger
  const debouncedSearch = useCallback(
    (searchQuery) => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
      debounceTimer.current = setTimeout(() => {
        if (searchQuery.trim()) {
          onSearch(searchQuery.trim());
        }
      }, 300);
    },
    [onSearch]
  );

  const handleSubmit = () => {
    // Cancel any pending debounce
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }
    if (query.trim()) onSearch(query.trim());
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSubmit();
  };

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
    };
  }, []);

  return (
    <div className="search-bar">
      <input
        id="doc-search-input"
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="search-input"
        disabled={isLoading}
      />
      <button
        id="doc-search-btn"
        onClick={handleSubmit}
        className="search-btn"
        disabled={isLoading}
      >
        🔍 Search
      </button>
    </div>
  );
}

export default SearchBar;