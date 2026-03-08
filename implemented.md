# MemoryLens — Implementation Log

> This file tracks what has been implemented. Updated after each round of work.

---

## Pre-existing (before corrections)

The following files existed as part of the initial project scaffold:

### Backend
| File | Status |
|------|--------|
| [main.py](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/backend/main.py) | ✅ Exists — stub routes with TODOs, not wired to any real logic |
| [requirements.txt](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/backend/requirements.txt) | ✅ Exists — over-specified with 30 pinned transitive deps |
| [create_collection.py](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/backend/create_collection.py) | ✅ Exists — works but hardcodes values |
| [test_aws.py](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/backend/test_aws.py) | ✅ Exists — works but has wrong Claude model ID |
| [face_indexer.py](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/backend/face_indexer.py) | ⚠️ Exists but empty |
| [doc_indexer.py](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/backend/doc_indexer.py) | ⚠️ Exists but empty |
| [face_search.py](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/backend/face_search.py) | ❌ Missing |
| [doc_search.py](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/backend/doc_search.py) | ❌ Missing |
| [.env.example](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/backend/.env.example) | ❌ Missing |
| [test_doc_pipeline.py](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/backend/test_doc_pipeline.py) | ❌ Missing |

### Frontend (`frontend/memorylens-ui/`)
| File | Status |
|------|--------|
| `App.js` | ✅ Exists — good UI but uses `fetch`, has dummy fallbacks |
| `App.css` | ✅ Exists — well-styled with dark/light mode |
| `SearchBar.jsx` | ✅ Exists — has typewriter effect, no debounce |
| `UploadPanel.jsx` | ✅ Exists — drag-and-drop works |
| `ResultsGrid.jsx` | ✅ Exists — doesn't match API data contracts |
| `index.js` | ✅ Exists |
| `package.json` | ✅ Exists — missing `axios` and `tailwindcss` |

### Root
| File | Status |
|------|--------|
| `.gitignore` | ✅ Exists — incomplete |
| `README.md` | ⚠️ Exists but empty |
| `sample_data/docs/` | ✅ Directory exists (empty, has `.gitkeep`) |
| `sample_data/photos/` | ✅ Directory exists (empty, has `.gitkeep`) |

---

---

## Round 1 — Project Structure Correction *(2026-03-07)*

### Backend (10 files — all complete)
| File | Change |
|------|--------|
| `requirements.txt` | ✅ Replaced 30 pinned deps → clean 10-package list |
| `.env.example` | ✅ Created credential template (7 env vars) |
| `create_collection.py` | ✅ Uses env vars for region + collection ID |
| `test_aws.py` | ✅ Fixed Claude model ID, uses env vars for regions |
| `main.py` | ✅ Full rewrite: lifespan, wired services, correct routes + params |
| `face_indexer.py` | ✅ Implemented `FaceIndexer` class |
| `face_search.py` | ✅ Created `FaceSearcher` class |
| `doc_indexer.py` | ✅ Implemented `DocIndexer` (text extraction, OCR, embeddings, FAISS, SQLite) |
| `doc_search.py` | ✅ Created `DocSearcher` (Claude parsing, semantic+keyword, merge+rank) |
| `test_doc_pipeline.py` | ✅ Created end-to-end test script |

### Frontend (6 files)
| File | Change |
|------|--------|
| `frontend/.gitkeep` | 🗑️ Deleted |
| `App.js` → `App.jsx` | ✅ Renamed + rewritten with axios, Index Folder FAB |
| `SearchBar.jsx` | ✅ Added 300ms debounce, fixed `onKeyPress` → `onKeyDown` |
| `ResultsGrid.jsx` | ✅ Aligned with API contracts, badges, click-to-copy |
| `App.css` | ✅ Added CSS for FAB, badges, copy feedback, info toast |
| `package.json` | ✅ Added `axios` dependency |

### Root
| File | Change |
|------|--------|
| `.gitignore` | ✅ Added `docs.db`, `docs.index` |
| `README.md` | ✅ Full README per spec (overview, setup, architecture) |

---

*— Future implementation records will be appended below —*
