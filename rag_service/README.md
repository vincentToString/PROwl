# RAG Service - Knowledge Graph Index

A RAG (Retrieval-Augmented Generation) service with a Knowledge Graph Index engine for document ingestion and querying.

## Features

- **Document Ingestion**: Processes raw documents into knowledge graphs
  - Text chunking with overlap for context preservation
  - Entity extraction using LLM (persons, organizations, concepts, etc.)
  - Relationship extraction between entities
  - Semantic embeddings for similarity search

- **Knowledge Graph Storage**: PostgreSQL with optimized schema
  - Documents, chunks, entities, and relations tables
  - Efficient indexing for fast queries
  - Support for metadata and custom attributes

- **Query API**: FastAPI endpoints for accessing the knowledge base
  - Semantic search across chunks
  - Entity lookup by text matching
  - Relationship traversal
  - Document graph visualization

## Architecture

```
Document → Chunking → Entity Extraction → Relation Extraction → Storage
                                                                     ↓
Query → Embedding → Similarity Search → Entity Match → Results
```

## API Endpoints

### Health Check
```
GET /health
```

### Ingest Document
```
POST /api/v1/kg-index/ingest
Content-Type: application/json

{
  "document_id": "doc-123",
  "content": "Your document content here...",
  "title": "Document Title",
  "metadata": {
    "author": "John Doe",
    "tags": ["tech", "ai"]
  }
}
```

**Response:**
```json
{
  "document_id": "doc-123",
  "chunks_created": 5,
  "entities_created": 12,
  "relations_created": 8,
  "duration_seconds": 3.45,
  "status": "success"
}
```

### Query Knowledge Graph
```
POST /api/v1/kg-index/query
Content-Type: application/json

{
  "query": "What is machine learning?",
  "top_k": 5,
  "include_relations": true
}
```

**Response:**
```json
{
  "query": "What is machine learning?",
  "chunks": [
    {
      "chunk_id": "doc-123_chunk_0",
      "content": "Machine learning is...",
      "score": 0.89,
      "document_id": "doc-123"
    }
  ],
  "entities": [
    {
      "entity_id": "uuid-here",
      "text": "Machine Learning",
      "type": "CONCEPT",
      "metadata": {}
    }
  ],
  "relations": [
    {
      "relation_id": "uuid-here",
      "source": "Machine Learning",
      "target": "Artificial Intelligence",
      "type": "PART_OF",
      "confidence": 0.8
    }
  ]
}
```

### Get Document Graph
```
GET /api/v1/kg-index/document/{document_id}
```

**Response:**
```json
{
  "document_id": "doc-123",
  "title": "Document Title",
  "metadata": {},
  "entities": [...],
  "relations": [...],
  "chunks_count": 5
}
```

## Configuration

Environment variables (set in `.env` or `docker-compose.yml`):

- `POSTGRES_HOST`: PostgreSQL host (default: localhost)
- `POSTGRES_PORT`: PostgreSQL port (default: 5432)
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_DB`: Database name
- `OPENROUTER_API_KEY`: API key for LLM services
- `OPENROUTER_BASE`: Base URL for OpenRouter API
- `EMBEDDING_MODEL`: Model for embeddings
- `SERVICE_HOST`: Service host (default: 0.0.0.0)
- `SERVICE_PORT`: Service port (default: 8002)
- `KG_CHUNK_SIZE`: Text chunk size (default: 512)
- `KG_CHUNK_OVERLAP`: Chunk overlap (default: 50)
- `KG_MAX_ENTITIES_PER_CHUNK`: Max entities per chunk (default: 10)

## Running with Docker

```bash
# Build and start the service
docker-compose up -d rag_service

# View logs
docker-compose logs -f rag_service

# Stop the service
docker-compose down
```

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_USER=prowl_user
export POSTGRES_PASSWORD=prowl_password
export POSTGRES_DB=prowl_db
export OPENROUTER_API_KEY=your-api-key

# Run the service
python main.py
```

The service will be available at `http://localhost:8002`

## Database Schema

### Tables

1. **kg_documents**: Stores document metadata
2. **kg_chunks**: Text chunks with embeddings
3. **kg_entities**: Extracted entities (persons, concepts, etc.)
4. **kg_relations**: Relationships between entities

### Relationships

- Documents → Chunks (one-to-many)
- Chunks → Entities (one-to-many)
- Entities → Relations (many-to-many through relations table)

## Using the Knowledge Graph Index Programmatically

### Direct Integration with LlamaIndex

The Knowledge Graph Index Engine is built on **LlamaIndex** and can be used directly in your Python code for more advanced use cases:

#### 1. Basic Usage from Another Service

```python
from indexes.knowledge_graph_index import KnowledgeGraphIndexEngine
from database import get_db

# Initialize the engine
kg_engine = KnowledgeGraphIndexEngine()

# Ingest a document
async with get_db() as db:
    result = await kg_engine.ingest_document(
        db=db,
        document_id="my-doc-001",
        content="Your document text here...",
        title="My Document",
        metadata={"category": "research"}
    )
    print(f"Created {result['entities_created']} entities")

# Query the knowledge graph
async with get_db() as db:
    results = await kg_engine.query_knowledge_graph(
        db=db,
        query="What are the main concepts?",
        top_k=5,
        include_relations=True
    )
    for chunk in results['chunks']:
        print(f"Score: {chunk['score']}, Content: {chunk['content'][:100]}")
```

#### 2. Using LlamaIndex Query Engine Directly

For more advanced querying with LlamaIndex's native capabilities:

