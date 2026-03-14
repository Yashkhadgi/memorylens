# MemoryLens

MemoryLens is an AI-powered local search assistant that helps users find:
- **Documents** using natural-language memory cues ("the budget file from last quarter")
- **Photos** using face-based matching (upload one reference photo, find similar faces)

It combines a React frontend with a FastAPI backend, plus indexing/search pipelines for both text and images.

---

## Why this project matters

People remember *context*, not exact filenames or folders. MemoryLens reduces retrieval time by enabling **memory-first search**:
- "I remember what it was about" → semantic document search
- "I remember who was in it" → face-based photo search

This makes digital archives faster to navigate for students, professionals, creators, and teams.

---

## What a hackathon evaluator can quickly verify

### 1) End-to-end working product
- Index a folder containing documents + photos
- Search documents by natural language
- Search photos by uploading a face image
- Open matched files directly from results

### 2) Technical depth
- Multi-modal indexing pipeline (text + images)
- Local vector index for fast semantic retrieval (FAISS)
- Parallel face indexing for performance
- Background indexing with real-time progress tracking

### 3) Product thinking
- Unified UX for two different search modes
- Practical utility for real-world personal/team data
- Cross-platform backend support for file opening (Windows/macOS/Linux)

### 4) Demo readiness
- Clear API endpoints (`/api/index`, `/api/search/docs`, `/api/search/faces`)
- Separate backend + frontend dev flows
- Built frontend can be served from backend static route

---

## Core features

### Document Intelligence
- Extracts text from multiple formats: PDF, DOC/DOCX, PPTX, XLS/XLSX, TXT, MD, CSV
- Generates embeddings and stores vectors in FAISS for semantic retrieval
- Returns ranked matches with snippet preview and similarity score

### Face Intelligence
- Indexes faces from image folders (supports broad image format coverage)
- Uses face similarity search with configurable threshold
- Groups indexed photos by person (cluster-style view)

### Experience Layer
- Folder picker + manual path input for indexing
- Indexing progress UI (processed, indexed, skipped, errors)
- Result cards with one-click open file + copy path
- Face result popups and grouped person rows

---

## Project structure

```text
memorylens/
├─ backend/
│  ├─ main.py
│  ├─ doc_indexer.py
│  ├─ doc_search.py
│  ├─ face_indexer.py
│  ├─ face_search.py
│  ├─ requirements.txt
│  └─ static/                # built frontend assets served by FastAPI
└─ frontend/
	└─ memorylens-ui/
		├─ src/
		└─ package.json
```

---

## System architecture (high level)

1. User selects a local folder to index.
2. Backend starts a background indexing job.
3. Documents are parsed → embedded → stored in FAISS + metadata.
4. Images are processed → faces indexed into a face collection.
5. UI polls progress endpoint and updates live status.
6. User performs:
	- text query (`/api/search/docs`) for documents
	- image upload (`/api/search/faces`) for face matching

---

## Tech stack

### 🎨 Frontend

