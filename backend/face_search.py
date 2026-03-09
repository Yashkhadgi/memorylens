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
        If the image contains multiple faces, returns matches for ALL of them.

        Args:
            image_bytes: Raw bytes of the reference photo.
            threshold: Minimum similarity percentage (default 80%).

        Returns:
            List of groups: [{"person_id": int, "faces": [{"file_path", "similarity", "face_id"}]}]
        """
        import base64
        try:
            # First, detect faces in the uploaded image to get bounding boxes
            detect_res = self.client.detect_faces(Image={"Bytes": image_bytes})
            detected_faces = detect_res.get("FaceDetails", [])
            
            if not detected_faces:
                logger.info("No face detected in the uploaded image")
                return []
                
            groups = []
            
            # For each detected face, search the collection
            # Rekognition search_faces_by_image actually searches for the *largest* face by default if we don't crop.
            # However, we can use detect_faces + crop, OR just rely on IndexFaces to index everything and SearchFaces.
            # But since we just have an image, we can crop the image for each bounding box and search.
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
            
            for i, face_detail in enumerate(detected_faces):
                box = face_detail["BoundingBox"]
                # Calculate pixel coordinates
                left = int(box["Left"] * width)
                top = int(box["Top"] * height)
                w = int(box["Width"] * width)
                h = int(box["Height"] * height)
                
                # Add a small margin
                margin_x = int(w * 0.1)
                margin_y = int(h * 0.1)
                
                crop_left = max(0, left - margin_x)
                crop_top = max(0, top - margin_y)
                crop_right = min(width, left + w + margin_x)
                crop_bottom = min(height, top + h + margin_y)
                
                # Crop the face
                face_img = img.crop((crop_left, crop_top, crop_right, crop_bottom))
                
                # Convert back to bytes
                buf = io.BytesIO()
                face_img.save(buf, format=img.format or 'JPEG')
                face_bytes = buf.getvalue()
                
                try:
                    search_res = self.client.search_faces_by_image(
                        CollectionId=self.collection_id,
                        Image={"Bytes": face_bytes},
                        FaceMatchThreshold=threshold,
                        MaxFaces=50,
                    )
                    
                    matches = []
                    for match in search_res.get("FaceMatches", []):
                        face = match["Face"]
                        ext_id = face.get("ExternalImageId", "")
                        
                        try:
                            padding = '=' * (4 - (len(ext_id) % 4))
                            file_path = base64.urlsafe_b64decode(ext_id + padding).decode('utf-8')
                        except Exception:
                            file_path = ext_id
                            
                        matches.append({
                            "file_path": file_path,
                            "similarity": round(match["Similarity"], 2),
                            "face_id": face["FaceId"],
                        })
                        
                    if matches:
                        # Sort by similarity
                        matches.sort(key=lambda x: x["similarity"], reverse=True)
                        groups.append({
                            "person_id": i,
                            "count": len(matches),
                            "faces": matches
                        })
                except self.client.exceptions.InvalidParameterException:
                    continue  # Face crop wasn't good enough for search
                    
            return groups

        except Exception as e:
            logger.error(f"Face search error: {e}")
            raise

    def group_faces(self, threshold: float = 80.0) -> list[dict]:
        """Group all indexed faces by person.

        Uses Rekognition search_faces (face-to-face) to cluster similar faces.

        Returns:
            List of groups: [{"person_id": int, "faces": [{"file_path", "face_id"}]}]
        """
        import base64

        # Step 1: List all faces in the collection
        all_faces = []
        try:
            paginator_params = {"CollectionId": self.collection_id, "MaxResults": 100}
            while True:
                response = self.client.list_faces(**paginator_params)
                all_faces.extend(response.get("Faces", []))
                next_token = response.get("NextToken")
                if not next_token:
                    break
                paginator_params["NextToken"] = next_token
        except Exception as e:
            logger.error(f"Error listing faces: {e}")
            return []

        if not all_faces:
            return []

        # Step 2: Build a map of face_id -> file_path
        face_map = {}
        for face in all_faces:
            face_id = face["FaceId"]
            ext_id = face.get("ExternalImageId", "")
            try:
                padding = '=' * (4 - (len(ext_id) % 4))
                file_path = base64.urlsafe_b64decode(ext_id + padding).decode('utf-8')
            except Exception:
                file_path = ext_id
            face_map[face_id] = file_path

        # Step 3: Cluster faces by person using search_faces
        visited = set()
        groups = []
        person_id = 0

        for face_id in face_map:
            if face_id in visited:
                continue

            # Search for faces similar to this one
            try:
                response = self.client.search_faces(
                    CollectionId=self.collection_id,
                    FaceId=face_id,
                    FaceMatchThreshold=threshold,
                    MaxFaces=100,
                )
            except Exception as e:
                logger.warning(f"search_faces failed for {face_id}: {e}")
                visited.add(face_id)
                continue

            # Build group: the seed face + all matches
            group_faces = [{"face_id": face_id, "file_path": face_map[face_id]}]
            visited.add(face_id)

            for match in response.get("FaceMatches", []):
                matched_id = match["Face"]["FaceId"]
                if matched_id not in visited and matched_id in face_map:
                    group_faces.append({
                        "face_id": matched_id,
                        "file_path": face_map[matched_id],
                    })
                    visited.add(matched_id)

            groups.append({
                "person_id": person_id,
                "count": len(group_faces),
                "faces": group_faces,
            })
            person_id += 1

        # Sort groups by size (most photos first)
        groups.sort(key=lambda g: g["count"], reverse=True)
        return groups
