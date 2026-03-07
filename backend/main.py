"""MemoryLens API — FastAPI application.
Face pipeline fully implemented with parallel indexing + progress tracking.
Doc pipeline routes are stubbed — will be merged from teammate's branch.
"""
import os
import sys
import subprocess
import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from face_indexer import FaceIndexer
from face_search import FaceSearcher

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Globals ──────────────────────────────────────────────
face_indexer = None
face_searcher = None

# Indexing progress state (shared between background thread and API)
indexing_state = {
    "is_running": False,
    "processed": 0,
    "total": 0,
    "indexed": 0,
    "skipped": 0,
    "errors": 0,
    "done": False,
    "message": "",
}
state_lock = threading.Lock()


# ── Request Models ───────────────────────────────────────
class IndexRequest(BaseModel):
    folder_path: str


# ── Lifespan ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    global face_indexer, face_searcher

    face_indexer = FaceIndexer()
    face_searcher = FaceSearcher()

    logger.info("MemoryLens API started — face pipeline ready")
    yield
    logger.info("MemoryLens API stopped")


app = FastAPI(title="MemoryLens API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Progress Callback ────────────────────────────────────
def on_progress(processed: int, total: int):
    """Called by face_indexer from worker threads to report progress."""
    with state_lock:
        indexing_state["processed"] = processed
        indexing_state["total"] = total


def run_indexing(folder_path: str):
    """Background thread: runs the actual indexing."""
    global indexing_state
    try:
        result = face_indexer.index_folder(
            folder_path,
            max_workers=10,
            progress_callback=on_progress,
        )

        with state_lock:
            indexing_state["indexed"] = result["indexed"]
            indexing_state["skipped"] = result["skipped"]
            indexing_state["errors"] = result["errors"]
            indexing_state["done"] = True
            indexing_state["is_running"] = False
            indexing_state["message"] = (
                f"Done! Indexed {result['indexed']} photos "
                f"({result['skipped']} skipped, {result['errors']} errors)"
            )
        logger.info(f"Indexing complete: {result}")

    except Exception as e:
        with state_lock:
            indexing_state["done"] = True
            indexing_state["is_running"] = False
            indexing_state["message"] = f"Error: {str(e)}"
        logger.error(f"Indexing failed: {e}")


# ── Health Check ─────────────────────────────────────────
@app.get("/api/health")
def health_check():
    return {"status": "ok"}


# ── Select Folder Dialog ─────────────────────────────────
@app.get("/api/select-folder")
def select_folder():
    """Opens a native OS folder selection dialog via a fresh process."""
    script = (
        "import tkinter as tk, tkinter.filedialog as fd;\n"
        "root = tk.Tk()\n"
        "root.withdraw()\n"
        "root.attributes('-topmost', True)\n"
        "print(fd.askdirectory(title='Select Folder to Index'))\n"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, text=True
        )
        return {"folder_path": result.stdout.strip()}
    except Exception as e:
        logger.error(f"Failed to open folder dialog: {e}")
        return {"folder_path": ""}


# ── Index Folder (starts background task) ────────────────
@app.post("/api/index")
async def index_folder(request: IndexRequest):
    """Start indexing photos in the given folder (runs in background)."""
    folder = request.folder_path

    if not os.path.isdir(folder):
        raise HTTPException(status_code=400, detail=f"Folder not found: {folder}")

    with state_lock:
        if indexing_state["is_running"]:
            raise HTTPException(status_code=409, detail="Indexing already in progress")

        # Reset state
        indexing_state.update({
            "is_running": True,
            "processed": 0,
            "total": 0,
            "indexed": 0,
            "skipped": 0,
            "errors": 0,
            "done": False,
            "message": "Scanning folder...",
        })

    # Start background thread
    thread = threading.Thread(target=run_indexing, args=(folder,), daemon=True)
    thread.start()

    return {"status": "indexing_started", "message": "Indexing started in background"}


# ── Index Progress ───────────────────────────────────────
@app.get("/api/index/progress")
def get_index_progress():
    """Get the current indexing progress."""
    with state_lock:
        return {
            "is_running": indexing_state["is_running"],
            "processed": indexing_state["processed"],
            "total": indexing_state["total"],
            "indexed": indexing_state["indexed"],
            "skipped": indexing_state["skipped"],
            "errors": indexing_state["errors"],
            "done": indexing_state["done"],
            "message": indexing_state["message"],
        }


# ── Face Search ──────────────────────────────────────────
@app.post("/api/search/faces")
async def search_faces(file: UploadFile = File(...)):
    """Upload a reference photo to find matching faces."""
    image_bytes = await file.read()
    results = face_searcher.search_by_face(image_bytes)
    total_indexed = face_searcher.get_total_faces()
    
    return {
        "results": results,
        "stats": {
            "total_indexed": total_indexed,
            "found": len(results),
            "not_match": max(0, total_indexed - len(results))
        }
    }


# ── Document Search (stub — teammate will implement) ─────
@app.get("/api/search/docs")
async def search_docs(query: str = Query(...)):
    """Stub for doc search — will be merged from teammate's branch."""
    return {
        "results": [],
        "message": "Doc search not yet available. Coming soon from doc pipeline team.",
    }