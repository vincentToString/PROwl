"""FastAPI application for RAG service."""
import traceback
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from datetime import datetime

from database import init_db, get_db
from indexes.knowledge_graph_index import KnowledgeGraphIndexEngine
from schemas import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    QueryRequest,
    QueryResponse,
    DocumentGraphResponse,
    HealthResponse
)
from config import settings


# Initialize index engine
kg_index_engine = KnowledgeGraphIndexEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the application."""
    # Startup
    print("Initializing database...")
    await init_db()
    print("Database initialized successfully")

    yield

    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="PROwl RAG Service",
    description="RAG service with Knowledge Graph Index for document ingestion and querying",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        service="rag_service"
    )


@app.post(
    "/api/v1/kg-index/ingest",
    response_model=DocumentIngestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Knowledge Graph Index"]
)
async def ingest_document(
    request: DocumentIngestRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest a document into the knowledge graph index.

    This endpoint:
    1. Splits the document into chunks
    2. Extracts entities and relations using LLM
    3. Creates embeddings for semantic search
    4. Stores everything in PostgreSQL

    Args:
        request: Document ingestion request
        db: Database session

    Returns:
        Ingestion result with statistics
    """
    try:
        result = await kg_index_engine.ingest_document(
            db=db,
            document_id=request.document_id,
            content=request.content,
            title=request.title,
            metadata=request.metadata
        )
        return DocumentIngestResponse(**result)
    except Exception as e:
        print(f"ERROR in ingest_document: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {str(e)}"
        )


@app.post(
    "/api/v1/kg-index/query",
    response_model=QueryResponse,
    tags=["Knowledge Graph Index"]
)
async def query_knowledge_graph(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Query the knowledge graph.

    This endpoint searches for:
    1. Semantically similar chunks
    2. Matching entities
    3. Related entities and their relationships

    Args:
        request: Query request
        db: Database session

    Returns:
        Query results with chunks, entities, and relations
    """
    try:
        result = await kg_index_engine.query_knowledge_graph(
            db=db,
            query=request.query,
            top_k=request.top_k,
            include_relations=request.include_relations
        )
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query knowledge graph: {str(e)}"
        )


@app.get(
    "/api/v1/kg-index/document/{document_id}",
    response_model=DocumentGraphResponse,
    tags=["Knowledge Graph Index"]
)
async def get_document_graph(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the complete knowledge graph for a specific document.

    Args:
        document_id: Document identifier
        db: Database session

    Returns:
        Document graph with all entities and relations
    """
    try:
        result = await kg_index_engine.get_document_graph(
            db=db,
            document_id=document_id
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{document_id}' not found"
            )

        return DocumentGraphResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document graph: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=True
    )
