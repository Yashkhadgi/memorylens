import os
import json
import platform
import subprocess
import doc_indexer
from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from doc_search import search_documents

load_dotenv()

app = FastAPI(title="MemoryLens API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── Startup ───────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    print("🚀 MemoryLens API starting...")
    doc_indexer.load_index()
    print("✅ API ready!")

# ── Health Check ──────────────────────────────────────────
@app.get("/")
def home():
    return {
        "status": "MemoryLens API is running ✅",
        "version": "1.0.0",
        "docs_indexed": len(doc_indexer.doc_meta),
        "faces_indexed": "pending Member A"
    }

# ── Face Search ───────────────────────────────────────────
@app.post("/api/search/faces")
async def face_search(file: UploadFile = File(...)):
    # TODO: Wire up after Member A is done
    return {
        "success": False,
        "message": "Face pipeline — Member A is building it!",
        "results": []
    }

# ── Document Search ───────────────────────────────────────
@app.get("/api/search/docs")
async def doc_search(q: str = Query(...)):
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
            "results": results
        }
    except Exception as e:
        return {"success": False, "error": str(e), "results": []}

# ── Index Folder ──────────────────────────────────────────
@app.post("/api/index")
async def index_folder():
    try:
        base_path = os.path.join(os.path.dirname(__file__), '..', 'sample_data')
        docs_path = os.path.join(base_path, 'docs')

        if os.path.exists(docs_path):
            result = doc_indexer.index_docs_folder(docs_path)
            return {"success": True, "docs": result}
        else:
            return {"success": False, "error": "docs folder not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ── Stats ─────────────────────────────────────────────────
@app.get("/api/stats")
def get_stats():
    return {
        "documents_indexed": len(doc_indexer.doc_meta),
        "faiss_total": doc_indexer.doc_index.ntotal
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