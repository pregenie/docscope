"""Pydantic models for API request/response"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class DocumentFormat(str, Enum):
    """Document format types"""
    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    YAML = "yaml"
    CODE = "code"
    NOTEBOOK = "notebook"
    OFFICE = "office"
    UNKNOWN = "unknown"


class DocumentStatus(str, Enum):
    """Document status"""
    PENDING = "pending"
    INDEXED = "indexed"
    FAILED = "failed"
    UPDATED = "updated"
    DELETED = "deleted"


# Request Models

class DocumentCreate(BaseModel):
    """Request model for creating a document"""
    path: str
    title: str
    content: str
    format: DocumentFormat
    tags: Optional[List[str]] = []
    category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    
    class Config:
        schema_extra = {
            "example": {
                "path": "/docs/guide.md",
                "title": "Getting Started Guide",
                "content": "# Getting Started\n\nWelcome to DocScope!",
                "format": "markdown",
                "tags": ["guide", "documentation"],
                "category": "tutorials"
            }
        }


class DocumentUpdate(BaseModel):
    """Request model for updating a document"""
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    """Request model for search"""
    query: str = Field(..., min_length=1, max_length=500)
    filters: Optional[Dict[str, Any]] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: Optional[str] = None
    facets: bool = True
    highlight: bool = True
    
    class Config:
        schema_extra = {
            "example": {
                "query": "authentication",
                "filters": {"format": "markdown"},
                "limit": 10,
                "offset": 0,
                "facets": True,
                "highlight": True
            }
        }


class ScanRequest(BaseModel):
    """Request model for scanning documents"""
    paths: List[str]
    recursive: bool = True
    formats: Optional[List[str]] = None
    incremental: bool = False
    since: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "paths": ["/docs", "/README.md"],
                "recursive": True,
                "formats": ["md", "txt", "json"],
                "incremental": False
            }
        }


class CategoryCreate(BaseModel):
    """Request model for creating a category"""
    name: str = Field(..., min_length=1, max_length=100)
    parent_id: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class TagCreate(BaseModel):
    """Request model for creating a tag"""
    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = None
    description: Optional[str] = None


# Response Models

class DocumentResponse(BaseModel):
    """Response model for a document"""
    id: str
    path: str
    title: str
    content: str
    format: DocumentFormat
    size: int
    content_hash: str
    created_at: datetime
    modified_at: datetime
    indexed_at: Optional[datetime]
    category: Optional[str]
    tags: List[str]
    metadata: Dict[str, Any]
    status: DocumentStatus
    
    class Config:
        orm_mode = True


class DocumentListResponse(BaseModel):
    """Response model for document list"""
    items: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    pages: int


class SearchResultItem(BaseModel):
    """Search result item"""
    document_id: str
    title: str
    path: str
    score: float
    snippet: str
    format: DocumentFormat
    category: Optional[str]
    tags: List[str]
    highlights: Optional[List[str]] = []
    
    class Config:
        orm_mode = True


class SearchResponse(BaseModel):
    """Response model for search results"""
    query: str
    results: List[SearchResultItem]
    total: int
    facets: Optional[Dict[str, Dict[str, int]]]
    suggestions: Optional[List[str]]
    duration: float


class ScanResponse(BaseModel):
    """Response model for scan operation"""
    total: int
    successful: int
    failed: int
    skipped: int
    errors: List[Dict[str, str]]
    duration: float


class CategoryResponse(BaseModel):
    """Response model for a category"""
    id: str
    name: str
    parent_id: Optional[str]
    description: Optional[str]
    color: Optional[str]
    icon: Optional[str]
    document_count: int
    children: Optional[List['CategoryResponse']] = []
    
    class Config:
        orm_mode = True


class TagResponse(BaseModel):
    """Response model for a tag"""
    id: str
    name: str
    color: Optional[str]
    description: Optional[str]
    document_count: int
    usage_count: int
    
    class Config:
        orm_mode = True


class StatsResponse(BaseModel):
    """Response model for statistics"""
    documents: int
    categories: int
    tags: int
    index_size_mb: float
    database_size_mb: Optional[float]
    formats: Dict[str, int]
    last_scan: Optional[datetime]
    last_index_update: Optional[datetime]


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, bool]
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2024-01-15T10:30:00Z",
                "services": {
                    "database": True,
                    "search_index": True,
                    "scanner": True
                }
            }
        }


class ErrorResponse(BaseModel):
    """Response model for errors"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "error": "NotFound",
                "message": "Document not found",
                "details": {"id": "doc123"}
            }
        }


class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


# Update forward references
CategoryResponse.update_forward_refs()