"""Document Search — Claude query parsing + FAISS semantic + SQLite keyword search."""
import json
import logging
import time

import numpy as np
import boto3
from dotenv import load_dotenv
import os

load_dotenv()
logger = logging.getLogger(__name__)


class DocSearcher:
    """Searches indexed documents using semantic + keyword hybrid approach."""

    def __init__(self, doc_indexer):
        """
        Args:
            doc_indexer: DocIndexer instance (shares FAISS index + SQLite).
        """
        self.indexer = doc_indexer
        self.index = doc_indexer.index
        self.db = doc_indexer.db

        self.bedrock = boto3.client(
            "bedrock-runtime",
            region_name=os.getenv("BEDROCK_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("BEDROCK_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("BEDROCK_SECRET_KEY"),
        )

    # ── Query Parsing ────────────────────────────────────────

    def parse_query_with_claude(self, query: str) -> dict:
        """Use Claude Sonnet 4 to parse user query into structured data.

        Returns:
            {"type": "document"|"image"|"any", "keywords": [...], "intent": "..."}
        """
        try:
            response = self._invoke_claude(query)
            result = json.loads(response["body"].read())
            text = result["content"][0]["text"]
            parsed = json.loads(text)
            return parsed
        except (json.JSONDecodeError, KeyError, IndexError):
            logger.warning(f"Claude returned invalid JSON for query: {query}")
            return {
                "type": "any",
                "keywords": query.split(),
                "intent": query,
            }
        except Exception as e:
            # Retry once after 2 seconds (Bedrock rate limit handling)
            logger.warning(f"Claude parse failed, retrying: {e}")
            time.sleep(2)
            try:
                response = self._invoke_claude(query)
                result = json.loads(response["body"].read())
                text = result["content"][0]["text"]
                return json.loads(text)
            except Exception:
                return {
                    "type": "any",
                    "keywords": query.split(),
                    "intent": query,
                }

    def _invoke_claude(self, query: str):
        """Make the actual Bedrock Claude API call."""
        return self.bedrock.invoke_model(
            modelId="us.anthropic.claude-sonnet-4-5-20251001",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 200,
                "system": "You are a search query parser. Extract structured data from user queries.",
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f'Parse this file search query and return ONLY valid JSON (no markdown):\n'
                            f'Query: "{query}"\n'
                            f'Return: {{"type": "document"|"image"|"any", '
                            f'"keywords": ["word1","word2",...], '
                            f'"intent": "brief description"}}\n'
                            f'Extract all meaningful keywords, names, numbers, and phrases.'
                        ),
                    }
                ],
            }),
        )

    # ── Semantic Search ──────────────────────────────────────

    def semantic_search(self, query_text: str, top_k: int = 20) -> list[dict]:
        """Search FAISS index for semantically similar documents."""
        if self.index.ntotal == 0:
            return []

        query_vec = self.indexer.get_embedding(query_text).reshape(1, -1)
        distances, indices = self.index.search(query_vec, min(top_k, self.index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue

            cursor = self.db.execute(
                "SELECT file_path, file_type, text_snippet FROM docs WHERE faiss_id = ?",
                (int(idx),),
            )
            row = cursor.fetchone()
            if row:
                # Convert L2 distance to similarity score
                score = round(1 / (1 + float(dist)), 4)
                results.append({
                    "file_path": row[0],
                    "file_type": row[1],
                    "snippet": row[2],
                    "score": score,
                    "match_source": "semantic",
                })

        return results

    # ── Keyword Search ───────────────────────────────────────

    def keyword_search(self, keywords: list[str], top_k: int = 20) -> list[dict]:
        """Search SQLite using keyword matching on full_text."""
        if not keywords:
            return []

        # Build WHERE clause
        conditions = " OR ".join(["full_text LIKE ?" for _ in keywords])
        params = [f"%{kw}%" for kw in keywords]

        cursor = self.db.execute(
            f"SELECT file_path, file_type, text_snippet, full_text FROM docs WHERE {conditions}",
            params,
        )

        results = []
        for row in cursor.fetchall():
            file_path, file_type, snippet, full_text = row
            full_text_lower = full_text.lower()

            # Score by count of matching keywords
            match_count = sum(
                1 for kw in keywords if kw.lower() in full_text_lower
            )
            score = round(match_count / len(keywords), 4) if keywords else 0

            results.append({
                "file_path": file_path,
                "file_type": file_type,
                "snippet": snippet,
                "score": score,
                "match_source": "keyword",
            })

        # Sort by score descending and limit
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    # ── Smart Snippet ────────────────────────────────────────

    def extract_smart_snippet(
        self, full_text: str, keywords: list[str], window: int = 300
    ) -> str:
        """Find the text region where keywords cluster most densely."""
        if not keywords or not full_text:
            return full_text[:300] if full_text else ""

        text_lower = full_text.lower()
        best_pos = 0
        best_count = 0

        # Slide a window and count keyword hits
        for i in range(0, len(full_text) - window, 50):
            chunk = text_lower[i : i + window]
            count = sum(1 for kw in keywords if kw.lower() in chunk)
            if count > best_count:
                best_count = count
                best_pos = i

        start = max(0, best_pos)
        end = min(len(full_text), best_pos + window)
        snippet = full_text[start:end].strip()

        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(full_text) else ""

        return f"{prefix}{snippet}{suffix}"

    # ── Merge & Rank ─────────────────────────────────────────

    def merge_and_rank(
        self, semantic: list[dict], keyword: list[dict]
    ) -> list[dict]:
        """Combine semantic and keyword results, boost overlaps."""
        merged = {}

        for item in semantic:
            fp = item["file_path"]
            merged[fp] = item.copy()

        for item in keyword:
            fp = item["file_path"]
            if fp in merged:
                # Boost score for appearing in both
                merged[fp]["score"] = min(merged[fp]["score"] + 0.2, 1.0)
                merged[fp]["match_source"] = "semantic+keyword"
            else:
                merged[fp] = item.copy()

        # Sort by score descending, return top 10
        ranked = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
        return ranked[:10]

    # ── Main Search ──────────────────────────────────────────

    def search(self, query: str) -> list[dict]:
        """Full search pipeline: parse → semantic + keyword → merge → snippets.

        Returns:
            [{"file_path", "file_type", "snippet", "score", "match_source"}]
        """
        # Parse query with Claude
        parsed = self.parse_query_with_claude(query)
        logger.info(f"Parsed query: {parsed}")

        # Dual search
        sem_results = self.semantic_search(query)
        kw_results = self.keyword_search(parsed.get("keywords", query.split()))

        # Merge and rank
        merged = self.merge_and_rank(sem_results, kw_results)

        # Improve snippets with smart extraction
        keywords = parsed.get("keywords", query.split())
        for result in merged:
            cursor = self.db.execute(
                "SELECT full_text FROM docs WHERE file_path = ?",
                (result["file_path"],),
            )
            row = cursor.fetchone()
            if row and row[0]:
                result["snippet"] = self.extract_smart_snippet(row[0], keywords)

        return merged
