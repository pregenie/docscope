"""Tests for search engine"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import shutil

from docscope.search import SearchEngine
from docscope.search.indexer import DocumentIndexer
from docscope.search.query_parser import QueryParser
from docscope.search.ranker import SearchRanker
from docscope.search.schema import create_document_schema
from docscope.core.models import Document, DocumentFormat, SearchResults


@pytest.fixture
def temp_index_dir():
    """Create temporary index directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def search_engine(temp_index_dir):
    """Create search engine with temporary index"""
    engine = SearchEngine(index_dir=temp_index_dir)
    return engine


@pytest.fixture
def sample_documents():
    """Create sample documents for testing"""
    docs = [
        Document(
            id="doc1",
            path="/docs/guide.md",
            title="Getting Started Guide",
            content="This is a comprehensive guide to getting started with DocScope. "
                   "It covers installation, configuration, and basic usage.",
            format=DocumentFormat.MARKDOWN,
            size=1024,
            content_hash="hash1",
            created_at=datetime.now() - timedelta(days=5),
            modified_at=datetime.now() - timedelta(days=2),
            tags=["guide", "documentation", "tutorial"],
            metadata={"author": "John Doe"}
        ),
        Document(
            id="doc2",
            path="/docs/api.md",
            title="API Documentation",
            content="Complete API reference for DocScope. Includes all endpoints, "
                   "parameters, and response formats for the REST API.",
            format=DocumentFormat.MARKDOWN,
            size=2048,
            content_hash="hash2",
            created_at=datetime.now() - timedelta(days=10),
            modified_at=datetime.now() - timedelta(days=1),
            tags=["api", "reference", "documentation"],
            metadata={"version": "1.0"}
        ),
        Document(
            id="doc3",
            path="/code/example.py",
            title="Python Example",
            content="import docscope\n\n# Example Python code showing how to use DocScope\n"
                   "engine = docscope.SearchEngine()\nresults = engine.search('test')",
            format=DocumentFormat.CODE,
            size=512,
            content_hash="hash3",
            created_at=datetime.now() - timedelta(days=3),
            modified_at=datetime.now() - timedelta(days=3),
            tags=["python", "example", "code"],
            metadata={"language": "python"}
        ),
        Document(
            id="doc4",
            path="/config/settings.json",
            title="Configuration Settings",
            content='{"search": {"engine": "whoosh", "fuzzy": true}, '
                   '"api": {"port": 8080}}',
            format=DocumentFormat.JSON,
            size=256,
            content_hash="hash4",
            created_at=datetime.now() - timedelta(days=7),
            modified_at=datetime.now() - timedelta(days=7),
            tags=["configuration", "settings"],
            metadata={"type": "config"}
        ),
    ]
    return docs


def test_search_engine_initialization(search_engine):
    """Test search engine initialization"""
    assert search_engine is not None
    assert search_engine.indexer is not None
    assert search_engine.query_parser is not None
    assert search_engine.ranker is not None
    assert search_engine.suggestions is not None


def test_index_documents(search_engine, sample_documents):
    """Test indexing documents"""
    # Index documents
    count = search_engine.index_documents(sample_documents)
    assert count == len(sample_documents)
    
    # Verify stats
    stats = search_engine.get_stats()
    assert stats['total_documents'] == len(sample_documents)


def test_basic_search(search_engine, sample_documents):
    """Test basic search functionality"""
    # Index documents first
    search_engine.index_documents(sample_documents)
    
    # Search for a term
    results = search_engine.search("documentation")
    
    assert isinstance(results, SearchResults)
    assert results.total > 0
    assert len(results.results) > 0
    
    # Check that relevant documents are returned
    titles = [r.title for r in results.results]
    assert "API Documentation" in titles or "Getting Started Guide" in titles


def test_search_with_filters(search_engine, sample_documents):
    """Test search with filters"""
    search_engine.index_documents(sample_documents)
    
    # Filter by format
    results = search_engine.search("", filters={"format": "markdown"})
    assert results.total == 2  # Only markdown documents
    
    # Filter by tags
    results = search_engine.search("", filters={"tags": "api"})
    assert results.total >= 1
    assert any("API Documentation" in r.title for r in results.results)


def test_phrase_search(search_engine, sample_documents):
    """Test phrase search"""
    search_engine.index_documents(sample_documents)
    
    # Search for exact phrase
    results = search_engine.search('"getting started"')
    assert results.total >= 1
    assert any("Getting Started" in r.title for r in results.results)


def test_field_search(search_engine, sample_documents):
    """Test field-specific search"""
    search_engine.index_documents(sample_documents)
    
    # Search in title field
    results = search_engine.search("title:API")
    assert results.total >= 1
    assert any("API" in r.title for r in results.results)
    
    # Search by format
    results = search_engine.search("format:code")
    assert results.total == 1
    assert results.results[0].format == DocumentFormat.CODE


def test_boolean_search(search_engine, sample_documents):
    """Test boolean operators"""
    search_engine.index_documents(sample_documents)
    
    # AND operator
    results = search_engine.search("documentation AND api")
    assert results.total >= 1
    
    # OR operator
    results = search_engine.search("python OR configuration")
    assert results.total >= 2
    
    # NOT operator
    results = search_engine.search("documentation NOT api")
    assert all("API" not in r.title for r in results.results)


