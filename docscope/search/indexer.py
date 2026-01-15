"""Document indexer for search engine"""

import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import shutil

from whoosh.index import create_in, open_dir, exists_in
from whoosh.writing import AsyncWriter
import whoosh.index as index

from .schema import create_document_schema, create_suggestion_schema, FIELD_CONFIGS
from ..core.models import Document, DocumentFormat
from ..core.logging import get_logger
from ..core.exceptions import SearchError

logger = get_logger(__name__)


class DocumentIndexer:
    """Indexes documents for full-text search"""
    
    def __init__(self, index_dir: str = "~/.docscope/search_index"):
        """Initialize document indexer
        
        Args:
            index_dir: Directory to store search index
        """
        self.index_dir = Path(os.path.expanduser(index_dir))
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.doc_index_path = self.index_dir / "documents"
        self.suggestion_index_path = self.index_dir / "suggestions"
        
        self.doc_index = None
        self.suggestion_index = None
        self._initialize_indexes()
    
    def _initialize_indexes(self):
        """Initialize or open existing indexes"""
        # Initialize document index
        if not self.doc_index_path.exists():
            self.doc_index_path.mkdir(parents=True)
            self.doc_index = create_in(str(self.doc_index_path), create_document_schema())
            logger.info(f"Created new document index at {self.doc_index_path}")
        else:
            try:
                self.doc_index = open_dir(str(self.doc_index_path))
                logger.info(f"Opened existing document index at {self.doc_index_path}")
            except Exception as e:
                logger.error(f"Failed to open index, recreating: {e}")
                shutil.rmtree(self.doc_index_path)
                self.doc_index_path.mkdir(parents=True)
                self.doc_index = create_in(str(self.doc_index_path), create_document_schema())
        
        # Initialize suggestion index
        if not self.suggestion_index_path.exists():
            self.suggestion_index_path.mkdir(parents=True)
            self.suggestion_index = create_in(
                str(self.suggestion_index_path), 
                create_suggestion_schema()
            )
        else:
            try:
                self.suggestion_index = open_dir(str(self.suggestion_index_path))
            except:
                shutil.rmtree(self.suggestion_index_path)
                self.suggestion_index_path.mkdir(parents=True)
                self.suggestion_index = create_in(
                    str(self.suggestion_index_path),
                    create_suggestion_schema()
                )
    
    def index_document(self, doc: Document, update: bool = True) -> None:
        """Index a single document
        
        Args:
            doc: Document to index
            update: Whether to update if document already exists
        """
        try:
            writer = self.doc_index.writer()
            
            # Prepare document data
            doc_data = self._prepare_document_data(doc)
            
            if update:
                # Update existing document
                writer.update_document(**doc_data)
            else:
                # Add new document
                writer.add_document(**doc_data)
            
            writer.commit()
            logger.debug(f"Indexed document: {doc.id}")
            
            # Update suggestions
            self._update_suggestions(doc)
            
        except Exception as e:
            logger.error(f"Failed to index document {doc.id}: {e}")
            raise SearchError(f"Indexing failed: {e}")
    
    def index_documents(self, documents: List[Document], batch_size: int = 100) -> int:
        """Index multiple documents in batch
        
        Args:
            documents: List of documents to index
            batch_size: Number of documents to index per batch
            
        Returns:
            Number of documents indexed
        """
        indexed = 0
        
        try:
            # Use AsyncWriter for better performance
            writer = AsyncWriter(self.doc_index)
            
            for i, doc in enumerate(documents):
                try:
                    doc_data = self._prepare_document_data(doc)
                    writer.update_document(**doc_data)
                    indexed += 1
                    
                    if (i + 1) % batch_size == 0:
                        writer.commit()
                        writer = AsyncWriter(self.doc_index)
                        logger.info(f"Indexed {i + 1} documents")
                        
                except Exception as e:
                    logger.error(f"Failed to index document {doc.id}: {e}")
            
            writer.commit()
            logger.info(f"Indexed {indexed} documents total")
            
            # Update suggestions for all documents
            self._update_suggestions_batch(documents)
            
        except Exception as e:
            logger.error(f"Batch indexing failed: {e}")
            raise SearchError(f"Batch indexing failed: {e}")
        
        return indexed
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the index
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            writer = self.doc_index.writer()
            deleted = writer.delete_by_term('id', doc_id)
            writer.commit()
            
            if deleted:
                logger.debug(f"Deleted document from index: {doc_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False
    
    def clear_index(self) -> None:
        """Clear all documents from the index"""
        try:
            writer = self.doc_index.writer()
            writer.commit(mergetype=writer.CLEAR)
            logger.info("Cleared document index")
            
            # Clear suggestions too
            sug_writer = self.suggestion_index.writer()
            sug_writer.commit(mergetype=sug_writer.CLEAR)
            
        except Exception as e:
            logger.error(f"Failed to clear index: {e}")
            raise SearchError(f"Failed to clear index: {e}")
    
    def optimize_index(self) -> None:
        """Optimize the search index for better performance"""
        try:
            writer = self.doc_index.writer()
            writer.commit(optimize=True)
            logger.info("Optimized document index")
            
            # Optimize suggestions
            sug_writer = self.suggestion_index.writer()
            sug_writer.commit(optimize=True)
            
        except Exception as e:
            logger.error(f"Failed to optimize index: {e}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the search index
        
        Returns:
            Dictionary with index statistics
        """
        try:
            with self.doc_index.searcher() as searcher:
                stats = {
                    'total_documents': searcher.doc_count(),
                    'index_size_mb': self._get_index_size() / (1024 * 1024),
                    'fields': list(self.doc_index.schema.names()),
                    'last_modified': self._get_last_modified(),
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {}
    
    def _prepare_document_data(self, doc: Document) -> Dict[str, Any]:
        """Prepare document data for indexing
        
        Args:
            doc: Document to prepare
            
        Returns:
            Dictionary of field values for indexing
        """
        # Extract path components
        path_parts = Path(doc.path).parts
        
        # Prepare basic fields
        data = {
            'id': doc.id,
            'path': doc.path,
            'title': doc.title,
            'content': doc.content,
            'format': doc.format.value,
            'content_hash': doc.content_hash,
            'size': doc.size,
            'created_at': doc.created_at,
            'modified_at': doc.modified_at,
            'indexed_at': doc.indexed_at or datetime.now(),
            'status': doc.status.value,
            'path_components': ','.join(path_parts),
        }
        
        # Add category if present
        if doc.category:
            data['category'] = doc.category
        
        # Add tags if present
        if doc.tags:
            data['tags'] = ','.join(doc.tags)
        
        # Extract year and month for faceting
        if doc.created_at:
            data['year'] = doc.created_at.year
            data['month'] = doc.created_at.month
        
        # Add metadata as JSON
        if doc.metadata:
            data['metadata_json'] = json.dumps(doc.metadata)
            
            # Extract specific metadata fields based on format
            self._extract_format_specific_fields(doc, data)
        
        # Generate snippet
        data['snippet'] = self._generate_snippet(doc.content)
        
        return data
    
    def _extract_format_specific_fields(self, doc: Document, data: Dict[str, Any]):
        """Extract format-specific fields for better searching
        
        Args:
            doc: Document to extract from
            data: Data dictionary to update
        """
        format_config = FIELD_CONFIGS.get(doc.format.value, {})
        
        if doc.format == DocumentFormat.MARKDOWN and 'headers' in doc.metadata:
            # Extract headers as keywords
            headers = [h['text'] for h in doc.metadata.get('headers', [])]
            if headers:
                data['keywords'] = ','.join(headers[:20])
        
        elif doc.format == DocumentFormat.CODE and doc.metadata:
            # Extract functions and classes as keywords
            keywords = []
            keywords.extend(doc.metadata.get('functions', [])[:10])
            keywords.extend(doc.metadata.get('classes', [])[:10])
            if keywords:
                data['keywords'] = ','.join(keywords)
    
    def _generate_snippet(self, content: str, max_length: int = 200) -> str:
        """Generate a snippet from content
        
        Args:
            content: Full content
            max_length: Maximum snippet length
            
        Returns:
            Content snippet
        """
        if len(content) <= max_length:
            return content
        
        # Try to break at word boundary
        snippet = content[:max_length]
        last_space = snippet.rfind(' ')
        if last_space > max_length * 0.8:
            snippet = snippet[:last_space]
        
        return snippet + "..."
    
    def _update_suggestions(self, doc: Document):
        """Update search suggestions based on document
        
        Args:
            doc: Document to extract suggestions from
        """
        try:
            writer = self.suggestion_index.writer()
            
            # Add title as suggestion
            writer.update_document(
                term=doc.title.lower(),
                term_ngram=doc.title,
                frequency=1,
                type='title',
                last_used=datetime.now()
            )
            
            # Add tags as suggestions
            for tag in doc.tags:
                writer.update_document(
                    term=tag.lower(),
                    term_ngram=tag,
                    frequency=1,
                    type='tag',
                    last_used=datetime.now()
                )
            
            writer.commit()
            
        except Exception as e:
            logger.warning(f"Failed to update suggestions: {e}")
    
    def _update_suggestions_batch(self, documents: List[Document]):
        """Update suggestions for multiple documents
        
        Args:
            documents: Documents to process
        """
        try:
            writer = self.suggestion_index.writer()
            
            for doc in documents:
                # Add titles
                writer.update_document(
                    term=doc.title.lower(),
                    term_ngram=doc.title,
                    frequency=1,
                    type='title',
                    last_used=datetime.now()
                )
                
                # Add tags
                for tag in doc.tags:
                    writer.update_document(
                        term=tag.lower(),
                        term_ngram=tag,
                        frequency=1,
                        type='tag',
                        last_used=datetime.now()
                    )
            
            writer.commit()
            
        except Exception as e:
            logger.warning(f"Failed to update suggestions batch: {e}")
    
    def _get_index_size(self) -> int:
        """Get total size of index directory in bytes"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.index_dir):
            for filename in filenames:
                filepath = Path(dirpath) / filename
                if filepath.exists():
                    total_size += filepath.stat().st_size
        return total_size
    
    def _get_last_modified(self) -> Optional[datetime]:
        """Get last modification time of index"""
        try:
            # Check index files
            index_files = list(self.doc_index_path.glob('*'))
            if index_files:
                latest = max(f.stat().st_mtime for f in index_files)
                return datetime.fromtimestamp(latest)
        except:
            pass
        return None