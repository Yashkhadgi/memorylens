import os
import json
from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="MemoryLens API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── Health Check ──────────────────────────────────────────
@app.get("/")
def home():
    return {
        "status": "MemoryLens API is running ✅",
        "version": "1.0.0",
        "message": "All systems ready!"
    }

# ── Face Search ───────────────────────────────────────────
@app.post("/api/search/faces")
async def face_search(file: UploadFile = File(...)):
    # TODO: Member A will complete this
    return {
        "success": True,
        "count": 0,
        "results": [],
        "message": "Face pipeline coming soon — Member A is building it!"
    }

# ── Document Search ───────────────────────────────────────
@app.get("/api/search/docs")
async def doc_search(q: str = Query(...)):
    # TODO: Member B will complete this
    return {
        "success": True,
        "query": q,
        "count": 0,
        "results": [],
        "message": "Doc pipeline coming soon — Member B is building it!"
    }

# ── Index Folder ──────────────────────────────────────────
@app.post("/api/index")
async def index_folder():
    # TODO: Wire up after A and B are done
    return {
        "success": True,
        "message": "Indexing pipeline coming soon!"
    }

# ── Stats ─────────────────────────────────────────────────
@app.get("/api/stats")
def get_stats():
    return {
        "status": "running",
        "documents_indexed": 0,
        "faces_indexed": 0
    }