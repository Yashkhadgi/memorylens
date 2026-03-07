# MemoryLens — Full Build Specification
> Give this entire file to an AI model. It contains everything needed to build the complete project from scratch.

---

## 1. Project Summary

**MemoryLens** is a privacy-first, AWS-powered personal file intelligence system.

Users search their local files using:
- **Face Search** — upload a photo of a person → find every other photo of that person
- **Document Search** — type what you remember writing → find the exact document

**Core principle:** AWS services act as a stateless inference engine. Files are never stored on AWS. All indexes (FAISS, SQLite) live locally on the user's machine.

**Hackathon:** AWS Hackathon — Category: Generative AI on AWS  
**Team:** 4 members (Leader, Member A, Member B, Member C)

---

## 2. Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** — REST API framework
- **uvicorn** — ASGI server
- **boto3** — AWS SDK for Python
- **PyMuPDF (fitz)** — native PDF text extraction
- **python-docx** — DOCX text extraction
- **faiss-cpu** — local vector similarity search
- **sqlite3** — local metadata + keyword search (stdlib)
- **numpy** — vector math
- **Pillow** — image processing
- **python-multipart** — file upload handling
- **python-dotenv** — .env loading

### Frontend
- **React 18** (Create React App)
- **axios** — HTTP client
- **Tailwind CSS** — utility styling

### AWS Services
| Service | Purpose | Used In |
|---|---|---|
| Amazon Rekognition | Face detection, indexing, similarity search | Face pipeline |
| Amazon Textract | OCR — extract text from scanned PDFs and images | Doc pipeline |
| Amazon Bedrock — Claude Sonnet 4 | Natural language query parsing + intent extraction | Doc pipeline |
| Amazon Bedrock — Titan Embeddings V2 | Convert text → 512-dim semantic vectors | Doc pipeline |
| AWS IAM | Least-privilege credentials per service | Both |

---

## 3. Repository Structure

Build the project with this exact structure:

```
memorylens/
├── backend/
│   ├── main.py                   # FastAPI app — all API routes
│   ├── face_indexer.py           # Rekognition: index faces into collection
│   ├── face_search.py            # Rekognition: search photos by face
│   ├── doc_indexer.py            # Textract + Titan: index documents
│   ├── doc_search.py             # Claude + FAISS + SQLite: search documents
│   ├── create_collection.py      # One-time: create Rekognition collection
│   ├── test_aws.py               # Verify all 4 AWS connections
│   ├── test_doc_pipeline.py      # End-to-end doc pipeline test
│   ├── requirements.txt
│   └── .env.example              # Template — never commit real credentials
│
├── frontend/
│   └── memorylens-ui/
│       ├── src/
│       │   ├── App.jsx           # Main app — mode toggle, global state
│       │   ├── SearchBar.jsx     # Text search input
│       │   ├── UploadPanel.jsx   # Face photo drag-and-drop upload
│       │   └── ResultsGrid.jsx   # Results display with scores
│       └── package.json
│
├── sample_data/
│   ├── photos/                   # Test photos (at least 3 with same person)
│   └── docs/                     # Test docs: 1 native PDF, 1 DOCX, 1 scanned PDF
│
└── README.md
```

---

## 4. Environment Variables

Create `backend/.env` (and `backend/.env.example` without real values):

```env
# AWS Account — for Rekognition + Textract
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# Rekognition
REKOGNITION_COLLECTION_ID=memorylens

# Bedrock — separate account/role (Claude + Titan)
BEDROCK_ACCESS_KEY=bedrock_access_key
BEDROCK_SECRET_KEY=bedrock_secret_key
BEDROCK_REGION=us-east-1
```

---

## 5. Backend — File by File Specification

### 5.1 `requirements.txt`

```
fastapi
uvicorn
boto3
pymupdf
python-docx
faiss-cpu
numpy
Pillow
python-multipart
python-dotenv
```

---

### 5.2 `main.py` — FastAPI Application

Build a FastAPI app with these routes:

