"""Query parser for search engine"""

import re
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta

from whoosh.query import (
    Query, Term, And, Or, Not, Phrase, Wildcard, Regex,
    DateRange, NumericRange, FuzzyTerm, Variations, Every
)
from whoosh.qparser import QueryParser as WhooshQueryParser
from whoosh.qparser import MultifieldParser, OrGroup, AndGroup
from whoosh.qparser.syntax import OrGroup as SyntaxOrGroup
from whoosh.qparser.plugins import (
    WhitespacePlugin, SingleQuotePlugin, 
    WildcardPlugin, RegexPlugin, FuzzyTermPlugin
)

from ..core.logging import get_logger

logger = get_logger(__name__)


class QueryParser:
    """Advanced query parser for search queries"""
    
    def __init__(self, schema):
        """Initialize query parser
        
        Args:
            schema: Whoosh schema for the index
        """
        self.schema = schema
        self._init_parsers()
        
        # Query type patterns
        self.patterns = {
            'phrase': r'"([^"]+)"',
            'field': r'(\w+):([^\s]+)',
            'wildcard': r'[*?]',
            'fuzzy': r'~\d*$',
            'range': r'\[.+\s+TO\s+.+\]',
            'boolean': r'\b(AND|OR|NOT)\b',
        }
    
    def _init_parsers(self):
        """Initialize different parser types"""
        # Simple parser for basic queries
        self.simple_parser = MultifieldParser(
            ["title", "content", "tags"],
            self.schema,
            group=OrGroup
        )
        
        # Advanced parser with all features
        self.advanced_parser = MultifieldParser(
            ["title", "content", "tags", "keywords"],
            self.schema
        )
        
        # Add plugins for advanced features
        self.advanced_parser.add_plugin(WildcardPlugin())
        self.advanced_parser.add_plugin(RegexPlugin())
        self.advanced_parser.add_plugin(FuzzyTermPlugin())
    
    def parse(self, query_string: str, advanced: bool = False) -> Query:
        """Parse a search query string
        
        Args:
            query_string: The query string to parse
            advanced: Whether to use advanced parsing
            
        Returns:
            Whoosh Query object
        """
        if not query_string or not query_string.strip():
            # Return query that matches everything
            return Every()
        
        query_string = query_string.strip()
        
        try:
            # Detect query type and use appropriate parser
            if self._is_advanced_query(query_string) or advanced:
                return self._parse_advanced(query_string)
            else:
                return self._parse_simple(query_string)
                
        except Exception as e:
            logger.warning(f"Failed to parse query '{query_string}': {e}")
            # Fallback to simple term search
            return self._create_fallback_query(query_string)
    
    def _parse_simple(self, query_string: str) -> Query:
        """Parse a simple search query
        
        Args:
            query_string: Simple query string
            
        Returns:
            Parsed query
        """
        return self.simple_parser.parse(query_string)
    
    def _parse_advanced(self, query_string: str) -> Query:
        """Parse an advanced search query
        
        Args:
            query_string: Advanced query string
            
        Returns:
            Parsed query
        """
        # Pre-process query for special syntax
        processed_query = self._preprocess_query(query_string)
        
        # Parse with advanced parser
        return self.advanced_parser.parse(processed_query)
    
    def _is_advanced_query(self, query_string: str) -> bool:
        """Check if query requires advanced parsing
        
        Args:
            query_string: Query to check
            
        Returns:
            True if advanced features detected
        """
        # Check for advanced patterns
        for pattern_name, pattern in self.patterns.items():
            if pattern_name in ['phrase', 'boolean']:
                continue  # These work in simple parser too
            if re.search(pattern, query_string):
                return True
        
        # Check for field-specific searches
        if ':' in query_string:
            return True
        
        return False
    
    def _preprocess_query(self, query_string: str) -> str:
        """Preprocess query string for special syntax
        
        Args:
            query_string: Original query
            
        Returns:
            Preprocessed query
        """
        # Handle date ranges
        query_string = self._process_date_ranges(query_string)
        
        # Handle special operators
        query_string = self._process_operators(query_string)
        
        return query_string
    
    def _process_date_ranges(self, query_string: str) -> str:
        """Process date range queries
        
        Args:
            query_string: Query with potential date ranges
            
        Returns:
            Query with processed date ranges
        """
        # Pattern for relative dates like "last week", "past month"
        relative_patterns = {
            r'\blast\s+(\d+\s+)?days?\b': self._get_days_ago,
            r'\blast\s+week\b': lambda: 7,
            r'\blast\s+month\b': lambda: 30,
            r'\blast\s+year\b': lambda: 365,
            r'\btoday\b': lambda: 0,
            r'\byesterday\b': lambda: 1,
        }
        
        for pattern, days_func in relative_patterns.items():
            match = re.search(pattern, query_string, re.IGNORECASE)
            if match:
                if callable(days_func):
                    days = days_func()
                else:
                    days = days_func(match)
                
                # Create date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                date_range = f"modified_at:[{start_date.strftime('%Y%m%d')} TO {end_date.strftime('%Y%m%d')}]"
                query_string = re.sub(pattern, date_range, query_string, flags=re.IGNORECASE)
        
        return query_string
    
    def _get_days_ago(self, match) -> int:
        """Extract number of days from match"""
        if match.group(1):
            return int(match.group(1).strip())
        return 1
    
    def _process_operators(self, query_string: str) -> str:
        """Process special operators in query
        
        Args:
            query_string: Query with operators
            
        Returns:
            Processed query
        """
        # Convert common operators
        replacements = {
            ' && ': ' AND ',
            ' || ': ' OR ',
            ' ! ': ' NOT ',
            ' + ': ' AND ',  # Required term
            ' - ': ' NOT ',  # Excluded term
        }
        
        for old, new in replacements.items():
            query_string = query_string.replace(old, new)
        
        return query_string
    
    def build_filter_query(self, filters: Dict[str, Any]) -> Optional[Query]:
        """Build a filter query from filter dictionary
        
        Args:
            filters: Dictionary of field:value filters
            
        Returns:
            Combined filter query or None
        """
        if not filters:
            return None
        
        filter_queries = []
        
        for field, value in filters.items():
            if field not in self.schema.names():
                logger.warning(f"Unknown filter field: {field}")
                continue
            
            if isinstance(value, list):
                # Multiple values - OR them together
                or_queries = [Term(field, v) for v in value]
                filter_queries.append(Or(or_queries))
            elif isinstance(value, dict):
                # Range query
                if 'from' in value or 'to' in value:
                    filter_queries.append(self._build_range_query(field, value))
            else:
                # Single value
                filter_queries.append(Term(field, value))
        
        if len(filter_queries) == 1:
            return filter_queries[0]
        elif len(filter_queries) > 1:
            return And(filter_queries)
        
        return None
    
    def _build_range_query(self, field: str, range_dict: Dict) -> Query:
        """Build a range query
        
        Args:
            field: Field to query
            range_dict: Dictionary with 'from' and/or 'to' keys
            
        Returns:
            Range query
        """
        field_type = self.schema[field]
        
        if 'DATETIME' in str(field_type):
            # Date range
            start = range_dict.get('from')
            end = range_dict.get('to')
            
            if isinstance(start, str):
                start = datetime.fromisoformat(start)
            if isinstance(end, str):
                end = datetime.fromisoformat(end)
            
            return DateRange(field, start, end)
        else:
            # Numeric range
            start = range_dict.get('from')
            end = range_dict.get('to')
            return NumericRange(field, start, end)
    
    def _create_fallback_query(self, query_string: str) -> Query:
        """Create a fallback query for failed parsing
        
        Args:
            query_string: Original query string
            
        Returns:
            Simple OR query across main fields
        """
        # Split into terms
        terms = query_string.split()
        
        # Create OR query across title and content
        or_queries = []
        for term in terms:
            or_queries.append(Term("title", term.lower()))
            or_queries.append(Term("content", term.lower()))
        
        if len(or_queries) == 1:
            return or_queries[0]
        else:
            return Or(or_queries)
    
    def extract_facets(self, query_string: str) -> List[str]:
        """Extract fields that should be used for faceting
        
        Args:
            query_string: Query string
            
        Returns:
            List of field names for faceting
        """
        facet_fields = ['format', 'category', 'tags', 'status', 'year']
        
        # Add fields mentioned in the query
        field_pattern = r'(\w+):'
        matches = re.findall(field_pattern, query_string)
        for field in matches:
            if field in self.schema.names() and field not in facet_fields:
                facet_fields.append(field)
        
        return facet_fields
    
    def suggest_query(self, partial_query: str) -> List[str]:
        """Suggest query completions
        
        Args:
            partial_query: Partial query string
            
        Returns:
            List of suggested completions
        """
        suggestions = []
        
        # Suggest field names if typing ':'
        if partial_query.endswith(':'):
            field_prefix = partial_query[:-1]
            for field_name in self.schema.names():
                if field_name.startswith(field_prefix):
                    suggestions.append(f"{field_name}:")
        
        # Suggest boolean operators
        last_word = partial_query.split()[-1] if partial_query else ""
        if last_word:
            for operator in ['AND', 'OR', 'NOT']:
                if operator.startswith(last_word.upper()):
                    suggestions.append(operator)
        
        return suggestions[:10]  # Limit suggestions