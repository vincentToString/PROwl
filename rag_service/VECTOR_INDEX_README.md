# Vector Index Implementation

This document describes the parallel implementation of the Vector Index alongside the Knowledge Graph Index in the RAG service.

## Overview

The Vector Index Engine provides semantic search capabilities using LlamaIndex's `VectorStoreIndex`. It follows the same architecture patterns as the Knowledge Graph Index but focuses solely on vector embeddings and semantic similarity search.

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│                         (main.py)                            │
└────────┬──────────────────────────────────────┬──────────────┘
         │                                      │
    POST /api/v1/vector-index/ingest      POST /api/v1/vector-index/query
    GET /api/v1/vector-index/document/{id}
         │                                      │
         └──────────────────┬───────────────────┘
                            │
                ┌───────────▼─────────────┐
                │  VectorIndexEngine      │
                │  (vector_index.py)      │
                └───────────┬─────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
    ┌────▼────┐  ┌─────────▼──────────┐  ┌───▼────┐
    │LlamaIndex│  │ SimpleVectorStore │  │ Hash   │
    │Document  │  │  (Embeddings)     │  │Embedder│
    │&VectorIdx│  │                   │  │        │
    └────┬────┘  └─────────┬──────────┘  └────────┘
         │                 │
         └─────────────────┼─────────────────┐
                           │                  │
                ┌──────────▼──────────┐      │
                │   PostgreSQL        │      │
                │   Database          │      │
                ├─────────────────────┤      │
                │ vector_documents    │      │
                │ vector_chunks       │ ◄────┘
                └─────────────────────┘