```
POST /api/index
  Body: { "folder_path": "/Users/you/files" }
  Action: Index all photos into Rekognition collection + all docs into FAISS/SQLite
  Response: { "status": "indexed", "photos_indexed": int, "docs_indexed": int }

POST /api/search/faces
  Body: multipart/form-data with file upload (the reference photo)
  Action: Search Rekognition collection for matching faces
  Response: { "results": [ { "file_path": str, "similarity": float } ] }

GET /api/search/docs
  Query param: ?query=the+text+you+remember
  Action: Parse with Claude → embed with Titan → FAISS + SQLite search → merge
  Response: { "results": [ { "file_path": str, "snippet": str, "score": float, "match_source": str } ] }

GET /api/health
  Response: { "status": "ok" }
```

On app startup (FastAPI lifespan or @app.on_event("startup")):
- Load FAISS index from disk if it exists (`docs.index`)
- Initialize DocIndexer and DocSearcher as singletons

---

### 5.3 `face_indexer.py` — Face Indexing

**Class: `FaceIndexer`**

```python
# Constructor
def __init__(self):
    # boto3 Rekognition client using AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY
    # collection_id from env: REKOGNITION_COLLECTION_ID

# Method: index_photo(file_path: str) -> bool
# - Read image bytes from file_path
# - Call rekognition.index_faces(
#     CollectionId=collection_id,
#     Image={"Bytes": image_bytes},
#     ExternalImageId=file_path,   # store path as the face ID
#     DetectionAttributes=[]
#   )
# - Return True if at least 1 face was indexed, False if no faces found

# Method: index_folder(folder_path: str) -> dict
# - Walk folder recursively
# - Call index_photo() for every .jpg, .jpeg, .png file
# - Return {"indexed": int, "skipped": int, "errors": int}
```

---

### 5.4 `face_search.py` — Face Search

**Class: `FaceSearcher`**

```python
# Constructor
def __init__(self):
    # boto3 Rekognition client

# Method: search_by_face(image_bytes: bytes, threshold: float = 80.0) -> list[dict]
# - Call rekognition.search_faces_by_image(
#     CollectionId=collection_id,
#     Image={"Bytes": image_bytes},
#     FaceMatchThreshold=threshold,
#     MaxFaces=50
#   )
# - Map results to list of dicts:
#   [{ "file_path": face["Face"]["ExternalImageId"],
#      "similarity": round(face["Similarity"], 2),
#      "face_id": face["Face"]["FaceId"] }]
# - Sort by similarity descending
# - Return list
```

---

### 5.5 `doc_indexer.py` — Document Indexing

This is the most complex file. Build it carefully.

**Class: `DocIndexer`**

```python
# Constructor
def __init__(self):
    # Bedrock client: boto3.client("bedrock-runtime",
    #   region_name=BEDROCK_REGION,
    #   aws_access_key_id=BEDROCK_ACCESS_KEY,
    #   aws_secret_access_key=BEDROCK_SECRET_KEY)
    # Textract client: boto3.client("textract",
    #   aws_access_key_id=AWS_ACCESS_KEY_ID,
    #   aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    #   region_name=AWS_REGION)
    # FAISS index: faiss.IndexFlatL2(512)   ← 512 dimensions for Titan V2
    # SQLite: connect to "docs.db", create table if not exists
    # SQLite schema:
    #   CREATE TABLE IF NOT EXISTS docs (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     file_path TEXT UNIQUE,
    #     file_type TEXT,
    #     text_snippet TEXT,
    #     full_text TEXT,
    #     faiss_id INTEGER,
    #     indexed_at TEXT
    #   )
    # self.faiss_id_counter = 0  (increment on each indexed doc)

# Method: extract_text_native(file_path: str) -> str
# - .pdf  → use fitz.open(file_path), extract text from all pages
# - .docx → use docx.Document(file_path), join all paragraph.text
# - .txt  → open and read
# - others → return ""

# Method: is_scanned(file_path: str, native_text: str) -> bool
# - If file is PDF and len(native_text.strip()) < 50 → return True (needs OCR)
# - If file is image (.jpg/.png/.tiff) → return True
# - Otherwise → return False

# Method: extract_text_ocr(file_path: str) -> str
# - Read file bytes
# - Call textract.detect_document_text(Document={"Bytes": file_bytes})
# - Extract all blocks where BlockType == "LINE"
# - Join with " " and return
# - Handle exception: if file > 5MB, log warning and return ""

# Method: get_embedding(text: str) -> np.ndarray shape (512,)
# - Truncate text to 8000 characters (Titan input limit)
# - Call bedrock.invoke_model(
#     modelId="amazon.titan-embed-text-v2:0",
#     body=json.dumps({"inputText": text, "dimensions": 512})
#   )
# - Parse response body JSON → ["embedding"]
# - Return np.array(embedding, dtype=np.float32)

# Method: index_file(file_path: str) -> bool
# - Skip if file_path already in SQLite (check by file_path UNIQUE)
# - native_text = extract_text_native(file_path)
# - if is_scanned(file_path, native_text): text = extract_text_ocr(file_path)
# - else: text = native_text
# - if not text.strip(): return False
# - embedding = get_embedding(text)
# - Add embedding to FAISS index
# - Insert row into SQLite:
#   file_path, file_type (extension), text_snippet (first 500 chars),
#   full_text, faiss_id=self.faiss_id_counter, indexed_at=datetime.now().isoformat()
# - self.faiss_id_counter += 1
# - return True

# Method: index_folder(folder_path: str) -> dict
# - Walk folder recursively with os.walk
# - Supported extensions: .pdf, .docx, .txt, .png, .jpg, .jpeg, .tiff
# - Call index_file() for each
# - Return {"indexed": int, "skipped": int, "errors": int}

# Method: save_index()
# - faiss.write_index(self.index, "docs.index")

# Method: load_index()
# - If "docs.index" exists: self.index = faiss.read_index("docs.index")
# - Sync self.faiss_id_counter from SQLite count
```

