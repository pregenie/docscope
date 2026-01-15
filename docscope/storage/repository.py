"""Repository pattern for database operations"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc, func

from .models import DocumentModel, CategoryModel, TagModel, SearchHistoryModel
from ..core.models import Document, Category, Tag
from ..core.logging import get_logger

logger = get_logger(__name__)


class DocumentRepository:
    """Repository for document operations"""
    
    def __init__(self, session: Session):
        """Initialize repository with database session
        
        Args:
            session: Database session
        """
        self.session = session
    
    def create(self, document: Document) -> DocumentModel:
        """Create a new document
        
        Args:
            document: Document to create
            
        Returns:
            Created document model
        """
        db_doc = DocumentModel(
            id=document.id,
            path=document.path,
            title=document.title,
            content=document.content,
            content_hash=document.content_hash,
            format=document.format.value,
            size=document.size,
            created_at=document.created_at,
            modified_at=document.modified_at,
            indexed_at=document.indexed_at,
            doc_metadata=document.metadata,
            status=document.status.value,
            error=document.error
        )
        
        # Add tags if provided
        if document.tags:
            for tag_name in document.tags:
                tag = self.session.query(TagModel).filter_by(name=tag_name).first()
                if not tag:
                    tag = TagModel(id=str(uuid.uuid4()), name=tag_name)
                    self.session.add(tag)
                db_doc.tags.append(tag)
        
        self.session.add(db_doc)
        self.session.flush()
        
        logger.debug(f"Created document: {db_doc.id}")
        return db_doc
    
    def get(self, doc_id: str) -> Optional[DocumentModel]:
        """Get document by ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document model or None
        """
        return self.session.query(DocumentModel).filter_by(id=doc_id).first()
    
    def get_by_path(self, path: str) -> Optional[DocumentModel]:
        """Get document by file path
        
        Args:
            path: File path
            
        Returns:
            Document model or None
        """
        return self.session.query(DocumentModel).filter_by(path=path).first()
    
    def update(self, doc_id: str, updates: Dict[str, Any]) -> Optional[DocumentModel]:
        """Update a document
        
        Args:
            doc_id: Document ID
            updates: Dictionary of updates
            
        Returns:
            Updated document model or None
        """
        doc = self.get(doc_id)
        if not doc:
            return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(doc, key) and key not in ['id', 'created_at']:
                setattr(doc, key, value)
        
        doc.modified_at = datetime.now()
        self.session.flush()
        
        logger.debug(f"Updated document: {doc_id}")
        return doc
    
    def delete(self, doc_id: str) -> bool:
        """Delete a document
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if deleted, False if not found
        """
        doc = self.get(doc_id)
        if not doc:
            return False
        
        self.session.delete(doc)
        self.session.flush()
        
        logger.debug(f"Deleted document: {doc_id}")
        return True
    
    def list(
        self,
        limit: int = 100,
        offset: int = 0,
        format: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = 'modified_at',
        sort_order: str = 'desc'
    ) -> List[DocumentModel]:
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
            List of document models
        """
        query = self.session.query(DocumentModel)
        
        # Apply filters
        if format:
            query = query.filter(DocumentModel.format == format)
        if status:
            query = query.filter(DocumentModel.status == status)
        if category:
            query = query.join(DocumentModel.categories).filter(
                CategoryModel.name == category
            )
        if tags:
            for tag in tags:
                query = query.join(DocumentModel.tags).filter(
                    TagModel.name == tag
                )
        
        # Apply sorting
        order_func = desc if sort_order == 'desc' else asc
        if hasattr(DocumentModel, sort_by):
            query = query.order_by(order_func(getattr(DocumentModel, sort_by)))
        
        # Apply pagination
        return query.offset(offset).limit(limit).all()
    
    def count(
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
        query = self.session.query(func.count(DocumentModel.id))
        
        if format:
            query = query.filter(DocumentModel.format == format)
        if status:
            query = query.filter(DocumentModel.status == status)
        if category:
            query = query.join(DocumentModel.categories).filter(
                CategoryModel.name == category
            )
        
        return query.scalar()
    
    def find_duplicates(self) -> List[List[DocumentModel]]:
        """Find duplicate documents by content hash
        
        Returns:
            List of duplicate document groups
        """
        # Find content hashes with more than one document
        duplicates = self.session.query(
            DocumentModel.content_hash,
            func.count(DocumentModel.id).label('count')
        ).group_by(
            DocumentModel.content_hash
        ).having(
            func.count(DocumentModel.id) > 1
        ).all()
        
        result = []
        for hash_value, _ in duplicates:
            docs = self.session.query(DocumentModel).filter_by(
                content_hash=hash_value
            ).all()
            result.append(docs)
        
        return result
    
    def get_modified_since(self, since: datetime) -> List[DocumentModel]:
        """Get documents modified since a timestamp
        
        Args:
            since: Timestamp to filter from
            
        Returns:
            List of modified documents
        """
        return self.session.query(DocumentModel).filter(
            DocumentModel.modified_at > since
        ).all()
    
    def update_many(self, doc_ids: List[str], updates: Dict[str, Any]) -> int:
        """Update multiple documents
        
        Args:
            doc_ids: List of document IDs
            updates: Dictionary of updates
            
        Returns:
            Number of updated documents
        """
        count = self.session.query(DocumentModel).filter(
            DocumentModel.id.in_(doc_ids)
        ).update(updates, synchronize_session=False)
        
        self.session.flush()
        logger.debug(f"Updated {count} documents")
        return count
    
    def delete_many(self, doc_ids: List[str]) -> int:
        """Delete multiple documents
        
        Args:
            doc_ids: List of document IDs
            
        Returns:
            Number of deleted documents
        """
        count = self.session.query(DocumentModel).filter(
            DocumentModel.id.in_(doc_ids)
        ).delete(synchronize_session=False)
        
        self.session.flush()
        logger.debug(f"Deleted {count} documents")
        return count


class CategoryRepository:
    """Repository for category operations"""
    
    def __init__(self, session: Session):
        """Initialize repository with database session
        
        Args:
            session: Database session
        """
        self.session = session
    
    def create(self, name: str, parent_id: Optional[str] = None, **kwargs) -> CategoryModel:
        """Create a new category
        
        Args:
            name: Category name
            parent_id: Parent category ID
            **kwargs: Additional fields
            
        Returns:
            Created category model
        """
        category = CategoryModel(
            id=str(uuid.uuid4()),
            name=name,
            parent_id=parent_id,
            **kwargs
        )
        
        self.session.add(category)
        self.session.flush()
        
        logger.debug(f"Created category: {category.name}")
        return category
    
    def get(self, category_id: str) -> Optional[CategoryModel]:
        """Get category by ID
        
        Args:
            category_id: Category ID
            
        Returns:
            Category model or None
        """
        return self.session.query(CategoryModel).filter_by(id=category_id).first()
    
    def get_by_name(self, name: str) -> Optional[CategoryModel]:
        """Get category by name
        
        Args:
            name: Category name
            
        Returns:
            Category model or None
        """
        return self.session.query(CategoryModel).filter_by(name=name).first()
    
    def list(self, parent_id: Optional[str] = None) -> List[CategoryModel]:
        """List categories
        
        Args:
            parent_id: Filter by parent ID (None for root categories)
            
        Returns:
            List of category models
        """
        query = self.session.query(CategoryModel)
        
        if parent_id is None:
            query = query.filter(CategoryModel.parent_id.is_(None))
        else:
            query = query.filter_by(parent_id=parent_id)
        
        return query.order_by(CategoryModel.order, CategoryModel.name).all()
    
    def get_tree(self) -> List[CategoryModel]:
        """Get category tree structure
        
        Returns:
            List of root categories with children populated
        """
        return self.list(parent_id=None)
    
    def delete(self, category_id: str, reassign_to: Optional[str] = None) -> bool:
        """Delete a category
        
        Args:
            category_id: Category ID
            reassign_to: Category ID to reassign documents to
            
        Returns:
            True if deleted, False if not found
        """
        category = self.get(category_id)
        if not category:
            return False
        
        # Reassign documents if specified
        if reassign_to and category.documents:
            new_category = self.get(reassign_to)
            if new_category:
                for doc in category.documents:
                    doc.categories.remove(category)
                    if new_category not in doc.categories:
                        doc.categories.append(new_category)
        
        self.session.delete(category)
        self.session.flush()
        
        logger.debug(f"Deleted category: {category_id}")
        return True


class TagRepository:
    """Repository for tag operations"""
    
    def __init__(self, session: Session):
        """Initialize repository with database session
        
        Args:
            session: Database session
        """
        self.session = session
    
    def create(self, name: str, **kwargs) -> TagModel:
        """Create a new tag
        
        Args:
            name: Tag name
            **kwargs: Additional fields
            
        Returns:
            Created tag model
        """
        tag = TagModel(
            id=str(uuid.uuid4()),
            name=name,
            **kwargs
        )
        
        self.session.add(tag)
        self.session.flush()
        
        logger.debug(f"Created tag: {tag.name}")
        return tag
    
    def get(self, tag_id: str) -> Optional[TagModel]:
        """Get tag by ID
        
        Args:
            tag_id: Tag ID
            
        Returns:
            Tag model or None
        """
        return self.session.query(TagModel).filter_by(id=tag_id).first()
    
    def get_by_name(self, name: str) -> Optional[TagModel]:
        """Get tag by name
        
        Args:
            name: Tag name
            
        Returns:
            Tag model or None
        """
        return self.session.query(TagModel).filter_by(name=name).first()
    
    def get_or_create(self, name: str, **kwargs) -> TagModel:
        """Get existing tag or create new one
        
        Args:
            name: Tag name
            **kwargs: Additional fields for creation
            
        Returns:
            Tag model
        """
        tag = self.get_by_name(name)
        if not tag:
            tag = self.create(name, **kwargs)
        return tag
    
    def list(self, limit: int = 100, order_by: str = 'usage_count') -> List[TagModel]:
        """List tags
        
        Args:
            limit: Maximum number of tags
            order_by: Field to order by
            
        Returns:
            List of tag models
        """
        query = self.session.query(TagModel)
        
        if order_by == 'usage_count':
            query = query.order_by(desc(TagModel.usage_count))
        elif order_by == 'name':
            query = query.order_by(TagModel.name)
        else:
            query = query.order_by(desc(TagModel.created_at))
        
        return query.limit(limit).all()
    
    def get_popular(self, limit: int = 20) -> List[TagModel]:
        """Get most popular tags
        
        Args:
            limit: Maximum number of tags
            
        Returns:
            List of popular tags
        """
        return self.list(limit=limit, order_by='usage_count')
    
    def delete(self, tag_id: str) -> bool:
        """Delete a tag
        
        Args:
            tag_id: Tag ID
            
        Returns:
            True if deleted, False if not found
        """
        tag = self.get(tag_id)
        if not tag:
            return False
        
        self.session.delete(tag)
        self.session.flush()
        
        logger.debug(f"Deleted tag: {tag_id}")
        return True
    
    def merge(self, source_tag_id: str, target_tag_id: str) -> bool:
        """Merge one tag into another
        
        Args:
            source_tag_id: Source tag to merge from
            target_tag_id: Target tag to merge into
            
        Returns:
            True if merged, False if tags not found
        """
        source = self.get(source_tag_id)
        target = self.get(target_tag_id)
        
        if not source or not target:
            return False
        
        # Move all documents from source to target
        for doc in source.documents:
            if target not in doc.tags:
                doc.tags.append(target)
            doc.tags.remove(source)
        
        # Update usage count
        target.usage_count += source.usage_count
        
        # Delete source tag
        self.session.delete(source)
        self.session.flush()
        
        logger.debug(f"Merged tag {source_tag_id} into {target_tag_id}")
        return True