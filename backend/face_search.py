"""Face Search — Search photos by face using Rekognition."""
import os
import logging
import boto3
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class FaceSearcher:
    """Searches for matching faces in the Rekognition collection."""

    def __init__(self):
        self.client = boto3.client(
            "rekognition",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "us-east-1"),
        )
        self.collection_id = os.getenv("REKOGNITION_COLLECTION_ID", "memorylens")

    def search_by_face(
        self, image_bytes: bytes, threshold: float = 80.0
    ) -> list[dict]:
        """Search the collection for faces matching the given image.

        Args:
            image_bytes: Raw bytes of the reference photo.
            threshold: Minimum similarity percentage (default 80%).

        Returns:
            List of dicts: [{"file_path", "similarity", "face_id"}]
            sorted by similarity descending.
        """
        try:
            response = self.client.search_faces_by_image(
                CollectionId=self.collection_id,
                Image={"Bytes": image_bytes},
                FaceMatchThreshold=threshold,
                MaxFaces=50,
            )

            results = []
            for match in response.get("FaceMatches", []):
                face = match["Face"]
                results.append({
                    "file_path": face["ExternalImageId"],
                    "similarity": round(match["Similarity"], 2),
                    "face_id": face["FaceId"],
                })

            # Sort by similarity descending
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results

        except self.client.exceptions.InvalidParameterException:
            # No face detected in the query image
            logger.info("No face detected in the uploaded image")
            return []
        except Exception as e:
            logger.error(f"Face search error: {e}")
            raise
