"""Face Indexer — Parallel indexing with ThreadPoolExecutor + auto-resize."""
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from threading import Lock

import boto3
from PIL import Image
from dotenv import load_dotenv

# HEIC support (Apple photos) — optional dependency
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:
    HEIC_SUPPORTED = False

load_dotenv()
logger = logging.getLogger(__name__)

# Max image size for Rekognition (5MB)
MAX_IMAGE_BYTES = 5 * 1024 * 1024


class FaceIndexer:
    """Indexes photos into an AWS Rekognition face collection using parallel processing."""

    # All image formats we can handle (convert to JPEG for Rekognition)
    SUPPORTED_EXTENSIONS = {
        ".jpg", ".jpeg", ".png",          # Native Rekognition support
        ".heic", ".heif",                   # Apple photos (needs pillow-heif)
        ".webp", ".bmp", ".tiff", ".gif",  # Common formats (auto-converted)
    }
    # Formats Rekognition accepts directly
    NATIVE_FORMATS = {".jpg", ".jpeg", ".png"}

    def __init__(self):
        self.collection_id = os.getenv("REKOGNITION_COLLECTION_ID", "memorylens")
        self._region = os.getenv("AWS_REGION", "us-east-1")
        self._access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self._secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        # Main client for single operations
        self.client = boto3.client(
            "rekognition",
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            region_name=self._region,
        )

    def _create_client(self):
        """Create a new Rekognition client (thread-safe — one per thread)."""
        return boto3.client(
            "rekognition",
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            region_name=self._region,
        )

    @staticmethod
    def _resize_image(image_bytes: bytes) -> bytes:
        """Resize image to fit under 5MB while preserving quality for face detection."""
        img = Image.open(BytesIO(image_bytes))

        # Convert RGBA/palette to RGB
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        quality = 85
        while True:
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=quality)
            result = buffer.getvalue()

            if len(result) <= MAX_IMAGE_BYTES:
                return result

            # Reduce quality
            quality -= 10
            if quality < 30:
                # Still too big — scale down dimensions
                w, h = img.size
                img = img.resize((int(w * 0.7), int(h * 0.7)), Image.LANCZOS)
                quality = 85

    def _prepare_image(self, file_path: str) -> bytes:
        """Read image, convert format if needed, and resize if >5MB."""
        ext = os.path.splitext(file_path)[1].lower()

        # HEIC check
        if ext in (".heic", ".heif") and not HEIC_SUPPORTED:
            logger.warning(f"Skipping {file_path} — install pillow-heif for HEIC support")
            raise ValueError("HEIC not supported — pip install pillow-heif")

        # If format is not natively supported by Rekognition, convert to JPEG
        if ext not in self.NATIVE_FORMATS:
            logger.info(f"Converting {ext} → JPEG: {file_path}")
            img = Image.open(file_path)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            image_bytes = buffer.getvalue()
        else:
            with open(file_path, "rb") as f:
                image_bytes = f.read()

        # Resize if still too large
        if len(image_bytes) > MAX_IMAGE_BYTES:
            logger.info(f"Resizing {file_path} ({len(image_bytes) / 1024 / 1024:.1f}MB)")
            image_bytes = self._resize_image(image_bytes)

        return image_bytes

    def index_photo(self, file_path: str, client=None) -> bool:
        """Index a single photo into the Rekognition collection.

        Returns:
            True if at least 1 face was indexed, False if no faces found.
        """
        rek = client or self.client

        try:
            image_bytes = self._prepare_image(file_path)

            # Use Base64URL encoding so we don't lose the original path due to regex constraints
            import base64
            # Strip padding '=' as some AWS services strict-validate even base64
            external_id = base64.urlsafe_b64encode(file_path.encode('utf-8')).decode('utf-8').rstrip('=')
            external_id = external_id[-255:] # Hard limit for Rekognition

            response = rek.index_faces(
                CollectionId=self.collection_id,
                Image={"Bytes": image_bytes},
                ExternalImageId=external_id,
                DetectionAttributes=[],
            )

            faces_indexed = len(response.get("FaceRecords", []))
            return faces_indexed > 0

        except Exception as e:
            logger.error(f"Error indexing {file_path}: {e}")
            return False

    def _index_single(self, file_path: str, client, progress_callback, lock, counters):
        """Worker function for parallel indexing."""
        try:
            if self.index_photo(file_path, client=client):
                with lock:
                    counters["indexed"] += 1
            else:
                with lock:
                    counters["skipped"] += 1
        except Exception:
            with lock:
                counters["errors"] += 1

        # Report progress
        with lock:
            counters["processed"] += 1
            if progress_callback:
                progress_callback(counters["processed"], counters["total"])

    def index_folder(
        self,
        folder_path: str,
        max_workers: int = 10,
        progress_callback=None,
    ) -> dict:
        """Walk folder and index all photos in parallel.

        Args:
            folder_path: Path to folder containing photos.
            max_workers: Number of parallel threads (default 10).
            progress_callback: Optional callable(processed, total) for progress updates.

        Returns:
            {"indexed": int, "skipped": int, "errors": int, "total": int}
        """
        # Collect all image files first
        image_files = []
        for root, _, files in os.walk(folder_path):
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    image_files.append(os.path.join(root, filename))

        total = len(image_files)
        if total == 0:
            return {"indexed": 0, "skipped": 0, "errors": 0, "total": 0}

        counters = {"indexed": 0, "skipped": 0, "errors": 0, "processed": 0, "total": total}
        lock = Lock()

        # Report initial progress
        if progress_callback:
            progress_callback(0, total)

        # Parallel indexing — each thread gets its own Rekognition client
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            # Create one client per worker
            clients = [self._create_client() for _ in range(max_workers)]

            for i, file_path in enumerate(image_files):
                client = clients[i % max_workers]
                future = executor.submit(
                    self._index_single,
                    file_path,
                    client,
                    progress_callback,
                    lock,
                    counters,
                )
                futures.append(future)

            # Wait for all to complete
            for future in as_completed(futures):
                pass  # Errors handled inside _index_single

        return {
            "indexed": counters["indexed"],
            "skipped": counters["skipped"],
            "errors": counters["errors"],
            "total": total,
        }
