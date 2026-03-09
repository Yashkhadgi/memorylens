"""MemoryLens API — FastAPI application.
Unified pipeline with both Face and Document indexing and search.
"""
import os
import sys
import subprocess
import logging
import threading
import platform
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.responses import FileResponse
<<<<<<< HEAD
from fastapi.staticfiles import StaticFiles
=======
>>>>>>> main
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

import doc_indexer
from doc_search import search_documents

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
    mode: str = "both"  # 'doc', 'face', or 'both'


# ── Lifespan ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup. Resets face collection for a clean session."""
    global face_indexer, face_searcher

    print("🚀 MemoryLens API starting...")
    doc_indexer.load_index()

    face_indexer = FaceIndexer()
    face_searcher = FaceSearcher()

    # ── Auto-reset Rekognition collection on startup ──
    # This ensures no stale face data from other machines/sessions
    collection_id = face_indexer.collection_id
    rek_client = face_indexer.client
    try:
        rek_client.delete_collection(CollectionId=collection_id)
        logger.info(f"🗑️ Deleted existing collection: {collection_id}")
    except rek_client.exceptions.ResourceNotFoundException:
        logger.info(f"No existing collection to delete: {collection_id}")
    except Exception as e:
        logger.warning(f"Could not delete collection: {e}")

    try:
        rek_client.create_collection(CollectionId=collection_id)
        logger.info(f"✅ Created fresh collection: {collection_id}")
    except rek_client.exceptions.ResourceAlreadyExistsException:
        logger.info(f"Collection already exists: {collection_id}")
    except Exception as e:
        logger.error(f"Failed to create collection: {e}")

    logger.info("✅ MemoryLens API ready — both pipelines operational!")
    yield
    logger.info("MemoryLens API stopped")