```

## Implementation Details

### 1. Database Schema

**VectorDocument Table** (`vector_documents`)
- `id`: Primary key
- `document_id`: Unique document identifier
- `title`: Document title
- `content`: Full document text
- `doc_metadata`: JSON metadata
- `created_at`, `updated_at`: Timestamps

**VectorChunk Table** (`vector_chunks`)
- `id`: Primary key
- `chunk_id`: Unique chunk identifier
- `document_id`: Foreign key to document
- `content`: Chunk text
- `chunk_index`: Position in document
- `embedding`: JSON array of embedding vector (384 dimensions)
- `created_at`: Timestamp

### 2. Vector Index Engine (`indexes/vector_index.py`)

The `VectorIndexEngine` class provides:

#### Initialization
```python
VectorIndexEngine()
```
- Configures LlamaIndex settings
- Uses hash-based embeddings (fallback, no external API needed)
- Optional LLM via OpenRouter (Deepseek)
- Initializes SimpleVectorStore
- Maintains index cache

#### Document Ingestion
```python
async def ingest_document(
    db: AsyncSession,
    document_id: str,
    content: str,
    title: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

**Process:**
1. Check if document exists (update) or create new
2. Create LlamaIndex `Document` with metadata
3. Build `VectorStoreIndex` (automatic chunking)
4. Extract nodes/chunks from index
5. Generate embeddings for each chunk
6. Store chunks with embeddings in PostgreSQL
7. Cache index for querying

**Returns:**
```json
{
    "document_id": "doc_123",
    "chunks_created": 5,
    "duration_seconds": 1.23,
    "status": "success"
}
```

#### Querying
```python
async def query_vector_index(
    db: AsyncSession,
    query: str,
    top_k: int = 5
) -> Dict[str, Any]
```

**Process:**
1. Generate embedding for query
2. Fetch all chunks from database
3. Calculate cosine similarity with query embedding
4. Sort by similarity score (descending)
5. Return top K results

**Returns:**
```json
{
    "query": "search term",
    "chunks": [
        {
            "chunk_id": "doc_123_chunk_0",
            "content": "chunk text...",
            "score": 0.85,
            "document_id": "doc_123",
            "document_title": "Document Title"
        }
    ]
}
```

#### Document Retrieval
```python
async def get_document_chunks(
    db: AsyncSession,
    document_id: str
) -> Optional[Dict[str, Any]]
```

Returns all chunks for a specific document, ordered by chunk index.

### 3. API Endpoints

All endpoints are under `/api/v1/vector-index/`:

#### POST `/ingest`
Ingest a document into the vector index.

**Request:**
```json
{
    "document_id": "doc_123",
    "content": "Document text...",
    "title": "Document Title",
    "metadata": {"source": "test"}
}
```

**Response:** `VectorIngestResponse`

#### POST `/query`
Query the vector index using semantic similarity.

**Request:**
```json
{
    "query": "search term",
    "top_k": 5
}
```

**Response:** `VectorQueryResponse`

#### GET `/document/{document_id}`
Retrieve all chunks for a document.

**Response:** `VectorDocumentResponse`

### 4. Embedding Strategy

The implementation uses **hash-based embeddings** as a fallback that doesn't require external APIs:

```python
def _generate_simple_embedding(text: str) -> List[float]:
    # SHA256 hash of text
    # Convert to 384-dimensional vector
    # Values normalized to [-1, 1]
```

**Advantages:**
- No external API dependencies
- Deterministic (same text → same embedding)
- Fast computation
- No API costs

**Limitations:**
- Not as semantically rich as neural embeddings
- Best for exact/near-exact text matching

**Future Enhancement:**
Can be replaced with proper embedding models like:
- OpenAI `text-embedding-3-small`
- Sentence-Transformers
- HuggingFace models

## Comparison: Vector Index vs Knowledge Graph Index

| Feature | Vector Index | Knowledge Graph Index |
|---------|-------------|----------------------|
| **Primary Focus** | Semantic similarity | Entity relationships |
| **Storage** | Chunks + Embeddings | Chunks + Entities + Relations |
| **Query Type** | Similarity search | Graph traversal + Similarity |
| **Use Case** | Find similar content | Understand connections |
| **Complexity** | Lower | Higher |
| **LLM Required** | Optional | Yes (for extraction) |
| **Response Type** | Ranked chunks | Chunks + Entities + Relations |

## Configuration

All settings in `config.py` (shared with KG index):

```python
# Chunking
KG_CHUNK_SIZE = 512          # Chunk size in tokens
KG_CHUNK_OVERLAP = 50        # Overlap between chunks

# LLM (optional)
OPENROUTER_API_KEY = ""      # For Deepseek LLM
OPENROUTER_BASE = "..."      # OpenRouter API base URL
```

## Testing

Run the test suite:

```bash
cd rag_service
python test_vector_index.py
```

**Test Coverage:**
1. Database initialization
2. Document ingestion
3. Vector queries with multiple search terms
4. Document retrieval
5. Database state verification

## Usage Examples

### Python Client

```python
import httpx
import asyncio

async def test_vector_index():
    async with httpx.AsyncClient() as client:
        # Ingest document
        response = await client.post(
            "http://localhost:8002/api/v1/vector-index/ingest",
            json={
                "document_id": "doc1",
                "content": "Your document content here...",
                "title": "Document Title"
            }
        )
        print(response.json())

        # Query
        response = await client.post(
            "http://localhost:8002/api/v1/vector-index/query",
            json={
                "query": "search term",
                "top_k": 5
            }
        )
        print(response.json())

asyncio.run(test_vector_index())
```

### cURL

```bash
# Ingest
curl -X POST http://localhost:8002/api/v1/vector-index/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc1",
    "content": "Your document content...",
    "title": "Document Title"
  }'

# Query
curl -X POST http://localhost:8002/api/v1/vector-index/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "search term",
    "top_k": 5
  }'

# Get document
curl http://localhost:8002/api/v1/vector-index/document/doc1
```

## Performance Considerations

### Optimization Tips

1. **Batch Ingestion**: Ingest multiple documents in parallel
2. **Index Size**: Monitor database growth
3. **Query Performance**: Add database indices on frequently queried fields
4. **Embedding Cache**: Reuse embeddings for repeated queries
5. **Chunking Strategy**: Tune chunk size/overlap for your use case

### Scalability

- **PostgreSQL**: Handles millions of chunks
- **Async Operations**: Non-blocking I/O
- **Connection Pooling**: Configured (pool_size=10, max_overflow=20)
- **Future**: Can migrate to specialized vector databases (Pinecone, Weaviate, Milvus)

## Future Enhancements

1. **Better Embeddings**: Integrate with OpenAI or Sentence-Transformers
2. **Hybrid Search**: Combine vector search with keyword search
3. **Reranking**: Add cross-encoder for result refinement
4. **Metadata Filtering**: Filter results by metadata fields
5. **Batch Query**: Support multiple queries in one request
6. **Vector DB**: Migrate to pgvector or dedicated vector DB
7. **Compression**: Implement embedding compression techniques

## Troubleshooting

### Common Issues

**1. Import Error: `VectorDocument` not found**
- Ensure database models are imported in `database.py`
- Run `await init_db()` to create tables

**2. Embedding dimension mismatch**
- Check hash-based embedding always returns 384 dimensions
- Verify JSON storage in PostgreSQL

**3. Low similarity scores**
- Hash-based embeddings have limitations
- Consider switching to neural embeddings

**4. Performance issues**
- Add database indices
- Optimize chunk size
- Use connection pooling

## Related Files

- `indexes/vector_index.py` - Main implementation
- `indexes/knowledge_graph_index.py` - Parallel KG implementation
- `database.py` - Database models
- `main.py` - API endpoints
- `schemas.py` - Request/response schemas
- `test_vector_index.py` - Test suite
- `config.py` - Configuration

## Summary

The Vector Index provides a streamlined, efficient semantic search capability that complements the Knowledge Graph Index. It's simpler, faster to set up, and ideal for pure similarity search use cases. Both systems can run in parallel, allowing clients to choose the appropriate index for their needs.