![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Create React App](https://img.shields.io/badge/Create%20React%20App-CRA-09D3AC?style=for-the-badge&logo=createreactapp&logoColor=black)
![Axios](https://img.shields.io/badge/Axios-HTTP%20Client-5A29E4?style=for-the-badge&logo=axios&logoColor=white)

### ⚙️ Backend

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-ASGI%20Server-2C3E50?style=for-the-badge&logo=gunicorn&logoColor=white)

### 🧠 AI, Search & Indexing

![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-0467DF?style=for-the-badge)
![NumPy](https://img.shields.io/badge/NumPy-Numerics-013243?style=for-the-badge&logo=numpy&logoColor=white)
![Boto3](https://img.shields.io/badge/Boto3-AWS%20SDK-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)
![Amazon Rekognition](https://img.shields.io/badge/Amazon%20Rekognition-Face%20Recognition-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)
![Amazon Textract](https://img.shields.io/badge/Amazon%20Textract-OCR-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)
![Amazon Bedrock](https://img.shields.io/badge/Amazon%20Bedrock-Embeddings-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)

### 📄 Document & Image Processing

![PyMuPDF](https://img.shields.io/badge/PyMuPDF-PDF%20Parsing-4B5563?style=for-the-badge)
![python-docx](https://img.shields.io/badge/python--docx-DOCX%20Parsing-2563EB?style=for-the-badge)
![python-pptx](https://img.shields.io/badge/python--pptx-PPTX%20Parsing-D97706?style=for-the-badge)
![openpyxl](https://img.shields.io/badge/openpyxl-XLSX%20Parsing-16A34A?style=for-the-badge)
![Pillow](https://img.shields.io/badge/Pillow-Image%20Processing-8B5CF6?style=for-the-badge)
![pillow-heif](https://img.shields.io/badge/pillow--heif-HEIC%20Support-7C3AED?style=for-the-badge)

> Note: This README is intentionally generalized for hackathons. The current implementation uses cloud connectors, but the architecture can be adapted to alternate providers.

---

## Local setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm

### 1) Backend setup

```bash
cd backend
pip install -r requirements.txt
```

Create `.env` inside `backend/` (example):

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
REKOGNITION_COLLECTION_ID=memorylens

BEDROCK_ACCESS_KEY=your_access_key
BEDROCK_SECRET_KEY=your_secret_key
TITAN_MODEL_ID=amazon.titan-embed-text-v2:0
```

Run backend:

```bash
uvicorn main:app --reload --port 8000
```

Backend docs: `http://localhost:8000/docs`

### 2) Frontend setup

```bash
cd frontend/memorylens-ui
npm install
npm start
```

Frontend dev URL: `http://localhost:3000`

---

## How to use the project (demo flow)

1. Start backend and frontend.
2. In UI, choose a folder containing documents/photos.
3. Click **Index** and wait for progress completion.
4. For **Document Search**:
	- Enter a memory-like query (example: "budget update meeting")
	- Open a result directly from the card popup
5. For **Face Search**:
	- Upload a reference face image
	- Review grouped matches and open files

---

## API summary

- `GET /api/health` → service health
- `GET /api/status` → indexed counts and runtime status
- `POST /api/index` → start background indexing (`doc`, `face`, `both`)
- `GET /api/index/progress` → live indexing progress
- `GET /api/search/docs?q=...` → semantic document search
- `POST /api/search/faces` → face match search from uploaded image
- `GET /api/faces/groups` → clustered people groups from indexed faces
- `GET /api/open-file?path=...` → open local file in OS default app

---

## Hackathon evaluation checklist (recommended)

- **Innovation:** memory-first multimodal retrieval instead of keyword-only search
- **Execution:** complete indexing + retrieval + UI loop in one product
- **Scalability path:** modular pipelines and replaceable AI connectors
- **User impact:** saves time locating forgotten files/photos
- **Demo clarity:** visible progress, ranked outputs, direct file open action

---

## Proper and responsible use

- Use on folders/data where you have permission to process files and faces.
- Avoid indexing sensitive data without proper access controls.
- Face search should be used for personal productivity or consented organizational use cases.
- For production deployments, add authentication, role-based access, and audit logging.

---

## Current limitations

- Requires valid cloud credentials for current AI connectors.
- Performance depends on dataset size, network, and machine resources.
- No built-in auth layer in this prototype.
- Face matching quality depends on image quality and occlusion conditions.

---

## Future improvements

- Plug-and-play local/open-source model backends
- Incremental indexing (without full reset)
- Multi-user authentication and workspace isolation
- Metadata filters (date/type/person) and advanced ranking
- Packaging with Docker + one-command startup

---

## Pitch-ready one-liner

**MemoryLens turns "I remember what it looked like" and "I remember what it talked about" into instant file retrieval.**

