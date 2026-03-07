"""End-to-end document pipeline test."""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from doc_indexer import DocIndexer
from doc_search import DocSearcher


def main():
    print("=" * 50)
    print("MemoryLens — Document Pipeline Test")
    print("=" * 50)

    sample_dir = os.path.join(os.path.dirname(__file__), "..", "sample_data", "docs")
    sample_dir = os.path.abspath(sample_dir)

    if not os.path.isdir(sample_dir):
        print(f"❌ Sample data directory not found: {sample_dir}")
        print("   Please add test documents to sample_data/docs/")
        sys.exit(1)

    # Check if there are any files
    doc_files = [
        f for f in os.listdir(sample_dir)
        if not f.startswith(".") and os.path.isfile(os.path.join(sample_dir, f))
    ]
    if not doc_files:
        print(f"❌ No documents found in {sample_dir}")
        print("   Please add at least 1 PDF, DOCX, or TXT file")
        sys.exit(1)

    print(f"📁 Found {len(doc_files)} files in {sample_dir}")

    # Step 1: Init DocIndexer and index the folder
    print("\n--- Step 1: Indexing ---")
    indexer = DocIndexer()
    result = indexer.index_folder(sample_dir)
    print(f"✅ Indexed: {result['indexed']}, Skipped: {result['skipped']}, Errors: {result['errors']}")
    assert result["indexed"] > 0 or result["skipped"] > 0, "Nothing was indexed!"

    # Step 2: Save index
    print("\n--- Step 2: Saving index ---")
    indexer.save_index()
    print("✅ FAISS index saved to docs.index")

    # Step 3: Init DocSearcher
    print("\n--- Step 3: Initializing searcher ---")
    searcher = DocSearcher(indexer)
    print("✅ DocSearcher ready")

    # Step 4: Search for exact phrase
    print("\n--- Step 4: Exact phrase search ---")
    # Use the first file's snippet as a search term
    cursor = indexer.db.execute("SELECT text_snippet FROM docs LIMIT 1")
    row = cursor.fetchone()
    if row:
        # Take first few words as search query
        words = row[0].split()[:5]
        test_query = " ".join(words)
        print(f"   Query: \"{test_query}\"")
        results = searcher.search(test_query)
        print(f"   Results: {len(results)}")
        assert len(results) > 0, "Expected at least 1 result for exact phrase"
        print(f"✅ Found {len(results)} results")
    else:
        print("⚠️ No documents in DB to test against")

    # Step 5: Semantic/fuzzy search
    print("\n--- Step 5: Semantic search ---")
    sem_query = "important document about project work"
    print(f"   Query: \"{sem_query}\"")
    results = searcher.search(sem_query)
    print(f"   Top 3 results:")
    for i, r in enumerate(results[:3]):
        print(f"   {i+1}. {os.path.basename(r['file_path'])} — score: {r['score']} ({r['match_source']})")
    print("✅ Semantic search completed")

    # Step 6: Summary
    print("\n" + "=" * 50)
    print("🎉 All tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
