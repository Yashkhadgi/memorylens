# 🧠 MemoryLens

**Privacy-first, AWS-powered personal file intelligence.**  
Search your local files by face or memory — files never leave your machine.

---

## AWS Services Used

| Service | Purpose |
|---|---|
| Amazon Rekognition | Face detection, indexing, similarity search |
| Amazon Textract | OCR — extract text from scanned PDFs and images |
| Amazon Bedrock — Claude Sonnet 4 | Natural language query parsing + intent extraction |
| Amazon Bedrock — Titan Embeddings V2 | Convert text → 512-dim semantic vectors |

---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **AWS Account** with access to Rekognition, Textract, and Bedrock

---

## Setup

### 1. Clone & Install Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure AWS Credentials

```bash
cp .env.example .env
# Edit .env with your real AWS credentials
```

### 3. Create Rekognition Collection (one-time)

```bash
python create_collection.py
```

### 4. Verify AWS Connections

```bash
python test_aws.py
```

Expected output:
```
✅ Rekognition — connected
✅ Textract — connected
✅ Bedrock Claude 4 — connected
✅ Bedrock Titan — connected
```

### 5. Start Backend

```bash
uvicorn main:app --reload
```

### 6. Install & Start Frontend

```bash
cd frontend/memorylens-ui
npm install
npm start
```

Frontend launches at `http://localhost:3000`

---

## Usage

1. **Index a folder** — Click the "📁 Index Folder" button → Enter the full path to your files folder
2. **Face Search** — Switch to Face Search → Upload a photo → Find every other photo of that person
3. **Doc Search** — Switch to Document Search → Type what you remember writing → Find the exact document

---

## Privacy

> **Core principle:** AWS services act as a stateless inference engine.  
> Files are **never stored on AWS**. All indexes (FAISS, SQLite) live locally on your machine.

- Photos are sent to Rekognition only for face feature extraction — the image is discarded after processing
- Documents are sent to Textract/Bedrock only for text extraction and embedding — never stored
- Your FAISS vector index and SQLite metadata database stay on your local disk

---

## Architecture

```
┌─────────────────────────────┐
│        React Frontend       │  ← localhost:3000
│  (Face Upload / Doc Search) │
└─────────────┬───────────────┘
              │ HTTP (axios)
┌─────────────▼───────────────┐
│       FastAPI Backend       │  ← localhost:8000
│         main.py             │
├──────────┬──────────────────┤
│ Face     │ Document         │
│ Pipeline │ Pipeline         │
├──────────┼──────────────────┤
│ Rekog-   │ Textract → Titan │
│ nition   │ → FAISS + SQLite │
│          │ → Claude (parse) │
└──────────┴──────────────────┘
     ▲              ▲
     │              │
  AWS Cloud     AWS Cloud
  (stateless)   (stateless)

  Local Storage:
  ├── docs.db      (SQLite metadata)
  └── docs.index   (FAISS vectors)
```

---

## Team

Built for **AWS Hackathon — Generative AI on AWS**

*MemoryLens — Stop remembering file names. Start remembering faces and thoughts.*
