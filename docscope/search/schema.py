"""Search index schema definition"""

from whoosh import fields
from whoosh.analysis import (
    StandardAnalyzer, StemmingAnalyzer, KeywordAnalyzer,
    NgramFilter, IntraWordFilter
)
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC, DATETIME, BOOLEAN


def create_document_schema() -> Schema:
    """Create the search index schema for documents
    
    Returns:
        Whoosh schema for document indexing
    """
    # Create custom analyzers
    stem_analyzer = StemmingAnalyzer()
    keyword_analyzer = KeywordAnalyzer()
    
    # Define schema
    schema = Schema(
        # Core fields
        id=ID(stored=True, unique=True),
        path=ID(stored=True),
        title=TEXT(stored=True, analyzer=stem_analyzer, field_boost=2.0),
        content=TEXT(stored=False, analyzer=stem_analyzer),
        
        # Metadata fields
        format=KEYWORD(stored=True, lowercase=True),
        category=KEYWORD(stored=True, lowercase=True),
        tags=KEYWORD(stored=True, lowercase=True, commas=True),
        
        # Date fields
        created_at=DATETIME(stored=True, sortable=True),
        modified_at=DATETIME(stored=True, sortable=True),
        indexed_at=DATETIME(stored=True, sortable=True),
        
        # Numeric fields
        size=NUMERIC(stored=True, sortable=True),
        score=NUMERIC(stored=True, sortable=True, default=0.0),
        
        # Additional searchable fields
        description=TEXT(stored=True, analyzer=stem_analyzer),
        keywords=KEYWORD(stored=True, lowercase=True, commas=True),
        
        # Content hash for duplicate detection
        content_hash=ID(stored=True),
        
        # Status fields
        status=KEYWORD(stored=True, lowercase=True),
        
        # Full path components for hierarchical search
        path_components=KEYWORD(stored=True, lowercase=True, commas=True),
        
        # Snippet storage for search results
        snippet=TEXT(stored=True),
        
        # Faceting fields
        year=NUMERIC(stored=True, sortable=True),
        month=NUMERIC(stored=True, sortable=True),
        
        # Additional metadata as JSON string
        metadata_json=TEXT(stored=True),
    )
    
    return schema


def create_suggestion_schema() -> Schema:
    """Create schema for search suggestions and autocomplete
    
    Returns:
        Whoosh schema for suggestions
    """
    # Use n-gram analyzer for fuzzy matching
    ngram_analyzer = StandardAnalyzer() | NgramFilter(minsize=2, maxsize=4)
    
    schema = Schema(
        term=ID(stored=True, unique=True),
        term_ngram=TEXT(analyzer=ngram_analyzer),
        frequency=NUMERIC(stored=True, sortable=True),
        type=KEYWORD(stored=True),  # query, title, tag, etc.
        last_used=DATETIME(stored=True, sortable=True),
    )
    
    return schema


def create_facet_schema() -> Schema:
    """Create schema for faceted search
    
    Returns:
        Whoosh schema for facets
    """
    schema = Schema(
        field_name=ID(stored=True),
        field_value=KEYWORD(stored=True),
        document_count=NUMERIC(stored=True, sortable=True),
        last_updated=DATETIME(stored=True),
    )
    
    return schema


# Field configuration for different document types
FIELD_CONFIGS = {
    'markdown': {
        'boost_title': 2.0,
        'boost_headers': 1.5,
        'extract_headers': True,
        'extract_links': True,
    },
    'code': {
        'boost_title': 1.5,
        'boost_functions': 1.8,
        'extract_imports': True,
        'extract_functions': True,
        'extract_classes': True,
    },
    'text': {
        'boost_title': 2.0,
        'boost_first_paragraph': 1.2,
    },
    'json': {
        'boost_title': 1.5,
        'extract_keys': True,
    },
    'yaml': {
        'boost_title': 1.5,
        'extract_keys': True,
    },
}