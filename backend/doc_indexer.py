"""Document Indexer — Extract text, embed, and index documents."""
import os
import json
import sqlite3
import logging
from datetime import datetime

import fitz  # PyMuPDF
import docx
import faiss
import numpy as np
import boto3
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class DocIndexer:
    """Indexes documents using Textract (OCR), Titan Embeddings (vectors),
    FAISS (similarity search), and SQLite (metadata + keyword search)."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".tiff"}
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff"}

    def __init__(self):
        # Bedrock client (for Titan Embeddings)
        self.bedrock = boto3.client(
            "bedrock-runtime",
            region_name=os.getenv("BEDROCK_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("BEDROCK_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("BEDROCK_SECRET_KEY"),
        )

        # Textract client (for OCR)
        self.textract = boto3.client(
            "textract",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

        # FAISS index — 512 dimensions for Titan V2
        self.index = faiss.IndexFlatL2(512)

        # SQLite — local metadata store
        self.db = sqlite3.connect("docs.db", check_same_thread=False)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE,
                file_type TEXT,
                text_snippet TEXT,
                full_text TEXT,
                faiss_id INTEGER,
                indexed_at TEXT
            )
        """)
        self.db.commit()

        self.faiss_id_counter = 0

    # ── Text Extraction ──────────────────────────────────────

    def extract_text_native(self, file_path: str) -> str:
        """Extract text using native libraries (PyMuPDF, python-docx)."""
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == ".pdf":
                doc = fitz.open(file_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                return text

            elif ext == ".docx":
                doc = docx.Document(file_path)
                return "\n".join(p.text for p in doc.paragraphs)

            elif ext == ".txt":
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()

            else:
                return ""
        except Exception as e:
            logger.error(f"Native extraction failed for {file_path}: {e}")
            return ""

    def is_scanned(self, file_path: str, native_text: str) -> bool:
        """Determine if a file needs OCR via Textract."""
        ext = os.path.splitext(file_path)[1].lower()

        # Images always need OCR
        if ext in self.IMAGE_EXTENSIONS:
            return True

        # PDFs with very little native text are likely scanned
        if ext == ".pdf" and len(native_text.strip()) < 50:
            return True

        return False

    def extract_text_ocr(self, file_path: str) -> str:
        """Extract text using AWS Textract OCR."""
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            # Textract has a 5MB limit for synchronous operations
            if len(file_bytes) > 5 * 1024 * 1024:
                logger.warning(f"File too large for Textract (>5MB): {file_path}")
                return ""

            response = self.textract.detect_document_text(
                Document={"Bytes": file_bytes}
            )

            lines = [
                block["Text"]
                for block in response.get("Blocks", [])
                if block["BlockType"] == "LINE"
            ]

            return " ".join(lines)

        except Exception as e:
            logger.error(f"Textract OCR failed for {file_path}: {e}")
            return ""

    # ── Embedding ────────────────────────────────────────────

    def get_embedding(self, text: str) -> np.ndarray:
        """Convert text to a 512-dim vector using Titan Embeddings V2."""
        # Truncate to 8000 chars (Titan input limit)
        truncated = text[:8000]

        response = self.bedrock.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps({
                "inputText": truncated,
                "dimensions": 512,
            }),
        )

        result = json.loads(response["body"].read())
        return np.array(result["embedding"], dtype=np.float32)

    # ── Indexing ─────────────────────────────────────────────

    def index_file(self, file_path: str) -> bool:
        """Index a single file into FAISS + SQLite.

        Returns:
            True if indexed, False if skipped or failed.
        """
        # Skip if already indexed
        cursor = self.db.execute(
            "SELECT id FROM docs WHERE file_path = ?", (file_path,)
        )
        if cursor.fetchone():
            logger.info(f"Already indexed: {file_path}")
            return False

        # Extract text
        native_text = self.extract_text_native(file_path)

        if self.is_scanned(file_path, native_text):
            text = self.extract_text_ocr(file_path)
        else:
            text = native_text

        if not text.strip():
            logger.info(f"No text extracted from {file_path}")
            return False

        # Get embedding and add to FAISS
        embedding = self.get_embedding(text)
        embedding_2d = embedding.reshape(1, -1)
        self.index.add(embedding_2d)

        # Store metadata in SQLite
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        snippet = text[:500]

        self.db.execute(
            """INSERT INTO docs (file_path, file_type, text_snippet, full_text, faiss_id, indexed_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (file_path, ext, snippet, text, self.faiss_id_counter, datetime.now().isoformat()),
        )
        self.db.commit()

        self.faiss_id_counter += 1
        logger.info(f"Indexed: {file_path}")
        return True

    def index_folder(self, folder_path: str) -> dict:
        """Walk folder recursively and index all supported files.

        Returns:
            {"indexed": int, "skipped": int, "errors": int}
        """
        indexed = 0
        skipped = 0
        errors = 0

        for root, _, files in os.walk(folder_path):
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in self.SUPPORTED_EXTENSIONS:
                    continue

                file_path = os.path.join(root, filename)
                try:
                    if self.index_file(file_path):
                        indexed += 1
                    else:
                        skipped += 1
                except Exception as e:
                    logger.error(f"Error indexing {file_path}: {e}")
                    errors += 1

        return {"indexed": indexed, "skipped": skipped, "errors": errors}

    # ── Persistence ──────────────────────────────────────────

    def save_index(self):
        """Save FAISS index to disk."""
        faiss.write_index(self.index, "docs.index")
        logger.info("FAISS index saved to docs.index")

    def load_index(self):
        """Load FAISS index from disk if it exists."""
        if os.path.exists("docs.index"):
            self.index = faiss.read_index("docs.index")
            # Sync counter from SQLite
            cursor = self.db.execute("SELECT COUNT(*) FROM docs")
            self.faiss_id_counter = cursor.fetchone()[0]
            logger.info(f"FAISS index loaded — {self.faiss_id_counter} docs")
