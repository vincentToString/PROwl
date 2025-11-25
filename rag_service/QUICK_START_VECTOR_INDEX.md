# Vector Index - Quick Start Guide

## Overview
The Vector Index provides semantic search capabilities using LlamaIndex's VectorStoreIndex. It's simpler than the Knowledge Graph Index and focuses on finding similar content.

## When to Use Which Index?

### Use Vector Index When:
- You need fast semantic similarity search
- You want to find documents similar to a query
- You don't need entity relationships
- You want simpler, faster ingestion

### Use Knowledge Graph Index When:
- You need to understand entity relationships
- You want to traverse connections between concepts
- You need structured knowledge extraction
- Graph queries are important

### Use Both When:
- You want comprehensive search (similarity + relationships)
- Different use cases need different approaches
- You want to compare results from both methods

## Quick Setup

### 1. Ensure Prerequisites
```bash
# PostgreSQL running
# Virtual environment activated
cd rag_service
source venv/bin/activate  # or your virtualenv path

# Install dependencies
pip install -r requirements.txt
```

### 2. Start the Service
```bash
python main.py
# Service runs on http://localhost:8002
```

### 3. Check API Documentation
Open browser: `http://localhost:8002/docs`

## API Examples

### Ingest a Document
```bash
curl -X POST http://localhost:8002/api/v1/vector-index/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "my_doc_1",
    "content": "LlamaIndex is a data framework for LLM applications. It provides tools for ingesting, structuring, and accessing private or domain-specific data.",
    "title": "LlamaIndex Introduction"
  }'
```

**Response:**
```json
{
  "document_id": "my_doc_1",
  "chunks_created": 1,
  "duration_seconds": 0.52,
  "status": "success"
}
```

### Query the Index
```bash
curl -X POST http://localhost:8002/api/v1/vector-index/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is LlamaIndex used for?",
    "top_k": 3
  }'
```

**Response:**
```json
{
  "query": "What is LlamaIndex used for?",
  "chunks": [
    {
      "chunk_id": "my_doc_1_chunk_0",
      "content": "LlamaIndex is a data framework...",
      "score": 0.8542,
      "document_id": "my_doc_1",
      "document_title": "LlamaIndex Introduction"
    }
  ]
}
```

### Get Document Chunks
```bash
curl http://localhost:8002/api/v1/vector-index/document/my_doc_1
```

**Response:**
```json
{
  "document_id": "my_doc_1",
  "title": "LlamaIndex Introduction",
  "metadata": {},
  "chunks": [
    {
      "chunk_id": "my_doc_1_chunk_0",
      "content": "LlamaIndex is a data framework...",
      "chunk_index": 0
    }
  ],
  "chunks_count": 1
}
```

## Python Client Example

```python
import httpx
import asyncio

async def vector_search_demo():
    base_url = "http://localhost:8002/api/v1/vector-index"

    async with httpx.AsyncClient() as client:
        # 1. Ingest documents
        documents = [
            {
                "document_id": "doc1",
                "content": "Python is a programming language.",
                "title": "Python Basics"
            },
            {
                "document_id": "doc2",
                "content": "JavaScript is used for web development.",
                "title": "JavaScript Intro"
            }
        ]

        for doc in documents:
            response = await client.post(f"{base_url}/ingest", json=doc)
            print(f"Ingested: {response.json()}")

        # 2. Query
        query_response = await client.post(
            f"{base_url}/query",
            json={"query": "programming languages", "top_k": 5}
        )

        results = query_response.json()
        print(f"\nQuery: {results['query']}")
        print(f"Found {len(results['chunks'])} results:")

        for i, chunk in enumerate(results['chunks'], 1):
            print(f"\n{i}. Score: {chunk['score']:.4f}")
            print(f"   Document: {chunk['document_title']}")
            print(f"   Content: {chunk['content'][:100]}...")

asyncio.run(vector_search_demo())
```

## Testing

### Run the Test Suite
```bash
cd rag_service
python test_vector_index.py
```

