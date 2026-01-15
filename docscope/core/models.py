"""Core data models for DocScope"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
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


@dataclass
class Document:
    """Document model"""
    id: str
    path: str
    title: str
    content: str
    format: DocumentFormat
    size: int
    content_hash: str
    created_at: datetime
    modified_at: datetime
    indexed_at: Optional[datetime] = None
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: DocumentStatus = DocumentStatus.PENDING
    error: Optional[str] = None
    
    @property
    def relative_path(self) -> str:
        """Get relative path from root"""
        return str(Path(self.path).relative_to(Path.cwd()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "path": self.path,
            "title": self.title,
            "content": self.content,
            "format": self.format.value,
            "size": self.size,
            "content_hash": self.content_hash,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
            "category": self.category,
            "tags": self.tags,
            "metadata": self.metadata,
            "status": self.status.value,
            "error": self.error,
        }


@dataclass
class ScanResult:
    """Results from document scanning"""
    total: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    documents: List[Document] = field(default_factory=list)
    errors: List[Dict[str, str]] = field(default_factory=list)
    duration: float = 0.0
    
    def add_document(self, doc: Document):
        """Add a document to results"""
        self.documents.append(doc)
        self.total += 1
        if doc.status == DocumentStatus.INDEXED:
            self.successful += 1
        elif doc.status == DocumentStatus.FAILED:
            self.failed += 1
    
    def add_error(self, path: str, error: str):
        """Add an error to results"""
        self.errors.append({"path": path, "error": error})
        self.failed += 1
        self.total += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total": self.total,
            "successful": self.successful,
            "failed": self.failed,
            "skipped": self.skipped,
            "document_count": len(self.documents),
            "errors": self.errors,
            "duration": self.duration,
        }


@dataclass
class SearchResult:
    """Search result item"""
    document_id: str
    title: str
    path: str
    score: float
    snippet: str
    format: DocumentFormat
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    highlights: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "document_id": self.document_id,
            "title": self.title,
            "path": self.path,
            "score": self.score,
            "snippet": self.snippet,
            "format": self.format.value,
            "category": self.category,
            "tags": self.tags,
            "metadata": self.metadata,
            "highlights": self.highlights,
        }


@dataclass
class SearchResults:
    """Collection of search results"""
    query: str
    results: List[SearchResult]
    total: int
    facets: Dict[str, Dict[str, int]] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    duration: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "total": self.total,
            "facets": self.facets,
            "suggestions": self.suggestions,
            "duration": self.duration,
        }


@dataclass
class Category:
    """Document category"""
    id: str
    name: str
    parent_id: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    document_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "color": self.color,
            "icon": self.icon,
            "document_count": self.document_count,
        }


@dataclass
class Tag:
    """Document tag"""
    id: str
    name: str
    color: Optional[str] = None
    document_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "document_count": self.document_count,
        }