app = FastAPI(title="MemoryLens API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Progress Callback ────────────────────────────────────
def on_progress(processed: int, total: int):
    """Called by face_indexer from worker threads to report progress."""
    with state_lock:
        indexing_state["processed"] = processed
        indexing_state["total"] = total


def run_indexing(folder_path: str, mode: str = "both"):
    """Background thread: runs the actual indexing based on mode."""
    global indexing_state
    try:
        doc_count = 0
        face_result = {"indexed": 0, "skipped": 0, "errors": 0}

        # Index Documents (only for 'doc' or 'both' mode)
        if mode in ('doc', 'both') and os.path.exists(folder_path):
            logger.info(f"Indexing documents in {folder_path}...")
            result = doc_indexer.index_docs_folder(folder_path)
            doc_count = result.get("indexed", 0) if isinstance(result, dict) else result

        # Index Faces (only for 'face' or 'both' mode)
        if mode in ('face', 'both'):
            logger.info(f"Indexing faces in {folder_path}...")
            face_result = face_indexer.index_folder(
                folder_path,
                max_workers=10,
                progress_callback=on_progress,
            )

        with state_lock:
            indexing_state["indexed"] = face_result["indexed"] + doc_count
            indexing_state["skipped"] = face_result["skipped"]
            indexing_state["errors"] = face_result["errors"]
            indexing_state["done"] = True
            indexing_state["is_running"] = False

            if mode == 'doc':
                indexing_state["message"] = f"Done! Indexed {doc_count} documents"
            elif mode == 'face':
                indexing_state["message"] = (
                    f"Done! Indexed {face_result['indexed']} photos "
                    f"({face_result['skipped']} skipped, {face_result['errors']} errors)"
                )
            else:
                indexing_state["message"] = (
                    f"Done! Indexed {face_result['indexed']} photos & {doc_count} docs"
                )

        logger.info(f"Indexing complete: mode={mode}, Faces={face_result}, Docs={doc_count}")

    except Exception as e:
        with state_lock:
            indexing_state["done"] = True
            indexing_state["is_running"] = False
            indexing_state["message"] = f"Error: {str(e)}"
        logger.error(f"Indexing failed: {e}")


# ── Health Check ─────────────────────────────────────────
@app.get("/")
def home():
    return {
        "status": "MemoryLens API is running ✅",
        "version": "1.0.0",
        "docs_indexed": len(doc_indexer.doc_meta),
        "faces_indexed": face_searcher.get_total_faces() if face_searcher else 0
    }

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
async def index_folder(request: IndexRequest = None):
    """Start indexing documents and photos in the given folder (runs in background)."""
    # Fallback to sample_data/docs if no folder provided (for compatibility)
    if not request or not request.folder_path:
        base_path = os.path.join(os.path.dirname(__file__), '..', 'sample_data')
        folder = os.path.join(base_path, 'docs')
    else:
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
    index_mode = request.mode if request else "both"
    thread = threading.Thread(target=run_indexing, args=(folder,index_mode), daemon=True)
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
    results = face_searcher.search_by_face(image_bytes, threshold=95.0)
    total_indexed = face_searcher.get_total_faces()
    
    return {
        "success": True,
        "results": results,
        "stats": {
            "total_indexed": total_indexed,
            "found": len(results),
            "not_match": max(0, total_indexed - len(results))
        }
    }


# ── Face Groups (Google Photos-style) ────────────────────
@app.get("/api/faces/groups")
async def get_face_groups():
    """Get all indexed faces grouped by person."""
    try:
        groups = face_searcher.group_faces(threshold=95.0)
        return {
            "success": True,
            "total_people": len(groups),
            "groups": groups,
        }
    except Exception as e:
        logger.error(f"Face grouping error: {e}")
        return {"success": False, "error": str(e), "groups": []}


# ── Document Search ───────────────────────────────────────
@app.get("/api/search/docs")
async def search_docs(q: str = Query(...)):
    try:
        if not q.strip():
            return {"success": False, "error": "Query cannot be empty", "results": []}

        results = search_documents(
            q,
            doc_indexer.doc_index,
            doc_indexer.doc_meta
        )

        return {
            "success": True,
            "query": q,
            "count": len(results),
            "results": results,
            "message": f"Found {len(results)} matches for '{q}'"
        }
    except Exception as e:
        return {"success": False, "error": str(e), "results": []}


# ── Stats ─────────────────────────────────────────────────
@app.get("/api/stats")
def get_stats():
    return {
        "documents_indexed": len(doc_indexer.doc_meta),
        "faiss_total": doc_indexer.doc_index.ntotal if hasattr(doc_indexer.doc_index, 'ntotal') else 0,
        "faces_indexed": face_searcher.get_total_faces() if face_searcher else 0
    }

# ── Open File — Works on Mac + Windows + Linux ────────────
@app.get("/api/open-file")
def open_file(path: str):
    try:
        system = platform.system()
        if system == 'Windows':
            os.startfile(path)
        elif system == 'Darwin':  # Mac
            subprocess.run(['open', path])
        else:  # Linux
            subprocess.run(['xdg-open', path])
        return {"success": True, "message": f"Opened: {path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ── Web Search Links — Spotlight Style ────────────────────
@app.get("/api/web-search")
def web_search_links(q: str, mode: str = "doc"):
    encoded = q.replace(' ', '+')

    # Doc search links
    doc_links = [
        {"source": "Google", "icon": "🔍", "url": f"https://www.google.com/search?q={encoded}"},
        {"source": "Wikipedia", "icon": "📖", "url": f"https://en.wikipedia.org/wiki/Special:Search?search={encoded}"},
        {"source": "ChatGPT", "icon": "🤖", "url": f"https://chat.openai.com/?q={encoded}"},
        {"source": "YouTube", "icon": "🎥", "url": f"https://www.youtube.com/results?search_query={encoded}"},
        {"source": "Twitter", "icon": "🐦", "url": f"https://twitter.com/search?q={encoded}"},
    ]

    # Face search links
    face_links = [
        {"source": "Google Images", "icon": "🔍", "url": f"https://www.google.com/search?tbm=isch&q={encoded}"},
        {"source": "ChatGPT", "icon": "🤖", "url": f"https://chat.openai.com/?q={encoded}"},
        {"source": "Pinterest", "icon": "📸", "url": f"https://www.pinterest.com/search/pins/?q={encoded}"},
    ]

    return {
        "query": q,
        "mode": mode,
        "links": face_links if mode == "face" else doc_links
    }

# ── Serve Local Image ────────────────────────────────────
@app.get("/api/image")
def serve_image(path: str):
    """Serve a local image file so the frontend can display it."""
    import mimetypes
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    mime, _ = mimetypes.guess_type(path)
    if not mime or not mime.startswith("image"):
        # Try to serve anyway — browser will handle it
        mime = "application/octet-stream"
    return FileResponse(path, media_type=mime)


# ── Serve Frontend ───────────────────────────────────────
# 1. Mount the static directory for CSS/JS/Images
# Note: CRA puts assets in build/static, which we copied to backend/static
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static", "static")), name="static_assets")

# 2. Serve the index.html for the root and any other non-API routes
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # Only serve index.html if the path doesn't start with /api
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="API route not found")
    
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Frontend build not found. Run 'npm run build' first."}