---

### 5.6 `doc_search.py` — Document Search

**Class: `DocSearcher`**

```python
# Constructor
def __init__(self, doc_indexer: DocIndexer):
    # Store reference to doc_indexer (shares same FAISS index + SQLite)
    # Bedrock client (same as indexer)

# Method: parse_query_with_claude(query: str) -> dict
# - Call Bedrock Claude Sonnet 4:
#   modelId = "us.anthropic.claude-sonnet-4-5-20251001"
#   System prompt: "You are a search query parser. Extract structured data from user queries."
#   User prompt:
#     f"""Parse this file search query and return ONLY valid JSON (no markdown):
#     Query: "{query}"
#     Return: {{"type": "document"|"image"|"any", "keywords": ["word1","word2",...], "intent": "brief description"}}
#     Extract all meaningful keywords, names, numbers, and phrases."""
# - Parse JSON from response
# - Return dict with keys: type, keywords, intent
# - On parse error: return {"type": "any", "keywords": query.split(), "intent": query}

# Method: semantic_search(query_text: str, top_k: int = 20) -> list[dict]
# - Get embedding for query_text using doc_indexer.get_embedding()
# - Run FAISS search: distances, indices = self.index.search(query_vec, top_k)
# - For each result index, look up SQLite by faiss_id
# - Convert L2 distance to similarity score: score = 1 / (1 + distance)
# - Return [{"file_path", "snippet": text_snippet, "score", "source": "semantic"}]

# Method: keyword_search(keywords: list[str], top_k: int = 20) -> list[dict]
# - Build SQLite query dynamically:
#   WHERE full_text LIKE '%kw1%' OR full_text LIKE '%kw2%' ...
# - Score each result by count of matching keywords
# - Normalize score to 0–1 range
# - Return [{"file_path", "snippet": text_snippet, "score", "source": "keyword"}]

# Method: extract_smart_snippet(full_text: str, keywords: list[str], window: int = 300) -> str
# - Find position in full_text where most keywords cluster together
# - Return text window around that position with "..." prefix/suffix

# Method: merge_and_rank(semantic: list, keyword: list) -> list[dict]
# - Combine both lists
# - If same file_path appears in both: boost score by 0.2, set source = "semantic+keyword"
# - Deduplicate by file_path (keep highest score)
# - Sort by score descending
# - Return top 10

# Method: search(query: str) -> list[dict]
# - parsed = parse_query_with_claude(query)
# - sem_results = semantic_search(query)
# - kw_results = keyword_search(parsed["keywords"])
# - merged = merge_and_rank(sem_results, kw_results)
# - For each result, call extract_smart_snippet to improve the snippet
# - Return final list: [{"file_path", "file_type", "snippet", "score", "match_source"}]
```