**Expected Output:**
```
======================================================================
VECTOR INDEX ENGINE TEST SUITE
======================================================================

=== Testing Database Initialization ===
✓ Database initialized successfully

=== Testing Document Ingestion ===
✓ Document ingested successfully
  - Document ID: test_vector_doc_1
  - Chunks created: 3
  - Duration: 0.78 seconds
  - Status: success

=== Testing Vector Index Queries ===
Query: 'What is semantic search?'
  Found 3 results:
  ...

=== Testing Document Retrieval ===
✓ Document retrieved successfully
  ...

=== Verifying Database State ===
✓ Total documents: 1
✓ Total chunks: 3
...

======================================================================
ALL TESTS COMPLETED SUCCESSFULLY!
======================================================================
```

## Configuration

Edit `.env` or set environment variables:

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=prowl_user
POSTGRES_PASSWORD=prowl_password
POSTGRES_DB=prowl_db

# Chunking (shared with KG index)
KG_CHUNK_SIZE=512
KG_CHUNK_OVERLAP=50

# Optional: LLM for advanced features
OPENROUTER_API_KEY=your_key_here
```

## Comparison with Knowledge Graph Index

### Vector Index Endpoints
```
POST   /api/v1/vector-index/ingest
POST   /api/v1/vector-index/query
GET    /api/v1/vector-index/document/{id}
```

### Knowledge Graph Index Endpoints
```
POST   /api/v1/kg-index/ingest
POST   /api/v1/kg-index/query
GET    /api/v1/kg-index/document/{id}
```

### Response Differences

**Vector Index Query Response:**
```json
{
  "query": "...",
  "chunks": [...]
}
```

**KG Index Query Response:**
```json
{
  "query": "...",
  "chunks": [...],
  "entities": [...],
  "relations": [...]
}
```

## Common Use Cases

### 1. Document Similarity Search
```python
# Find documents similar to a query
query = "machine learning frameworks"
response = await client.post(f"{base_url}/query", json={"query": query, "top_k": 5})
```

### 2. Question Answering
```python
# Find relevant context for a question
question = "How do I install the package?"
response = await client.post(f"{base_url}/query", json={"query": question, "top_k": 3})
# Use top chunks as context for LLM
```

### 3. Duplicate Detection
```python
# Find similar/duplicate content
new_content = "..."
response = await client.post(f"{base_url}/query", json={"query": new_content, "top_k": 5})
# Check if any results have high similarity scores (e.g., > 0.9)
```

### 4. Recommendation System
```python
# Given a document, find similar documents
doc_content = "..."
response = await client.post(f"{base_url}/query", json={"query": doc_content, "top_k": 10})
# Recommend documents with high similarity
```

## Performance Tips

1. **Batch Ingestion**: Ingest multiple documents in parallel
   ```python
   tasks = [ingest_document(doc) for doc in documents]
   await asyncio.gather(*tasks)
   ```

2. **Tune Chunk Size**: Adjust `KG_CHUNK_SIZE` for your content
   - Smaller chunks (256): More precise matching
   - Larger chunks (1024): More context per result

3. **Top K Selection**: Use appropriate `top_k` values
   - Small corpus: top_k=10
   - Large corpus: top_k=20-50

4. **Caching**: Cache frequent queries (implement in your app)

## Troubleshooting

### Issue: No results returned
**Cause:** No documents ingested or query doesn't match content
**Solution:** Check documents are ingested successfully, try different queries

### Issue: Low similarity scores
**Cause:** Hash-based embeddings have limitations
**Solution:** This is expected with hash embeddings; consider neural embeddings for better semantic understanding

### Issue: Slow queries
**Cause:** Large number of chunks to compare
**Solution:** Add database indices, consider migrating to dedicated vector DB

### Issue: Database connection error
**Cause:** PostgreSQL not running or wrong credentials
**Solution:** Check PostgreSQL status, verify environment variables

## Next Steps

1. ✅ Test with your own documents
2. ✅ Try different query types
3. ✅ Compare results with Knowledge Graph Index
4. ✅ Integrate into your application
5. ⭐ Consider upgrading to neural embeddings for better results

## Resources

- **Detailed Documentation**: [VECTOR_INDEX_README.md](VECTOR_INDEX_README.md)
- **Implementation Summary**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **API Docs**: http://localhost:8002/docs (when service is running)
- **LlamaIndex Docs**: https://docs.llamaindex.ai/

## Questions?

Check the full documentation in [VECTOR_INDEX_README.md](VECTOR_INDEX_README.md) for:
- Architecture details
- Database schema
- Comparison tables
- Future enhancements
- Troubleshooting guide
