import { useState, useEffect, useRef } from 'react';

const API_BASE = 'http://localhost:8000';

function FaceGroups({ searchResults }) {
  const [groups, setGroups] = useState(searchResults || []);
  const [loading, setLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [copyFeedback, setCopyFeedback] = useState(false);

  // Fetch face groups from backend
  const fetchGroups = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/faces/groups`);
      const data = await res.json();
      if (data.success) {
        setGroups(data.groups || []);
      }
    } catch (e) {
      console.log('Could not fetch face groups');
    }
    setLoading(false);
  };

  useEffect(() => {
    if (searchResults) {
      setGroups(searchResults);
    } else {
      fetchGroups();
    }
  }, [searchResults]);

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

  if (loading) {
    return (
      <div className="face-groups-loading">
        <div className="spinner" />
        Loading face groups...
      </div>
    );
  }

  if (groups.length === 0) {
    return null; // Don't render anything if no groups
  }

  return (
    <div className="face-groups-container">
      <h3 className="face-groups-title">
        {searchResults
          ? `🔍 Found ${groups.length} ${groups.length === 1 ? 'Person' : 'People'} in search photo`
          : `👥 Detected ${groups.length} ${groups.length === 1 ? 'Person' : 'People'} in indexed files`}
      </h3>

      {groups.map((group) => (
        <PersonRow
          key={group.person_id}
          group={group}
          onImageClick={setSelectedImage}
        />
      ))}

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

// ── Individual Person Row with horizontal scroll ──
function PersonRow({ group, onImageClick }) {
  const scrollRef = useRef(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const checkScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    setCanScrollLeft(el.scrollLeft > 0);
    setCanScrollRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 2);
  };

  useEffect(() => {
    checkScroll();
    const el = scrollRef.current;
    if (el) el.addEventListener('scroll', checkScroll);
    return () => el && el.removeEventListener('scroll', checkScroll);
  }, []);

  const scroll = (dir) => {
    const el = scrollRef.current;
    if (!el) return;
    const amount = el.clientWidth * 0.8;
    el.scrollBy({ left: dir === 'left' ? -amount : amount, behavior: 'smooth' });
  };

  const getFilename = (filepath) => {
    if (!filepath) return 'Unknown';
    return filepath.split(/[/\\]/).pop();
  };

  return (
    <div className="person-row">
      <div className="person-row-header">
        <span className="person-label">Person {group.person_id + 1}</span>
        <span className="person-count">{group.count} photo{group.count !== 1 ? 's' : ''}</span>
      </div>

      <div className="person-scroll-wrapper">
        {canScrollLeft && (
          <button className="scroll-arrow scroll-left" onClick={() => scroll('left')}>‹</button>
        )}

        <div className="person-scroll" ref={scrollRef}>
          {group.faces.map((face, i) => (
            <div
              key={face.face_id}
              className="person-thumb"
              onClick={() => onImageClick(face)}
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              <img
                src={`${API_BASE}/api/image?path=${encodeURIComponent(face.file_path)}`}
                alt={getFilename(face.file_path)}
                className="person-thumb-img"
                loading="lazy"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.parentElement.classList.add('img-error');
                }}
              />
              <p className="person-thumb-name" title={getFilename(face.file_path)}>
                {getFilename(face.file_path)}
              </p>
            </div>
          ))}
        </div>

        {canScrollRight && (
          <button className="scroll-arrow scroll-right" onClick={() => scroll('right')}>›</button>
        )}
      </div>
    </div>
  );
}

export default FaceGroups;
