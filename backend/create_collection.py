"""One-time script: Create the Rekognition face collection."""
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

client = boto3.client(
    "rekognition",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

collection_id = os.getenv("REKOGNITION_COLLECTION_ID", "memorylens")

try:
    client.create_collection(CollectionId=collection_id)
    print(f"✅ Collection '{collection_id}' created")
except client.exceptions.ResourceAlreadyExistsException:
    print(f"ℹ️ Collection '{collection_id}' already exists")
except Exception as e:
    print(f"❌ Failed: {e}")