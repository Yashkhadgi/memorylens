# MemoryLens — Implementation Plans

> This file is a running log of all implementation plans. Each plan is numbered and separated by a horizontal rule.

---

## Plan #1 — Project Structure Correction *(2026-03-07)*

**Goal:** Align the existing project scaffold with the [build specification](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/memorylens%20build%20prompt.md). The current code has placeholder stubs, missing files, wrong API contracts, and naming issues.

### Backend Changes

| # | File | Action | What's Wrong / What to Do |
|---|------|--------|--------------------------|
| 1 | [requirements.txt](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/backend/requirements.txt) | MODIFY | Replace 30 pinned transitive deps → clean 10-package list per spec |
| 2 | `.env.example` | NEW | Create credential template (7 env vars) |
| 3 | [create_collection.py](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/backend/create_collection.py) | MODIFY | Hardcoded `"us-east-1"` and `"memorylens"` → use env vars |
| 4 | [test_aws.py](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/backend/test_aws.py) | MODIFY | Wrong Claude model ID, hardcoded regions → use env vars |
| 5 | [main.py](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/backend/main.py) | MODIFY | Wrong param name (`q`→`query`), missing `/api/health`, missing body for `/api/index`, add lifespan, remove `/api/stats` and `/`, wire real imports, set CORS to `localhost:3000` |
| 6 | [face_indexer.py](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/backend/face_indexer.py) | MODIFY | Empty → implement `FaceIndexer` class |
| 7 | `face_search.py` | NEW | Implement `FaceSearcher` class |
| 8 | [doc_indexer.py](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/backend/doc_indexer.py) | MODIFY | Empty → implement `DocIndexer` class (most complex) |
| 9 | `doc_search.py` | NEW | Implement `DocSearcher` class |
| 10 | `test_doc_pipeline.py` | NEW | End-to-end doc pipeline test script |

### Frontend Changes

| # | File | Action | What to Do |
|---|------|--------|-----------|
| 1 | [frontend/.gitkeep](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/frontend/.gitkeep) | DELETE | No longer needed |
| 2 | [package.json](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/frontend/memorylens-ui/package.json) | MODIFY | Add `axios`, `tailwindcss`, `postcss`, `autoprefixer` |
| 3 | [App.js](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/frontend/memorylens-ui/src/App.js) → `App.jsx` | RENAME+MODIFY | Rename, use `axios`, remove dummy data, add "Index Folder" button |
| 4 | [SearchBar.jsx](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/frontend/memorylens-ui/src/SearchBar.jsx) | MODIFY | Add 300ms debounce, fix deprecated `onKeyPress` |
| 5 | [ResultsGrid.jsx](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/frontend/memorylens-ui/src/ResultsGrid.jsx) | MODIFY | Align with API contracts (`file_path`, `similarity`, `match_source`), add badges, click-to-copy |
| 6 | [index.js](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/frontend/memorylens-ui/src/index.js) | MODIFY | Update import path if needed |
| 7 | Tailwind config | NEW | Set up `tailwind.config.js` + `postcss.config.js` |

### Root Changes

| # | File | Action | What to Do |
|---|------|--------|-----------|
| 1 | [.gitignore](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/.gitignore) | MODIFY | Add `docs.db`, `docs.index` |
| 2 | [README.md](file:///f:/Hackathon/Hack-AI-Bharat/Memor%20Lens/memorylens/README.md) | MODIFY | Write full README per spec §11 |

### Verification
- `python -c "import main, face_indexer, face_search, doc_indexer, doc_search"` — all modules import
- `npm run build` — React builds without errors
- (Manual, needs AWS creds) `python test_aws.py`, `uvicorn main:app`, `npm start`

---

*— Future plans will be appended below this line —*