```python
from indexes.knowledge_graph_index import KnowledgeGraphIndexEngine
from llama_index.core.query_engine import KnowledgeGraphQueryEngine

# Initialize the engine
kg_engine = KnowledgeGraphIndexEngine()

# After ingesting documents, access the LlamaIndex KnowledgeGraphIndex
document_id = "my-doc-001"
if document_id in kg_engine._index_cache:
    kg_index = kg_engine._index_cache[document_id]

    # Create a LlamaIndex query engine
    query_engine = kg_index.as_query_engine(
        include_text=True,  # Include original text in results
        response_mode="tree_summarize",  # How to synthesize the response
        embedding_mode="hybrid",  # Use both text and graph
    )

    # Query using LlamaIndex's natural language capabilities
    response = query_engine.query("What are the key relationships in this document?")
    print(response.response)

    # Access the source nodes (chunks) used for the response
    for node in response.source_nodes:
        print(f"Source: {node.text[:100]}")
        print(f"Score: {node.score}")
```

#### 3. Advanced: Custom Graph Traversal

```python
from indexes.knowledge_graph_index import KnowledgeGraphIndexEngine

kg_engine = KnowledgeGraphIndexEngine()

# Access the underlying graph store
graph_store = kg_engine.graph_store

# The graph store contains triplets in the form (subject, relation, object)
# Access via _data.rel_map for direct graph traversal
if hasattr(graph_store, '_data') and hasattr(graph_store._data, 'rel_map'):
    # rel_map is a dict: subject -> list of (object, relation_type)
    for subject, relations in graph_store._data.rel_map.items():
        print(f"Entity: {subject}")
        for obj, rel_type in relations:
            print(f"  {rel_type} -> {obj}")
```

#### 4. Integration in AI Service Worker

Example of using the KG Index in your AI processing pipeline:

```python
# In your AI service worker
from indexes.knowledge_graph_index import KnowledgeGraphIndexEngine
from database import get_db

class AIWorker:
    def __init__(self):
        self.kg_engine = KnowledgeGraphIndexEngine()

    async def process_document(self, document_text: str, doc_id: str):
        # 1. Ingest into knowledge graph
        async with get_db() as db:
            result = await self.kg_engine.ingest_document(
                db=db,
                document_id=doc_id,
                content=document_text
            )

        # 2. Use for RAG-based question answering
        async with get_db() as db:
            context = await self.kg_engine.query_knowledge_graph(
                db=db,
                query="Summarize the main topics",
                top_k=3
            )

        # 3. Build your response using the context
        relevant_chunks = [c['content'] for c in context['chunks']]
        return self.generate_response(relevant_chunks)
```

#### 5. Query Engine Options

LlamaIndex's KnowledgeGraphQueryEngine supports various modes:

```python
from llama_index.core.query_engine import KnowledgeGraphQueryEngine

# After getting the kg_index from cache
kg_index = kg_engine._index_cache[document_id]

# Option 1: Default query engine
query_engine = kg_index.as_query_engine()

# Option 2: With custom retrieval settings
query_engine = kg_index.as_query_engine(
    retriever_mode="keyword",  # "keyword", "embedding", or "hybrid"
    include_text=True,
    response_mode="compact",  # "refine", "compact", "tree_summarize"
    verbose=True
)

# Option 3: Knowledge Graph RAG (combines graph + vector search)
from llama_index.core.indices.knowledge_graph import KGTableRetriever

retriever = KGTableRetriever(
    index=kg_index,
    query_keyword_extract_template=custom_template,  # Optional
    max_keywords_per_query=10
)
```

### Key Points

1. **LlamaIndex Integration**: The engine uses `KnowledgeGraphIndex` from LlamaIndex, giving you access to all LlamaIndex features
2. **Index Caching**: Indexes are cached in `kg_engine._index_cache[document_id]` for efficient reuse
3. **Graph Store Access**: Direct access to triplets via `kg_engine.graph_store`
4. **Async/Await**: All database operations are async - use `async with get_db()`
5. **Query Modes**: LlamaIndex supports multiple query modes (keyword, embedding, hybrid)

### Example: Building a RAG Application

```python
from indexes.knowledge_graph_index import KnowledgeGraphIndexEngine
from database import get_db
from llama_index.core import Settings
from llama_index.llms.openrouter import OpenRouter

# Configure LlamaIndex globally
Settings.llm = OpenRouter(api_key="your-key", model="deepseek/deepseek-chat-v3.1:free")

kg_engine = KnowledgeGraphIndexEngine()

async def ask_question(question: str, document_id: str):
    """Ask a question about a specific document using knowledge graph."""

    # Get the cached index
    if document_id in kg_engine._index_cache:
        kg_index = kg_engine._index_cache[document_id]

        # Create query engine
        query_engine = kg_index.as_query_engine(
            include_text=True,
            response_mode="tree_summarize"
        )

        # Get response
        response = query_engine.query(question)

        return {
            "answer": response.response,
            "sources": [
                {"text": node.text, "score": node.score}
                for node in response.source_nodes
            ]
        }
    else:
        # Fallback to database query
        async with get_db() as db:
            return await kg_engine.query_knowledge_graph(
                db=db,
                query=question,
                top_k=5
            )
```

## Future Enhancements

This is the basic implementation of the knowledge graph index. Future versions will include:

- Vector index (using pgvector for efficient similarity search)
- Hybrid search (combining semantic and keyword search)
- Graph analytics (PageRank, community detection)
- Multi-modal support (images, PDFs)
- Incremental updates
- Caching layer

## API Documentation

Once the service is running, visit:
- Swagger UI: `http://localhost:8002/docs`
- ReDoc: `http://localhost:8002/redoc`
