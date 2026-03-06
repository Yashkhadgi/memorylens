import boto3
import os
from dotenv import load_dotenv

load_dotenv()

rek = boto3.client(
    'rekognition',
    region_name='us-east-1',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

try:
    rek.create_collection(CollectionId='memorylens')
    print("✅ Rekognition collection 'memorylens' created!")
except rek.exceptions.ResourceAlreadyExistsException:
    print("✅ Collection already exists — you're good!")
except Exception as e:
    print(f"❌ Failed: {e}")