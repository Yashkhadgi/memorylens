# MemoryLens — Backend

FastAPI backend for the MemoryLens face search pipeline.

---

## Setup

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

## Environment Variables

Copy `.env.example` → `.env` and fill in your credentials:

```env
AWS_ACCESS_KEY_ID=...          # For Rekognition
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
REKOGNITION_COLLECTION_ID=memorylens
BEDROCK_ACCESS_KEY=...         # For Titan/Nova (doc pipeline)
BEDROCK_SECRET_KEY=...
BEDROCK_REGION=us-east-1
```

## First-Time Setup

```bash
# 1. Create Rekognition face collection (one-time)
python create_collection.py

# 2. Verify all AWS connections
python test_aws.py
```

## Run the Server

```bash
uvicorn main:app --reload
```

Server starts at `http://localhost:8000`

---

## API Routes

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/api/health` | Health check → `{"status": "ok"}` |
| `POST` | `/api/index` | Index photos in a folder (runs in background) |
| `GET` | `/api/index/progress` | Poll indexing progress (processed/total) |
| `POST` | `/api/search/faces` | Upload a photo → find matching faces |
| `GET` | `/api/search/docs` | Doc search (stub — teammate's pipeline) |

### Index a Folder

```bash
curl -X POST http://localhost:8000/api/index \
  -H "Content-Type: application/json" \
  -d '{"folder_path": "C:/Users/you/Photos"}'
```

### Check Progress

```bash
curl http://localhost:8000/api/index/progress
# {"is_running": true, "processed": 42, "total": 100, ...}
```

### Face Search

```bash
curl -X POST http://localhost:8000/api/search/faces \
  -F "file=@my_photo.jpg"
```

---

## Supported Image Formats

| Format | Handling |
|--------|----------|
| `.jpg` `.jpeg` `.png` | Sent directly to Rekognition |
| `.heic` `.heif` | Auto-converted to JPEG (needs `pillow-heif`) |
| `.webp` `.bmp` `.tiff` `.gif` | Auto-converted to JPEG |

> Images > 5MB are automatically resized before upload.

---

## File Structure

```
backend/
├── main.py               # FastAPI app — routes + background indexing
├── face_indexer.py        # Parallel face indexing (ThreadPoolExecutor)
├── face_search.py         # Rekognition face search
├── create_collection.py   # One-time Rekognition collection setup
├── test_aws.py            # Verify AWS connections
├── requirements.txt       # Python dependencies
├── .env.example           # Credential template
└── .env                   # Your real credentials (git-ignored)
```

---

## Key Technical Details

- **Parallel indexing:** 10 concurrent threads via `ThreadPoolExecutor`
- **Progress tracking:** Background thread + shared state, polled by frontend every 500ms
- **Image limit:** Rekognition accepts max 5MB — larger images auto-resized with Pillow
- **ExternalImageId:** File path stored as face ID in Rekognition (truncated to 255 chars)
- **CORS:** Configured for `http://localhost:3000` (React frontend)
