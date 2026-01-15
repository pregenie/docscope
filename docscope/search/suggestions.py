"""Search suggestions and autocomplete"""

from typing import List, Dict, Optional
from datetime import datetime
import re

from whoosh.qparser import QueryParser
from whoosh.query import Term, Prefix, FuzzyTerm, Or

from ..core.logging import get_logger

logger = get_logger(__name__)


class SearchSuggestions:
    """Provides search suggestions and autocomplete functionality"""
    
    def __init__(self, suggestion_index, doc_index):
        """Initialize search suggestions
        
        Args:
            suggestion_index: Whoosh index for suggestions
            doc_index: Main document index
        """
        self.suggestion_index = suggestion_index
        self.doc_index = doc_index
        
        # Common query templates
        self.query_templates = [
            "title:{term}",
            "tags:{term}",
            "format:{term}",
            "{term} AND {term2}",
            "{term} OR {term2}",
            '"{term}"',  # Phrase search
        ]
    
    def get_suggestions(
        self,
        partial_query: str,
        limit: int = 10,
        include_history: bool = True
    ) -> List[Dict[str, str]]:
        """Get search suggestions for partial query
        
        Args:
            partial_query: Partial query string
            limit: Maximum number of suggestions
            include_history: Whether to include search history
            
        Returns:
            List of suggestions with type and text
        """
        suggestions = []
        
        if not partial_query:
            # Return popular suggestions
            return self._get_popular_suggestions(limit)
        
        partial_query = partial_query.lower().strip()
        
        # Get term suggestions
        term_suggestions = self._get_term_suggestions(partial_query, limit)
        suggestions.extend(term_suggestions)
        
        # Get query suggestions
        query_suggestions = self._get_query_suggestions(partial_query, limit)
        suggestions.extend(query_suggestions)
        
        # Get field suggestions
        if ':' in partial_query:
            field_suggestions = self._get_field_value_suggestions(partial_query, limit)
            suggestions.extend(field_suggestions)
        
        # Deduplicate and limit
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            key = suggestion['text']
            if key not in seen:
                seen.add(key)
                unique_suggestions.append(suggestion)
                if len(unique_suggestions) >= limit:
                    break
        
        return unique_suggestions
    
    def _get_term_suggestions(self, partial: str, limit: int) -> List[Dict]:
        """Get term completions from suggestion index
        
        Args:
            partial: Partial term
            limit: Maximum suggestions
            
        Returns:
            List of term suggestions
        """
        suggestions = []
        
        try:
            with self.suggestion_index.searcher() as searcher:
                # Use prefix query
                query = Prefix("term", partial)
                results = searcher.search(query, limit=limit * 2)
                
                for hit in results:
                    suggestions.append({
                        'text': hit['term'],
                        'type': hit.get('type', 'term'),
                        'frequency': hit.get('frequency', 0)
                    })
                
                # Also try fuzzy matching for typos
                if len(suggestions) < limit:
                    fuzzy_query = FuzzyTerm("term_ngram", partial)
                    fuzzy_results = searcher.search(fuzzy_query, limit=limit)
                    
                    for hit in fuzzy_results:
                        suggestions.append({
                            'text': hit['term'],
                            'type': 'fuzzy',
                            'frequency': hit.get('frequency', 0)
                        })
        
        except Exception as e:
            logger.warning(f"Failed to get term suggestions: {e}")
        
        # Sort by frequency
        suggestions.sort(key=lambda x: x['frequency'], reverse=True)
        
        return suggestions[:limit]
    
    def _get_query_suggestions(self, partial: str, limit: int) -> List[Dict]:
        """Get full query suggestions based on partial input
        
        Args:
            partial: Partial query
            limit: Maximum suggestions
            
        Returns:
            List of query suggestions
        """
        suggestions = []
        
        # Check if partial matches any templates
        for template in self.query_templates:
            if '{term}' in template:
                # Get term suggestions
                terms = self._get_term_suggestions(partial, 5)
                for term_dict in terms[:3]:
                    term = term_dict['text']
                    if '{term2}' in template:
                        # Need two terms
                        other_terms = self._get_related_terms(term, 3)
                        for other in other_terms:
                            query = template.format(term=term, term2=other)
                            suggestions.append({
                                'text': query,
                                'type': 'query_template'
                            })
                    else:
                        query = template.format(term=term)
                        suggestions.append({
                            'text': query,
                            'type': 'query_template'
                        })
        
        return suggestions[:limit]
    
    def _get_field_value_suggestions(self, partial: str, limit: int) -> List[Dict]:
        """Get suggestions for field:value queries
        
        Args:
            partial: Partial field:value query
            limit: Maximum suggestions
            
        Returns:
            List of field value suggestions
        """
        suggestions = []
        
        # Split field and partial value
        if ':' not in partial:
            return suggestions
        
        field, partial_value = partial.rsplit(':', 1)
        field = field.strip()
        partial_value = partial_value.strip()
        
        # Get unique values for the field
        try:
            with self.doc_index.searcher() as searcher:
                if field in ['format', 'category', 'status']:
                    # Get facet values
                    facets = searcher.facet_by_field(field)
                    for value, count in facets.items():
                        if partial_value.lower() in value.lower():
                            suggestions.append({
                                'text': f"{field}:{value}",
                                'type': 'field_value',
                                'count': count
                            })
                
                elif field == 'tags':
                    # Get tag suggestions
                    tag_suggestions = self._get_term_suggestions(partial_value, limit)
                    for tag in tag_suggestions:
                        suggestions.append({
                            'text': f"{field}:{tag['text']}",
                            'type': 'field_value'
                        })
        
        except Exception as e:
            logger.warning(f"Failed to get field suggestions: {e}")
        
        return suggestions[:limit]
    
    def _get_related_terms(self, term: str, limit: int) -> List[str]:
        """Get terms related to the given term
        
        Args:
            term: Base term
            limit: Maximum related terms
            
        Returns:
            List of related terms
        """
        related = []
        
        try:
            with self.doc_index.searcher() as searcher:
                # Search for documents containing the term
                query = Term("content", term)
                results = searcher.search(query, limit=10)
                
                # Extract other common terms from these documents
                term_freq = {}
                for hit in results:
                    # Get tags
                    if 'tags' in hit:
                        tags = hit['tags'].split(',')
                        for tag in tags:
                            tag = tag.strip()
                            if tag and tag != term:
                                term_freq[tag] = term_freq.get(tag, 0) + 1
                
                # Sort by frequency
                sorted_terms = sorted(term_freq.items(), key=lambda x: x[1], reverse=True)
                related = [term for term, _ in sorted_terms[:limit]]
        
        except Exception as e:
            logger.warning(f"Failed to get related terms: {e}")
        
        return related
    
    def _get_popular_suggestions(self, limit: int) -> List[Dict]:
        """Get popular search suggestions
        
        Args:
            limit: Maximum suggestions
            
        Returns:
            List of popular suggestions
        """
        suggestions = []
        
        try:
            with self.suggestion_index.searcher() as searcher:
                # Get most frequent terms
                results = searcher.search_page(
                    Term("type", "title"),
                    1,
                    pagelen=limit,
                    sortedby="frequency",
                    reverse=True
                )
                
                for hit in results:
                    suggestions.append({
                        'text': hit['term'],
                        'type': 'popular',
                        'frequency': hit.get('frequency', 0)
                    })
        
        except Exception as e:
            logger.warning(f"Failed to get popular suggestions: {e}")
        
        # Add some default suggestions if none found
        if not suggestions:
            suggestions = [
                {'text': 'format:markdown', 'type': 'default'},
                {'text': 'tags:documentation', 'type': 'default'},
                {'text': 'title:README', 'type': 'default'},
            ]
        
        return suggestions[:limit]
    
    def record_search(self, query: str):
        """Record a search query for future suggestions
        
        Args:
            query: Search query that was executed
        """
        try:
            writer = self.suggestion_index.writer()
            
            # Extract terms from query
            terms = re.findall(r'\b\w+\b', query.lower())
            
            for term in terms:
                if len(term) > 2:  # Skip very short terms
                    writer.update_document(
                        term=term,
                        term_ngram=term,
                        frequency=1,
                        type='query_term',
                        last_used=datetime.now()
                    )
            
            # Also store the full query
            if len(query) < 100:  # Don't store very long queries
                writer.update_document(
                    term=query.lower(),
                    term_ngram=query,
                    frequency=1,
                    type='full_query',
                    last_used=datetime.now()
                )
            
            writer.commit()
            
        except Exception as e:
            logger.warning(f"Failed to record search: {e}")
    
    def clear_history(self):
        """Clear search history and suggestions"""
        try:
            writer = self.suggestion_index.writer()
            writer.commit(mergetype=writer.CLEAR)
            logger.info("Cleared search suggestions")
        except Exception as e:
            logger.error(f"Failed to clear suggestions: {e}")