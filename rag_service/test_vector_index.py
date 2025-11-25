"""Test script for Vector Index Engine."""
import asyncio
import json
from datetime import datetime
from sqlalchemy import select

from database import init_db, AsyncSessionLocal, VectorDocument, VectorChunk
from indexes.vector_index import VectorIndexEngine


async def test_database():
    """Test database initialization."""
    print("\n=== Testing Database Initialization ===")
    await init_db()
    print("✓ Database initialized successfully")


async def test_document_ingestion():
    """Test document ingestion into vector index."""
    print("\n=== Testing Document Ingestion ===")

    engine = VectorIndexEngine()

    # Test document
    test_doc = {
        "document_id": "test_vector_doc_1",
        "title": "Introduction to Vector Search",
        "content": """
        Vector search is a powerful technique for finding similar items based on their semantic meaning.
        Unlike traditional keyword search, vector search uses embeddings to represent documents in a
        high-dimensional space. This allows for more nuanced similarity comparisons.

        The process works by converting text into dense vector representations, often using neural networks
        or other machine learning models. These vectors capture the semantic meaning of the text, so that
        documents with similar meanings will have similar vector representations.

        Applications of vector search include recommendation systems, semantic search engines, duplicate
        detection, and question answering systems. It's particularly useful when you need to find content
        that is conceptually similar rather than just matching keywords.
        """,
        "metadata": {"source": "test", "type": "tutorial"}
    }

    async with AsyncSessionLocal() as db:
        start_time = datetime.utcnow()
        result = await engine.ingest_document(
            db=db,
            document_id=test_doc["document_id"],
            content=test_doc["content"],
            title=test_doc["title"],
            metadata=test_doc["metadata"]
        )
        end_time = datetime.utcnow()

        print(f"\n✓ Document ingested successfully")
        print(f"  - Document ID: {result['document_id']}")
        print(f"  - Chunks created: {result['chunks_created']}")
        print(f"  - Duration: {result['duration_seconds']:.2f} seconds")
        print(f"  - Status: {result['status']}")

        return result


async def test_query():
    """Test querying the vector index."""
    print("\n=== Testing Vector Index Queries ===")

    engine = VectorIndexEngine()

    test_queries = [
        "What is semantic search?",
        "How do embeddings work?",
        "Applications of vector search"
    ]

    async with AsyncSessionLocal() as db:
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            result = await engine.query_vector_index(
                db=db,
                query=query,
                top_k=3
            )

            print(f"  Found {len(result['chunks'])} results:")
            for i, chunk in enumerate(result['chunks'], 1):
                print(f"\n  Result {i}:")
                print(f"    - Score: {chunk['score']:.4f}")
                print(f"    - Chunk ID: {chunk['chunk_id']}")
                print(f"    - Content preview: {chunk['content'][:100]}...")
                if chunk.get('document_title'):
                    print(f"    - Document: {chunk['document_title']}")


async def test_get_document():
    """Test retrieving document chunks."""
    print("\n=== Testing Document Retrieval ===")

    engine = VectorIndexEngine()
    document_id = "test_vector_doc_1"

    async with AsyncSessionLocal() as db:
        result = await engine.get_document_chunks(
            db=db,
            document_id=document_id
        )

        if result:
            print(f"\n✓ Document retrieved successfully")
            print(f"  - Document ID: {result['document_id']}")
            print(f"  - Title: {result['title']}")
            print(f"  - Total chunks: {result['chunks_count']}")
            print(f"\n  Chunks:")
            for chunk in result['chunks']:
                print(f"    - Chunk {chunk['chunk_index']}: {chunk['content'][:80]}...")
        else:
            print(f"✗ Document not found: {document_id}")


async def test_database_state():
    """Verify database state after ingestion."""
    print("\n=== Verifying Database State ===")

    async with AsyncSessionLocal() as db:
        # Count documents
        result = await db.execute(select(VectorDocument))
        docs = result.scalars().all()
        print(f"\n✓ Total documents: {len(docs)}")

        # Count chunks
        result = await db.execute(select(VectorChunk))
        chunks = result.scalars().all()
        print(f"✓ Total chunks: {len(chunks)}")

        # Show document details
        for doc in docs:
            print(f"\nDocument: {doc.document_id}")
            print(f"  - Title: {doc.title}")
            print(f"  - Created: {doc.created_at}")

            # Get chunks count separately to avoid lazy loading issue
            chunk_result = await db.execute(
                select(VectorChunk).where(VectorChunk.document_id == doc.id)
            )
            doc_chunks = chunk_result.scalars().all()
            print(f"  - Chunks: {len(doc_chunks)}")

            # Show first chunk embedding info
            if doc_chunks:
                first_chunk = doc_chunks[0]
                if first_chunk.embedding:
                    print(f"  - Embedding dimensions: {len(first_chunk.embedding)}")
                    print(f"  - Sample embedding values: {first_chunk.embedding[:5]}")


async def main():
    """Run all tests."""
    print("=" * 70)
    print("VECTOR INDEX ENGINE TEST SUITE")
    print("=" * 70)

    try:
        # Run tests in sequence
        await test_database()
        await test_document_ingestion()
        await test_query()
        await test_get_document()
        await test_database_state()

        print("\n" + "=" * 70)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