---

### 5.7 `create_collection.py` — One-Time Setup

```python
# Script: run once to create the Rekognition face collection
import boto3
from dotenv import load_dotenv
import os

load_dotenv()
client = boto3.client("rekognition",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"))

try:
    client.create_collection(CollectionId=os.getenv("REKOGNITION_COLLECTION_ID"))
    print("✅ Collection created")
except client.exceptions.ResourceAlreadyExistsException:
    print("ℹ️ Collection already exists")
```

---

### 5.8 `test_aws.py` — Connection Verification

```python
# Script: verify all 4 AWS services are reachable
# Test 1 — Rekognition: call list_collections(), print ✅ or ❌
# Test 2 — Textract: call get_document_analysis with dummy, catch expected error, print ✅ or ❌
# Test 3 — Bedrock Claude: send "say hello" message, check response, print ✅ or ❌
# Test 4 — Bedrock Titan: embed "test", check vector length == 512, print ✅ or ❌

# Expected output when working:
# ✅ Rekognition — connected
# ✅ Textract — connected
# ✅ Bedrock Claude 4 — connected
# ✅ Bedrock Titan — connected
```

---

### 5.9 `test_doc_pipeline.py` — End-to-End Test

```python
# Script: full pipeline test
# 1. Init DocIndexer, index ../sample_data/docs/ folder
# 2. Save index
# 3. Init DocSearcher
# 4. Search for exact phrase from a known document → assert results > 0
# 5. Search for semantic/fuzzy query → print top 3 results with scores
# 6. Search for content from the scanned PDF (tests Textract path)
# 7. Print ✅ or ❌ for each test
# 8. Final: "🎉 All tests passed!" or raise AssertionError
```

---

## 6. Frontend — File by File Specification

### 6.1 `App.jsx` — Main Application

State managed here:
- `mode`: `"face"` | `"doc"` — which search mode is active
- `results`: array of result objects from API
- `isLoading`: boolean
- `isIndexing`: boolean

Layout:
- Top navbar: "MemoryLens" logo + mode toggle buttons ("🔍 Face Search" / "📄 Doc Search")
- Center: conditionally render `<UploadPanel>` (face mode) or `<SearchBar>` (doc mode)
- Below: `<ResultsGrid results={results} mode={mode} />`
- Bottom-left floating button: "Index Folder" — triggers a folder path input dialog → POST /api/index

API calls via axios:
- `POST /api/search/faces` — FormData with the uploaded image
- `GET /api/search/docs?query=...` — text query

---

### 6.2 `UploadPanel.jsx` — Face Photo Upload

- Drag-and-drop zone: accepts image files (.jpg, .png)
- On drop/select: preview the image in the panel
- "Search for this person" button → calls App's search handler
- Show a loading spinner while searching
- Props: `onSearch(imageFile)`, `isLoading`

---

### 6.3 `SearchBar.jsx` — Document Text Search

- Single text input: placeholder "Type what you remember writing..."
- Submit on Enter key or clicking search button
- Debounce: wait 300ms after last keystroke before triggering
- Show query parsing feedback if desired (optional: show "Searching with Claude...")
- Props: `onSearch(queryText)`, `isLoading`

---

### 6.4 `ResultsGrid.jsx` — Results Display

For **face search results** (`mode === "face"`):
- Grid of image cards
- Each card: thumbnail photo, filename, similarity percentage badge
- Color-code badge: green ≥90%, yellow ≥80%, orange below

For **doc search results** (`mode === "doc"`):
- List of document cards
- Each card: file icon (based on type), filename, text snippet (highlighted keywords), score bar, match source badge ("semantic+keyword", "semantic", "keyword")
- Clicking a card: copy full file path to clipboard

Empty state: "No results found. Try indexing a folder first."

Props: `results`, `mode`

---

## 7. Data Contracts — API Response Formats

### Face Search Response
```json
{
  "results": [
    {
      "file_path": "/Users/you/photos/birthday.jpg",
      "similarity": 94.2,
      "face_id": "abc-123"
    }
  ]
}
```

