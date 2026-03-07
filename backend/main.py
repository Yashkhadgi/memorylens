"""MemoryLens API — FastAPI application with all routes."""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from face_indexer import FaceIndexer
from face_search import FaceSearcher
from doc_indexer import DocIndexer
from doc_search import DocSearcher

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Globals ──────────────────────────────────────────────
face_indexer: FaceIndexer | None = None
face_searcher: FaceSearcher | None = None
doc_indexer: DocIndexer | None = None
doc_searcher: DocSearcher | None = None


# ── Request Models ───────────────────────────────────────
class IndexRequest(BaseModel):
    folder_path: str


# ── Lifespan ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load FAISS index on startup, save on shutdown."""
    global face_indexer, face_searcher, doc_indexer, doc_searcher

    face_indexer = FaceIndexer()
    face_searcher = FaceSearcher()
    doc_indexer = DocIndexer()
    doc_indexer.load_index()
    doc_searcher = DocSearcher(doc_indexer)

    logger.info("MemoryLens API started — all services initialized")
    yield

    # Cleanup: save FAISS index on shutdown
    if doc_indexer:
        doc_indexer.save_index()
    logger.info("MemoryLens API stopped — index saved")


app = FastAPI(title="MemoryLens API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Check ─────────────────────────────────────────
@app.get("/api/health")
def health_check():
    return {"status": "ok"}


# ── Index Folder ─────────────────────────────────────────
@app.post("/api/index")
async def index_folder(request: IndexRequest):
    """Index all photos and documents in the given folder."""
    folder = request.folder_path

    if not os.path.isdir(folder):
        raise HTTPException(status_code=400, detail=f"Folder not found: {folder}")

    # Index photos
    photo_result = face_indexer.index_folder(folder)

    # Index documents
    doc_result = doc_indexer.index_folder(folder)
    doc_indexer.save_index()

    return {
        "status": "indexed",
        "photos_indexed": photo_result["indexed"],
        "docs_indexed": doc_result["indexed"],
    }


# ── Face Search ──────────────────────────────────────────
@app.post("/api/search/faces")
async def search_faces(file: UploadFile = File(...)):
    """Upload a reference photo to find matching faces."""
    image_bytes = await file.read()
    results = face_searcher.search_by_face(image_bytes)
    return {"results": results}


# ── Document Search ──────────────────────────────────────
@app.get("/api/search/docs")
async def search_docs(query: str = Query(...)):
    """Search indexed documents by text query."""
    if doc_indexer.index.ntotal == 0:
        raise HTTPException(
            status_code=503,
            detail="Index not built yet. Please index a folder first.",
        )

    results = doc_searcher.search(query)
    return {"results": results}