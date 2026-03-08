import { useState, useRef } from 'react';

function UploadPanel({ onSearch }) {
  const [preview, setPreview] = useState(null);
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handleFile = (selectedFile) => {
    if (!selectedFile) return;
    setFile(selectedFile);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(selectedFile);
  };

  const handleFileChange = (e) => handleFile(e.target.files[0]);

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => setDragging(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && dropped.type.startsWith('image/')) {
      handleFile(dropped);
    }
  };

  const handleSearch = () => {
    if (file) onSearch(file);
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div className="upload-panel">
      <div
        className={`upload-drop-zone ${dragging ? 'dragging' : ''} ${preview ? 'has-preview' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !preview && inputRef.current.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />

        {preview ? (
          <div className="preview-wrapper">
            <img src={preview} alt="Preview" className="preview-img" />
            <div className="preview-overlay">
              <span>✅ Ready to search</span>
            </div>
          </div>
        ) : (
          <div className="upload-placeholder">
            <div className="upload-icon">📸</div>
            <p className="upload-title">
              {dragging ? '📂 Drop it here!' : 'Drag & drop a photo'}
            </p>
            <p className="upload-subtitle">or click to browse</p>
          </div>
        )}
      </div>

      {file && (
        <div className="upload-actions">
          <button onClick={handleSearch} className="search-btn">
            🔍 Find Matching Faces
          </button>
          <button onClick={handleReset} className="reset-btn">
            🗑️ Remove
          </button>
        </div>
      )}
    </div>
  );
}

export default UploadPanel;