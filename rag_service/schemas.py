"""Pydantic schemas for API requests and responses."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentIngestRequest(BaseModel):
    """Request schema for document ingestion."""

    document_id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Raw document content")
    title: Optional[str] = Field(None, description="Document title")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class DocumentIngestResponse(BaseModel):
    """Response schema for document ingestion."""

    document_id: str
    chunks_created: int
    entities_created: int
    relations_created: int
    duration_seconds: float
    status: str


class QueryRequest(BaseModel):
    """Request schema for knowledge graph query."""

    query: str = Field(..., description="Search query")
    top_k: int = Field(5, ge=1, le=50, description="Number of results to return")
    include_relations: bool = Field(True, description="Include related entities")


class ChunkResult(BaseModel):
    """Chunk result in query response."""

    chunk_id: str
    content: str
    score: float
    document_id: Optional[str]


class EntityResult(BaseModel):
    """Entity result in query response."""

    entity_id: str
    text: str
    type: str
    metadata: Dict[str, Any]


class RelationResult(BaseModel):
    """Relation result in query response."""

    relation_id: str
    source: Optional[str]
    target: Optional[str]
    type: str
    confidence: float


class QueryResponse(BaseModel):
    """Response schema for knowledge graph query."""

    query: str
    chunks: List[ChunkResult]
    entities: List[EntityResult]
    relations: List[RelationResult]


class DocumentGraphResponse(BaseModel):
    """Response schema for document graph."""

    document_id: str
    title: Optional[str]
    metadata: Dict[str, Any]
    entities: List[Dict[str, Any]]
    relations: List[Dict[str, Any]]
    chunks_count: int


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime
    service: str
