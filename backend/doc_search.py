import boto3
import json
import os
import numpy as np
from dotenv import load_dotenv

load_dotenv()

bedrock = boto3.client(
    'bedrock-runtime',
    region_name='us-east-1',
    aws_access_key_id=os.getenv('BEDROCK_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('BEDROCK_SECRET_KEY')
)

def parse_query_with_ai(user_query: str) -> dict:
    """Use Nova Lite to understand what user is searching for"""
    try:
        prompt = f"""User is searching their files with this query: "{user_query}"

Extract the search intent. Reply ONLY with valid JSON, nothing else:
{{"keywords": ["word1", "word2"], "intent": "brief description of what they want"}}"""

        response = bedrock.invoke_model(
            modelId=os.getenv('BEDROCK_MODEL_ID', 'us.amazon.nova-lite-v1:0'),
            body=json.dumps({
                "messages": [{"role": "user", "content": [{"text": prompt}]}]
            })
        )
        result = json.loads(response['body'].read())
        text = result['output']['message']['content'][0]['text'].strip()
        # Strip markdown code fences if present
        text = text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except Exception as e:
        print(f"⚠️ AI query parsing failed, using fallback: {e}")
        # Fallback: simple keyword extraction
        words = user_query.lower().split()
        return {"keywords": words, "intent": user_query}

def get_query_embedding(text: str) -> list:
    """Get embedding for search query"""
    try:
        response = bedrock.invoke_model(
            modelId=os.getenv('TITAN_MODEL_ID', 'amazon.titan-embed-text-v2:0'),
            body=json.dumps({
                "inputText": text,
                "dimensions": 512,
                "normalize": True
            })
        )
        result = json.loads(response['body'].read())
        return result['embedding']
    except Exception as e:
        print(f"⚠️ Query embedding failed: {e}")
        return None

def search_documents(query: str, doc_index, doc_meta, top_k: int = 5) -> list:
    """Search documents by natural language query"""

    if len(doc_meta) == 0:
        return []

    # Step 1: Parse query with AI
    parsed = parse_query_with_ai(query)
    keywords = parsed.get('keywords', [])

    # Step 2: Get query embedding
    embedding = get_query_embedding(query)
    if embedding is None:
        return []

    # Step 3: FAISS semantic search
    vec = np.array([embedding], dtype='float32')
    k = min(top_k, len(doc_meta))
    distances, indices = doc_index.search(vec, k)

    # Step 4: Build results
    results = []
    for i, idx in enumerate(indices[0]):
        if idx == -1:
            continue

        meta = doc_meta[idx]
        score = float(distances[0][i])

        snippet = find_best_snippet(meta.get('full_text', meta['snippet']), keywords)

        # Fix 1: Only show results above 15% relevance
        final_score = round(score * 100, 1)
        if final_score < 15:
            continue

        results.append({
            "path": meta['path'],
            "filename": meta['filename'],
            "snippet": snippet,
            "score": final_score
        })

    return results

def find_best_snippet(text: str, keywords: list, snippet_len: int = 300) -> str:
    """Find the part of text that contains the most keywords"""
    if not keywords or not text:
        return text[:snippet_len]

    text_lower = text.lower()
    best_pos = 0
    best_count = 0

    for i in range(0, max(1, len(text) - snippet_len), 50):
        chunk = text_lower[i:i + snippet_len]
        count = sum(1 for kw in keywords if kw.lower() in chunk)
        if count > best_count:
            best_count = count
            best_pos = i

    snippet = text[best_pos:best_pos + snippet_len].strip()
    return snippet + "..." if len(text) > best_pos + snippet_len else snippet

# Test it
if __name__ == "__main__":
    parsed = parse_query_with_ai("find the document about project budget 9195")
    print("✅ AI parsed query:", parsed)