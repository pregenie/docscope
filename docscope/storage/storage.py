"""Main storage interface for DocScope"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from .database import DatabaseManager
from .repository import DocumentRepository, CategoryRepository, TagRepository
from .models import DocumentModel
from ..core.models import Document, ScanResult, DocumentStatus
from ..core.config import StorageConfig
from ..core.logging import get_logger
from ..core.exceptions import StorageError, NotFoundError

logger = get_logger(__name__)


class DocumentStore:
    """High-level storage interface for documents"""
    
    def __init__(self, config: StorageConfig):
        """Initialize document store
        
        Args:
            config: Storage configuration
        """
        self.config = config
        self.db_manager = DatabaseManager(config)
        self._initialized = False
        
    def initialize(self, drop_existing: bool = False) -> None:
        """Initialize storage backend
        
        Args:
            drop_existing: Whether to drop existing data
        """
        try:
            self.db_manager.initialize(drop_existing=drop_existing)
            self._initialized = True
            logger.info("Document store initialized")
        except Exception as e:
            logger.error(f"Failed to initialize document store: {e}")
            raise StorageError(f"Storage initialization failed: {e}")
    
    def store_document(self, doc: Document) -> str:
        """Store a document
        
        Args:
            doc: Document to store
            
        Returns:
            Document ID
        """
        if not self._initialized:
            self.initialize()
        
        try:
            with self.db_manager.session_scope() as session:
                repo = DocumentRepository(session)
                
                # Check if document already exists
                existing = repo.get_by_path(doc.path)
                if existing:
                    # Update existing document
                    updates = {
                        'title': doc.title,
                        'content': doc.content,
                        'content_hash': doc.content_hash,
                        'format': doc.format.value,
                        'size': doc.size,
                        'modified_at': doc.modified_at,
                        'indexed_at': doc.indexed_at,
                        'metadata': doc.metadata,
                        'status': doc.status.value,
                        'error': doc.error
                    }
                    repo.update(existing.id, updates)
                    logger.debug(f"Updated document: {doc.path}")
                    return existing.id
                else:
                    # Create new document
                    db_doc = repo.create(doc)
                    logger.debug(f"Stored new document: {doc.path}")
                    return db_doc.id
                    
        except Exception as e:
            logger.error(f"Failed to store document {doc.path}: {e}")
            raise StorageError(f"Failed to store document: {e}")
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Retrieve a document by ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document if found, None otherwise
        """
        if not self._initialized:
            self.initialize()
        
        try:
            with self.db_manager.session_scope() as session:
                repo = DocumentRepository(session)
                db_doc = repo.get(doc_id)
                
                if db_doc:
                    return self._model_to_document(db_doc)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            raise StorageError(f"Failed to get document: {e}")
    
    def get_document_by_path(self, path: str) -> Optional[Document]:
        """Retrieve a document by file path
        
        Args:
            path: File path
            
        Returns:
            Document if found, None otherwise
        """
        if not self._initialized:
            self.initialize()
        
        try:
            with self.db_manager.session_scope() as session:
                repo = DocumentRepository(session)
                db_doc = repo.get_by_path(path)
                
                if db_doc:
                    return self._model_to_document(db_doc)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get document by path {path}: {e}")
            raise StorageError(f"Failed to get document: {e}")
    
    def update_document(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """Update a document
        
        Args:
            doc_id: Document ID
            updates: Dictionary of updates
            
        Returns:
            True if updated, False if not found
        """
        if not self._initialized:
            self.initialize()
        
        try:
            with self.db_manager.session_scope() as session:
                repo = DocumentRepository(session)
                result = repo.update(doc_id, updates)
                return result is not None
                
        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {e}")
            raise StorageError(f"Failed to update document: {e}")
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if deleted, False if not found
        """
        if not self._initialized:
            self.initialize()
        
        try:
            with self.db_manager.session_scope() as session:
                repo = DocumentRepository(session)
                return repo.delete(doc_id)
                
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise StorageError(f"Failed to delete document: {e}")
    
    def store_scan_result(self, result: ScanResult) -> int:
        """Store documents from a scan result
        
        Args:
            result: Scan result with documents
            
        Returns:
            Number of documents stored
        """
        if not self._initialized:
            self.initialize()
        
        stored = 0
        for doc in result.documents:
            try:
                self.store_document(doc)
                stored += 1
            except Exception as e:
                logger.error(f"Failed to store document {doc.path}: {e}")
        
        logger.info(f"Stored {stored} documents from scan result")
        return stored
    
    def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        format: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = 'modified_at',
        sort_order: str = 'desc'
    ) -> List[Document]:
        """List documents with filters
        
        Args:
            limit: Maximum number of documents
            offset: Number of documents to skip
            format: Filter by format
            status: Filter by status
            category: Filter by category
            tags: Filter by tags
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            
        Returns:
            List of documents
        """
        if not self._initialized:
            self.initialize()
        
        try:
            with self.db_manager.session_scope() as session:
                repo = DocumentRepository(session)
                db_docs = repo.list(
                    limit=limit,
                    offset=offset,
                    format=format,
                    status=status,
                    category=category,
                    tags=tags,
                    sort_by=sort_by,
                    sort_order=sort_order
                )
                
                return [self._model_to_document(d) for d in db_docs]
                
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise StorageError(f"Failed to list documents: {e}")
    
    def count_documents(
        self,
        format: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None
    ) -> int:
        """Count documents with filters
        
        Args:
            format: Filter by format
            status: Filter by status
            category: Filter by category
            
        Returns:
            Document count
        """
        if not self._initialized:
            self.initialize()
        
        try:
            with self.db_manager.session_scope() as session:
                repo = DocumentRepository(session)
                return repo.count(format=format, status=status, category=category)
                
        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            raise StorageError(f"Failed to count documents: {e}")
    
    def find_duplicates(self) -> List[List[Document]]:
        """Find duplicate documents
        
        Returns:
            List of duplicate document groups
        """
        if not self._initialized:
            self.initialize()
        
        try:
            with self.db_manager.session_scope() as session:
                repo = DocumentRepository(session)
                duplicate_groups = repo.find_duplicates()
                
                result = []
                for group in duplicate_groups:
                    docs = [self._model_to_document(d) for d in group]
                    result.append(docs)
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to find duplicates: {e}")
            raise StorageError(f"Failed to find duplicates: {e}")
    
    def get_modified_since(self, since: datetime) -> List[Document]:
        """Get documents modified since a timestamp
        
        Args:
            since: Timestamp to filter from
            
        Returns:
            List of modified documents
        """
        if not self._initialized:
            self.initialize()
        
        try:
            with self.db_manager.session_scope() as session:
                repo = DocumentRepository(session)
                db_docs = repo.get_modified_since(since)
                return [self._model_to_document(d) for d in db_docs]
                
        except Exception as e:
            logger.error(f"Failed to get modified documents: {e}")
            raise StorageError(f"Failed to get modified documents: {e}")
    
    def create_category(self, name: str, parent_id: Optional[str] = None, **kwargs) -> str:
        """Create a category
        
        Args:
            name: Category name
            parent_id: Parent category ID
            **kwargs: Additional fields
            
        Returns:
            Category ID
        """
        if not self._initialized:
            self.initialize()
        
        try:
            with self.db_manager.session_scope() as session:
                repo = CategoryRepository(session)
                category = repo.create(name, parent_id, **kwargs)
                return category.id
                
        except Exception as e:
            logger.error(f"Failed to create category {name}: {e}")
            raise StorageError(f"Failed to create category: {e}")
    
    def list_categories(self, parent_id: Optional[str] = None) -> List[Dict]:
        """List categories
        
        Args:
            parent_id: Filter by parent ID
            
        Returns:
            List of category dictionaries
        """
        if not self._initialized:
            self.initialize()
        
        try:
            with self.db_manager.session_scope() as session:
                repo = CategoryRepository(session)
                categories = repo.list(parent_id)
                return [cat.to_dict() for cat in categories]
                
        except Exception as e:
            logger.error(f"Failed to list categories: {e}")
            raise StorageError(f"Failed to list categories: {e}")
    
    def create_tag(self, name: str, **kwargs) -> str:
        """Create a tag
        
        Args:
            name: Tag name
            **kwargs: Additional fields
            
        Returns:
            Tag ID
        """
        if not self._initialized:
            self.initialize()
        
        try:
            with self.db_manager.session_scope() as session:
                repo = TagRepository(session)
                tag = repo.get_or_create(name, **kwargs)
                return tag.id
                
        except Exception as e:
            logger.error(f"Failed to create tag {name}: {e}")
            raise StorageError(f"Failed to create tag: {e}")
    
    def list_tags(self, limit: int = 100) -> List[Dict]:
        """List tags
        
        Args:
            limit: Maximum number of tags
            
        Returns:
            List of tag dictionaries
        """
        if not self._initialized:
            self.initialize()
        
        try:
            with self.db_manager.session_scope() as session:
                repo = TagRepository(session)
                tags = repo.list(limit)
                return [tag.to_dict() for tag in tags]
                
        except Exception as e:
            logger.error(f"Failed to list tags: {e}")
            raise StorageError(f"Failed to list tags: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics
        
        Returns:
            Dictionary with statistics
        """
        stats = self.db_manager.get_stats()
        
        # Add format breakdown
        if self._initialized:
            try:
                with self.db_manager.session_scope() as session:
                    from .models import DocumentModel
                    from sqlalchemy import func
                    
                    format_counts = session.query(
                        DocumentModel.format,
                        func.count(DocumentModel.id)
                    ).group_by(DocumentModel.format).all()
                    
                    stats['formats'] = dict(format_counts)
            except:
                pass
        
        return stats
    
    def vacuum(self) -> None:
        """Optimize database"""
        self.db_manager.vacuum()
    
    def backup(self, backup_path: str) -> None:
        """Backup database
        
        Args:
            backup_path: Path to backup file
        """
        self.db_manager.backup(backup_path)
    
    def close(self) -> None:
        """Close storage connections"""
        self.db_manager.close()
        self._initialized = False
    
    def _model_to_document(self, model: DocumentModel) -> Document:
        """Convert database model to Document object
        
        Args:
            model: Database model
            
        Returns:
            Document object
        """
        from ..core.models import DocumentFormat, DocumentStatus
        
        return Document(
            id=model.id,
            path=model.path,
            title=model.title,
            content=model.content or "",
            format=DocumentFormat(model.format),
            size=model.size,
            content_hash=model.content_hash,
            created_at=model.created_at,
            modified_at=model.modified_at,
            indexed_at=model.indexed_at,
            category=model.categories[0].name if model.categories else None,
            tags=[tag.name for tag in model.tags],
            metadata=model.metadata or {},
            status=DocumentStatus(model.status) if model.status else DocumentStatus.PENDING,
            error=model.error
        )