### Doc Search Response
```json
{
  "results": [
    {
      "file_path": "/Users/you/docs/budget_q3.pdf",
      "file_type": "pdf",
      "snippet": "...Project Budget 9195 was approved for Q3 2024 with total...",
      "score": 0.94,
      "match_source": "semantic+keyword"
    }
  ]
}
```

### Index Response
```json
{
  "status": "indexed",
  "photos_indexed": 47,
  "docs_indexed": 23
}
```

---

## 8. Bedrock Model IDs (Use Exactly)

```
Claude Sonnet 4:    us.anthropic.claude-sonnet-4-5-20251001
Titan Embeddings:   amazon.titan-embed-text-v2:0
```

---

## 9. Key Technical Decisions

### Native PDF vs Scanned PDF Detection
```python
# Use PyMuPDF first. If extracted text < 50 chars, it's likely a scanned PDF.
# Fall back to Textract for OCR.
native_text = extract_text_native(path)
if len(native_text.strip()) < 50 and path.endswith(".pdf"):
    text = extract_text_ocr(path)  # Textract
else:
    text = native_text
```

### FAISS Index
- Use `faiss.IndexFlatL2(512)` — exact L2 distance, no approximation needed at personal file scale
- Persist to `docs.index` file with `faiss.write_index()` / `faiss.read_index()`
- Map FAISS integer IDs to file metadata via SQLite `faiss_id` column

### Titan Embeddings Input Limit
- Max ~8,000 characters input. Truncate long documents before embedding.
- For very long documents, consider chunking (split into 1000-char chunks, embed each, store all with same file_path)

### Rekognition Face Storage
- Use `ExternalImageId` = file path of the photo
- This lets you retrieve the file path directly from search results without a separate lookup table

### CORS
- Enable CORS in FastAPI for `http://localhost:3000` during development

---

## 10. Error Handling Requirements

| Error | Behavior |
|---|---|
| Textract file > 5MB | Log warning, skip file, continue indexing |
| No face detected in photo | Return empty results, not an error |
| FAISS index not loaded | Return 503 with message "Index not built yet. Please index a folder first." |
| Bedrock rate limit | Retry once after 2 seconds |
| File unreadable | Log error, skip, continue |
| Claude returns invalid JSON | Fall back to splitting query string on spaces as keywords |

---

## 11. README.md Content

Write a README that includes:
1. Project overview (2 sentences)
2. AWS services table
3. Prerequisites (Python 3.11+, Node 18+, AWS account)
4. Setup steps (clone → venv → .env → create_collection.py → test_aws.py → uvicorn → npm start)
5. Usage (index folder → face search → doc search)
6. Privacy section (files never stored on AWS)
7. Architecture diagram (ASCII)

---

## 12. Build Order (Recommended)

Build files in this order:

1. `requirements.txt`
2. `.env.example`
3. `create_collection.py`
4. `test_aws.py`
5. `doc_indexer.py` (biggest, most complex)
6. `doc_search.py`
7. `face_indexer.py`
8. `face_search.py`
9. `main.py` (wire everything together)
10. `test_doc_pipeline.py`
11. Frontend: `App.jsx` → `SearchBar.jsx` → `UploadPanel.jsx` → `ResultsGrid.jsx`
12. `README.md`

---

## 13. Definition of Done

The project is complete when:

- [ ] `python test_aws.py` shows 4 green checkmarks
- [ ] `python create_collection.py` creates the Rekognition collection
- [ ] `uvicorn main:app --reload` starts without errors
- [ ] `npm start` launches the React app at localhost:3000
- [ ] Indexing a folder with photos and docs completes without crashing
- [ ] Face search: upload photo → returns matching photos with similarity scores
- [ ] Doc search: "Project Budget 9195" → returns the correct document
- [ ] Doc search: "financial planning last quarter" → semantic match works
- [ ] Scanned PDF is indexed via Textract (not PyMuPDF)
- [ ] `python test_doc_pipeline.py` passes all assertions
- [ ] Frontend displays results correctly in both modes

---

*MemoryLens — Stop remembering file names. Start remembering faces and thoughts.*  
*Built on Amazon Rekognition · Textract · Bedrock Claude Sonnet 4 · Titan Embeddings V2 · FastAPI · React*