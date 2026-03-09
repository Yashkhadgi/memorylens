# MemoryLens — System Architecture

```
                            ┌──────────┐
                            │   User   │
                            └────┬─────┘
                                 │
                                 ▼
                ┌────────────────────────────────┐
                │       React Frontend (UI)      │
                │                                │
                │  Search · Index · Results ·    │
                │        File Viewer             │
                └──────────────┬─────────────────┘
                               │
                           REST API
                               │
                               ▼
                ┌────────────────────────────────┐
                │       FastAPI Backend          │
                │                                │
                │  Router · Orchestration ·      │
                │  File I/O · Static Serving     │
                └──────┬─────────────┬───────────┘
                       │             │
            ┌──────────┘             └──────────┐
            ▼                                   ▼
┌───────────────────────┐         ┌───────────────────────┐
│  Document Pipeline    │         │    Face Pipeline       │
│                       │         │                        │
│  • Parse Documents    │         │  • Image Processing    │
│    (PDF, DOCX, PPTX,  │         │  • Face Indexing       │
│     XLSX, TXT)        │         │  • Face Matching       │
│  • Generate Embeddings│         │  • Face Grouping       │
│  • Vector Indexing    │         │                        │
│  • Semantic Search    │         │                        │
└──────────┬────────────┘         └───────────┬────────────┘
           │                                  │
           └──────────┐         ┌─────────────┘
                      ▼         ▼
           ┌────────────────────────────────┐
           │      Storage & Results         │
           │                                │
           │  FAISS Index · Metadata ·      │
           │  Search Results · People       │
           │  Groups · Open Files           │
           └──────────────┬─────────────────┘
                          │
           ┌──────────────┼──────────────┐
           ▼              ▼              ▼
    ┌─────────────┐ ┌───────────┐ ┌──────────────┐
    │AWS Textract │ │AWS Bedrock│ │AWS Rekognition│
    │   (OCR)     │ │(Embed+AI) │ │  (Face AI)   │
    └─────────────┘ └───────────┘ └──────────────┘
```

---

## Component Details

### 1. React Frontend (UI)
| Feature | Description |
|---------|-------------|
| **Search Interface** | Natural language search for documents and face-based photo search |
| **Index Panel** | Folder selection and indexing controls with mode selection (docs/faces/both) |
| **Results Display** | Ranked search results with relevance scores and text snippets |
| **File Viewer** | Open matched files directly from the app |

---

### 2. FastAPI Backend
| Module | File | Role |
|--------|------|------|
| **API Router** | `main.py` | Routes all `/api/*` endpoints |
| **Task Orchestration** | `main.py` | Background threading for indexing tasks |
| **File Handling** | `main.py` | Serve images, open local files cross-platform |
| **Static Serving** | `main.py` | Serves the React production build |

---

### 3. Document Search Pipeline
| Step | File | Technology |
|------|------|------------|
| **Parse Documents** | `doc_indexer.py` | PyMuPDF, python-docx, python-pptx, openpyxl |
| **OCR Fallback** | `doc_indexer.py` | AWS Textract (for scanned/image-based docs) |
| **Generate Embeddings** | `doc_indexer.py` | AWS Bedrock — Titan Embed Text V2 (512-dim) |
| **Vector Indexing** | `doc_indexer.py` | FAISS (IndexFlatIP) |
| **Semantic Search** | `doc_search.py` | AWS Bedrock — Nova Lite (AI query parsing) + FAISS |

---

### 4. Face Search Pipeline
| Step | File | Technology |
|------|------|------------|
| **Image Processing** | `face_indexer.py` | Pillow — format conversion, resizing, HEIC support |
| **Face Indexing** | `face_indexer.py` | AWS Rekognition — parallel ThreadPoolExecutor |
| **Face Matching** | `face_search.py` | AWS Rekognition — `search_faces_by_image` |
| **Face Grouping** | `face_search.py` | AWS Rekognition — `search_faces` clustering |

---

### 5. Storage & Results
| Component | Description |
|-----------|-------------|
| **FAISS Index** | Local vector store (`doc_index.faiss`) for document embeddings |
| **Metadata** | Pickled metadata (`doc_meta.pkl`) with file paths, names, snippets |
| **Search Results** | Ranked document matches with relevance scores |
| **Face Matches** | Photos containing matching faces with similarity percentages |
| **People Groups** | Auto-grouped faces by person (Google Photos-style) |
| **Open Files** | Cross-platform file launcher (macOS, Windows, Linux) |

---

### 6. AWS Cloud Services
| Service | Usage |
|---------|-------|
| **AWS Textract** | OCR for scanned PDFs and image-based documents |
| **AWS Bedrock — Titan Embed V2** | 512-dimensional text embeddings for semantic search |
| **AWS Bedrock — Nova Lite** | AI-powered natural language query understanding |
| **AWS Rekognition** | Face detection, indexing, matching, and grouping |

---

### Data Flow Summary

```
User Query (text)  →  Frontend  →  Backend  →  Nova Lite (parse)
                                              →  Titan V2 (embed)
                                              →  FAISS (search)
                                              →  Ranked Results

User Query (photo) →  Frontend  →  Backend  →  Rekognition (match)
                                              →  Matched Photos

Indexing (folder)  →  Frontend  →  Backend  →  doc_indexer (text → embeddings → FAISS)
                                              →  face_indexer (images → Rekognition)
```
