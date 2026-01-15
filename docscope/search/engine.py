"""Main search engine implementation"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import time

from whoosh.searching import Searcher, ResultsPage
from whoosh.qparser import QueryParser as WhooshQueryParser
from whoosh.query import Every

from .indexer import DocumentIndexer
from .query_parser import QueryParser
from .ranker import SearchRanker
from .suggestions import SearchSuggestions
from .schema import create_document_schema
from ..core.models import SearchResults, SearchResult, DocumentFormat
from ..core.logging import get_logger
from ..core.exceptions import SearchError

logger = get_logger(__name__)


class SearchEngine:
    """Main search engine with full-text search capabilities"""
    
    def __init__(self, index_dir: str = "~/.docscope/search_index"):
        """Initialize search engine
        
        Args:
            index_dir: Directory for search index
        """
        self.index_dir = Path(os.path.expanduser(index_dir))
        self.indexer = DocumentIndexer(index_dir)
        self.schema = create_document_schema()
        self.query_parser = QueryParser(self.schema)
        self.ranker = SearchRanker()
        self.suggestions = SearchSuggestions(
            self.indexer.suggestion_index,
            self.indexer.doc_index
        )
        
        # Search configuration
        self.default_limit = 20
        self.max_limit = 100
        self.snippet_length = 200
    
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: Optional[str] = None,
        facets: bool = True,
        highlight: bool = True
    ) -> SearchResults:
        """Execute a search query
        
        Args:
            query: Search query string
            filters: Additional filters
            limit: Maximum results to return
            offset: Number of results to skip
            sort_by: Field to sort by
            facets: Whether to include facets
            highlight: Whether to highlight matches
            
        Returns:
            SearchResults object
        """
        start_time = time.time()
        
        try:
            # Parse query
            parsed_query = self.query_parser.parse(query)
            
            # Apply filters
            if filters:
                filter_query = self.query_parser.build_filter_query(filters)
                if filter_query:
                    from whoosh.query import And
                    parsed_query = And([parsed_query, filter_query])
            
            # Execute search
            with self.indexer.doc_index.searcher() as searcher:
                # Determine sorting
                sortedby = self._get_sort_field(sort_by)
                
                # Search with pagination
                results_page = searcher.search_page(
                    parsed_query,
                    pagenum=(offset // limit) + 1,
                    pagelen=min(limit, self.max_limit),
                    sortedby=sortedby,
                    reverse=(sort_by and sort_by.startswith('-'))
                )
                
                # Process results
                search_results = self._process_results(
                    results_page,
                    query,
                    highlight
                )
                
                # Get facets if requested
                if facets:
                    facet_fields = self.query_parser.extract_facets(query)
                    search_results.facets = self._get_facets(
                        searcher,
                        parsed_query,
                        facet_fields
                    )
                
                # Get suggestions
                search_results.suggestions = self._get_search_suggestions(
                    query,
                    results_page.total
                )
            
            # Record search for suggestions
            self.suggestions.record_search(query)
            
            # Set metadata
            search_results.query = query
            search_results.total = results_page.total
            search_results.duration = time.time() - start_time
            
            logger.info(
                f"Search '{query}' returned {results_page.total} results "
                f"in {search_results.duration:.3f}s"
            )
            
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed for '{query}': {e}")
            raise SearchError(f"Search failed: {e}")
    
    def search_similar(
        self,
        doc_id: str,
        limit: int = 10
    ) -> SearchResults:
        """Find similar documents
        
        Args:
            doc_id: Document ID to find similar to
            limit: Maximum results
            
        Returns:
            SearchResults with similar documents
        """
        start_time = time.time()
        
        try:
            with self.indexer.doc_index.searcher() as searcher:
                # Get the original document
                results = searcher.search(Term("id", doc_id), limit=1)
                if not results:
                    return SearchResults(
                        query=f"similar:{doc_id}",
                        results=[],
                        total=0,
                        duration=time.time() - start_time
                    )
                
                original = results[0]
                
                # Use more_like_this
                similar_docs = original.more_like_this("content", top=limit)
                
                # Process results
                search_results = self._process_results(similar_docs, f"similar:{doc_id}", False)
                search_results.query = f"similar:{doc_id}"
                search_results.total = len(similar_docs)
                search_results.duration = time.time() - start_time
                
                return search_results
                
        except Exception as e:
            logger.error(f"Similar search failed for '{doc_id}': {e}")
            raise SearchError(f"Similar search failed: {e}")
    
    def get_suggestions(
        self,
        partial_query: str,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Get search suggestions
        
        Args:
            partial_query: Partial query string
            limit: Maximum suggestions
            
        Returns:
            List of suggestions
        """
        return self.suggestions.get_suggestions(partial_query, limit)
    
    def index_documents(
        self,
        documents: List,
        batch_size: int = 100
    ) -> int:
        """Index multiple documents
        
        Args:
            documents: List of documents to index
            batch_size: Batch size for indexing
            
        Returns:
            Number of documents indexed
        """
        return self.indexer.index_documents(documents, batch_size)
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from index
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if deleted
        """
        return self.indexer.delete_document(doc_id)
    
    def clear_index(self):
        """Clear all documents from index"""
        self.indexer.clear_index()
    
    def optimize_index(self):
        """Optimize search index"""
        self.indexer.optimize_index()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics
        
        Returns:
            Dictionary with statistics
        """
        stats = self.indexer.get_index_stats()
        stats['search_suggestions'] = len(self.suggestions._get_popular_suggestions(100))
        return stats
    
    def _process_results(
        self,
        results: ResultsPage,
        query: str,
        highlight: bool
    ) -> SearchResults:
        """Process search results into SearchResults object
        
        Args:
            results: Whoosh results
            query: Original query
            highlight: Whether to highlight
            
        Returns:
            SearchResults object
        """
        search_results = SearchResults(
            query=query,
            results=[],
            total=0
        )
        
        for hit in results:
            # Create SearchResult object
            result = SearchResult(
                document_id=hit['id'],
                title=hit.get('title', ''),
                path=hit.get('path', ''),
                score=hit.score,
                snippet=hit.get('snippet', ''),
                format=DocumentFormat(hit.get('format', 'unknown')),
                category=hit.get('category'),
                tags=hit.get('tags', '').split(',') if hit.get('tags') else [],
                metadata={}
            )
            
            # Add highlights if requested
            if highlight and hasattr(hit, 'highlights'):
                result.highlights = list(hit.highlights("content"))
            
            search_results.results.append(result)
        
        return search_results
    
    def _get_facets(
        self,
        searcher: Searcher,
        query,
        facet_fields: List[str]
    ) -> Dict[str, Dict[str, int]]:
        """Get facets for search results
        
        Args:
            searcher: Whoosh searcher
            query: Search query
            facet_fields: Fields to facet on
            
        Returns:
            Dictionary of facets
        """
        facets = {}
        
        try:
            for field in facet_fields:
                if field in self.schema.names():
                    # Get facet counts
                    field_facets = searcher.facets(field, query)
                    if field_facets:
                        facets[field] = dict(field_facets)
        except Exception as e:
            logger.warning(f"Failed to get facets: {e}")
        
        return facets
    
    def _get_search_suggestions(
        self,
        query: str,
        result_count: int
    ) -> List[str]:
        """Get search suggestions based on results
        
        Args:
            query: Original query
            result_count: Number of results found
            
        Returns:
            List of suggested queries
        """
        suggestions = []
        
        # If no results, suggest alternatives
        if result_count == 0:
            # Try fuzzy search
            suggestions.append(f"~{query}~")
            
            # Try without quotes
            if '"' in query:
                suggestions.append(query.replace('"', ''))
            
            # Try broader search
            if ' AND ' in query:
                suggestions.append(query.replace(' AND ', ' OR '))
        
        # If too many results, suggest refinements
        elif result_count > 100:
            # Suggest adding filters
            suggestions.append(f'{query} format:markdown')
            suggestions.append(f'"{query}"')  # Exact phrase
        
        return suggestions[:5]
    
    def _get_sort_field(self, sort_by: Optional[str]) -> Optional[str]:
        """Get the field to sort by
        
        Args:
            sort_by: Sort specification
            
        Returns:
            Field name for sorting
        """
        if not sort_by:
            return None
        
        # Remove direction indicator
        if sort_by.startswith('-'):
            field = sort_by[1:]
        else:
            field = sort_by
        
        # Map common sort fields
        sort_map = {
            'relevance': None,  # Default scoring
            'date': 'modified_at',
            'created': 'created_at',
            'modified': 'modified_at',
            'size': 'size',
            'title': 'title',
        }
        
        return sort_map.get(field, field)