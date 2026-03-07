"""Face Indexer — Index faces into Rekognition collection."""
import os
import logging
import boto3
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class FaceIndexer:
    """Indexes photos into an AWS Rekognition face collection."""

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

    def __init__(self):
        self.client = boto3.client(
            "rekognition",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "us-east-1"),
        )
        self.collection_id = os.getenv("REKOGNITION_COLLECTION_ID", "memorylens")

    def index_photo(self, file_path: str) -> bool:
        """Index a single photo into the Rekognition collection.

        Args:
            file_path: Absolute path to the image file.

        Returns:
            True if at least 1 face was indexed, False if no faces found.
        """
        try:
            with open(file_path, "rb") as f:
                image_bytes = f.read()

            response = self.client.index_faces(
                CollectionId=self.collection_id,
                Image={"Bytes": image_bytes},
                ExternalImageId=file_path,
                DetectionAttributes=[],
            )

            faces_indexed = len(response.get("FaceRecords", []))
            if faces_indexed > 0:
                logger.info(f"Indexed {faces_indexed} face(s) from {file_path}")
                return True
            else:
                logger.info(f"No faces found in {file_path}")
                return False

        except Exception as e:
            logger.error(f"Error indexing {file_path}: {e}")
            raise

    def index_folder(self, folder_path: str) -> dict:
        """Walk folder recursively and index all supported images.

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
                    if self.index_photo(file_path):
                        indexed += 1
                    else:
                        skipped += 1
                except Exception as e:
                    logger.error(f"Failed to index {file_path}: {e}")
                    errors += 1

        return {"indexed": indexed, "skipped": skipped, "errors": errors}