def test_wildcard_search(search_engine, sample_documents):
    """Test wildcard search"""
    search_engine.index_documents(sample_documents)
    
    # Wildcard search
    results = search_engine.search("doc*")
    assert results.total > 0
    
    results = search_engine.search("*scope")
    assert results.total > 0


def test_search_pagination(search_engine, sample_documents):
    """Test search pagination"""
    search_engine.index_documents(sample_documents)
    
    # First page
    results1 = search_engine.search("", limit=2, offset=0)
    assert len(results1.results) <= 2
    
    # Second page
    results2 = search_engine.search("", limit=2, offset=2)
    assert len(results2.results) <= 2
    
    # Check no overlap
    ids1 = {r.document_id for r in results1.results}
    ids2 = {r.document_id for r in results2.results}
    assert not ids1.intersection(ids2)


def test_search_sorting(search_engine, sample_documents):
    """Test search result sorting"""
    search_engine.index_documents(sample_documents)
    
    # Sort by modified date descending
    results = search_engine.search("", sort_by="-modified_at")
    dates = [r.metadata.get('modified_at') for r in results.results if r.metadata]
    # Results should be in descending order
    
    # Sort by title ascending
    results = search_engine.search("", sort_by="title")
    titles = [r.title for r in results.results]
    assert titles == sorted(titles)


def test_search_facets(search_engine, sample_documents):
    """Test faceted search"""
    search_engine.index_documents(sample_documents)
    
    # Search with facets
    results = search_engine.search("", facets=True)
    
    assert results.facets is not None
    assert 'format' in results.facets
    assert results.facets['format'].get('markdown') == 2
    assert results.facets['format'].get('code') == 1


def test_search_suggestions(search_engine, sample_documents):
    """Test search suggestions"""
    search_engine.index_documents(sample_documents)
    
    # Get suggestions for partial query
    suggestions = search_engine.get_suggestions("doc")
    assert len(suggestions) > 0
    
    # Get suggestions for empty query (popular)
    suggestions = search_engine.get_suggestions("")
    assert len(suggestions) > 0


def test_delete_document(search_engine, sample_documents):
    """Test document deletion from index"""
    search_engine.index_documents(sample_documents)
    
    # Delete a document
    deleted = search_engine.delete_document("doc1")
    assert deleted
    
    # Verify it's gone
    results = search_engine.search("Getting Started Guide")
    assert results.total == 0 or not any(
        r.document_id == "doc1" for r in results.results
    )


def test_clear_index(search_engine, sample_documents):
    """Test clearing the index"""
    search_engine.index_documents(sample_documents)
    
    # Clear index
    search_engine.clear_index()
    
    # Verify empty
    stats = search_engine.get_stats()
    assert stats['total_documents'] == 0


def test_optimize_index(search_engine, sample_documents):
    """Test index optimization"""
    search_engine.index_documents(sample_documents)
    
    # Optimize should not raise errors
    search_engine.optimize_index()
    
    # Index should still work
    results = search_engine.search("documentation")
    assert results.total > 0


def test_query_parser():
    """Test query parser directly"""
    schema = create_document_schema()
    parser = QueryParser(schema)
    
    # Simple query
    query = parser.parse("test")
    assert query is not None
    
    # Advanced query
    query = parser.parse("title:API AND format:markdown")
    assert query is not None
    
    # Filter query
    filters = {"format": "markdown", "tags": ["api", "documentation"]}
    filter_query = parser.build_filter_query(filters)
    assert filter_query is not None


def test_search_ranker():
    """Test search ranker"""
    ranker = SearchRanker()
    
    # Test scoring algorithm initialization
    assert ranker.scorer is not None
    assert ranker.boost_factors is not None


def test_indexer_stats(search_engine, sample_documents):
    """Test indexer statistics"""
    indexer = search_engine.indexer
    
    # Index documents
    indexer.index_documents(sample_documents)
    
    # Get stats
    stats = indexer.get_index_stats()
    assert 'total_documents' in stats
    assert 'index_size_mb' in stats
    assert 'fields' in stats
    assert stats['total_documents'] == len(sample_documents)


def test_similar_documents(search_engine, sample_documents):
    """Test finding similar documents"""
    search_engine.index_documents(sample_documents)
    
    # Find documents similar to one
    results = search_engine.search_similar("doc1", limit=2)
    
    assert isinstance(results, SearchResults)
    # Should find other documentation
    assert any("documentation" in r.title.lower() for r in results.results)


def test_empty_query(search_engine, sample_documents):
    """Test empty query returns all documents"""
    search_engine.index_documents(sample_documents)
    
    results = search_engine.search("")
    assert results.total == len(sample_documents)


def test_no_results_query(search_engine, sample_documents):
    """Test query with no results"""
    search_engine.index_documents(sample_documents)
    
    results = search_engine.search("nonexistentterm12345")
    assert results.total == 0
    assert len(results.results) == 0
    
    # Should have suggestions
    assert len(results.suggestions) > 0