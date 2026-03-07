import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 40)
print("Testing AWS Connections...")
print("=" * 40)

# Test 1 — Rekognition
try:
    rek = boto3.client(
        'rekognition',
        region_name='us-east-1',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    rek.list_collections()
    print("✅ Rekognition — connected")
except Exception as e:
    print(f"❌ Rekognition failed: {e}")

# Test 2 — Textract
try:
    txt = boto3.client(
        'textract',
        region_name='us-east-1',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    print("✅ Textract — connected")
except Exception as e:
    print(f"❌ Textract failed: {e}")

# Test 3 — Bedrock Nova Lite
try:
    bedrock = boto3.client(
        'bedrock-runtime',
        region_name='us-east-1',
        aws_access_key_id=os.getenv('BEDROCK_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('BEDROCK_SECRET_KEY')
    )
    response = bedrock.invoke_model(
        modelId='us.amazon.nova-lite-v1:0',
        body=json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": "say hi"}]
                }
            ]
        })
    )
    result = json.loads(response['body'].read())
    text = result['output']['message']['content'][0]['text']
    print(f"✅ Bedrock Nova Lite — connected: {text}")
except Exception as e:
    print(f"❌ Bedrock Nova failed: {e}")

# Test 4 — Bedrock Titan Embeddings V2
try:
    response = bedrock.invoke_model(
        modelId='amazon.titan-embed-text-v2:0',
        body=json.dumps({
            "inputText": "test",
            "dimensions": 512,
            "normalize": True
        })
    )
    result = json.loads(response['body'].read())
    print(f"✅ Bedrock Titan — connected: got {len(result['embedding'])}-dim vector")
except Exception as e:
    print(f"❌ Bedrock Titan failed: {e}")

print("=" * 40)
print("All tests complete!")
print("=" * 40)