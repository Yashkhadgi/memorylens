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

    def get_total_faces(self) -> int:
        """Returns the total number of faces indexed in the collection."""
        try:
            response = self.client.describe_collection(CollectionId=self.collection_id)
            return response.get("FaceCount", 0)
        except Exception as e:
            logger.error(f"Error getting collection face count: {e}")
            return 0

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

            import base64
            results = []
            for match in response.get("FaceMatches", []):
                face = match["Face"]
                ext_id = face.get("ExternalImageId", "")
                
                # Decode Base64URL back to the exact original file path
                try:
                    padding = '=' * (4 - (len(ext_id) % 4))
                    file_path = base64.urlsafe_b64decode(ext_id + padding).decode('utf-8')
                except Exception:
                    file_path = ext_id # Fallback if it wasn't base64 encoded

                results.append({
                    "file_path": file_path,
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
