"""SQLAlchemy database models"""

from datetime import datetime
from typing import List, Optional
import json

from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Float, 
    ForeignKey, Table, Boolean, Index, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

Base = declarative_base()

# Many-to-many association tables
document_tags = Table(
    'document_tags',
    Base.metadata,
    Column('document_id', String, ForeignKey('documents.id', ondelete='CASCADE')),
    Column('tag_id', String, ForeignKey('tags.id', ondelete='CASCADE')),
    Index('ix_document_tags', 'document_id', 'tag_id')
)

document_categories = Table(
    'document_categories',
    Base.metadata,
    Column('document_id', String, ForeignKey('documents.id', ondelete='CASCADE')),
    Column('category_id', String, ForeignKey('categories.id', ondelete='CASCADE')),
    Index('ix_document_categories', 'document_id', 'category_id')
)


class DocumentModel(Base):
    """Document database model"""
    __tablename__ = 'documents'
    
    id = Column(String, primary_key=True)
    path = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False, index=True)
    content = Column(Text)
    content_hash = Column(String, index=True)
    format = Column(String, index=True)
    size = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    modified_at = Column(DateTime, default=func.now(), onupdate=func.now())
    indexed_at = Column(DateTime, index=True)
    accessed_at = Column(DateTime)
    
    # Metadata stored as JSON
    doc_metadata = Column(JSON)
    
    # Status and error tracking
    status = Column(String, default='pending', index=True)
    error = Column(Text)
    
    # Search optimization
    search_vector = Column(Text)  # For full-text search
    score = Column(Float, default=0.0)
    
    # Relationships
    tags = relationship('TagModel', secondary=document_tags, back_populates='documents')
    categories = relationship('CategoryModel', secondary=document_categories, back_populates='documents')
    
    # Indexes
    __table_args__ = (
        Index('ix_documents_modified', 'modified_at'),
        Index('ix_documents_format_status', 'format', 'status'),
        Index('ix_documents_path_hash', 'path', 'content_hash'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'path': self.path,
            'title': self.title,
            'content': self.content,
            'content_hash': self.content_hash,
            'format': self.format,
            'size': self.size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'indexed_at': self.indexed_at.isoformat() if self.indexed_at else None,
            'metadata': self.doc_metadata,
            'status': self.status,
            'error': self.error,
            'tags': [tag.name for tag in self.tags],
            'categories': [cat.name for cat in self.categories],
        }
    
    def __repr__(self):
        return f"<Document(id={self.id}, title={self.title})>"


class CategoryModel(Base):
    """Category database model"""
    __tablename__ = 'categories'
    
    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    parent_id = Column(String, ForeignKey('categories.id', ondelete='CASCADE'))
    description = Column(Text)
    color = Column(String)
    icon = Column(String)
    order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    parent = relationship('CategoryModel', remote_side=[id], backref='children')
    documents = relationship('DocumentModel', secondary=document_categories, back_populates='categories')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'order': self.order,
            'document_count': len(self.documents),
            'children': [child.to_dict() for child in self.children],
        }
    
    def get_path(self):
        """Get full category path"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return '/'.join(path)
    
    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name})>"


class TagModel(Base):
    """Tag database model"""
    __tablename__ = 'tags'
    
    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    color = Column(String)
    description = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    
    # Relationships
    documents = relationship('DocumentModel', secondary=document_tags, back_populates='tags')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'description': self.description,
            'document_count': len(self.documents),
            'usage_count': self.usage_count,
        }
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name})>"


class SearchHistoryModel(Base):
    """Search history for analytics and suggestions"""
    __tablename__ = 'search_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String, nullable=False, index=True)
    results_count = Column(Integer)
    execution_time = Column(Float)
    
    # User tracking (for future multi-user support)
    user_id = Column(String)
    session_id = Column(String)
    
    # Timestamp
    searched_at = Column(DateTime, default=func.now(), index=True)
    
    # Indexes
    __table_args__ = (
        Index('ix_search_history_query_time', 'query', 'searched_at'),
    )
    
    def __repr__(self):
        return f"<SearchHistory(query={self.query}, results={self.results_count})>"