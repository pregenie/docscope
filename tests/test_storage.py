"""Tests for storage layer"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import uuid

from docscope.storage import DocumentStore
from docscope.storage.database import DatabaseManager
from docscope.storage.repository import DocumentRepository, CategoryRepository, TagRepository
from docscope.core.config import StorageConfig
from docscope.core.models import Document, DocumentFormat, DocumentStatus, ScanResult


@pytest.fixture
def storage_config():
    """Create storage configuration for tests"""
    # Use temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    return StorageConfig(
        backend="sqlite",
        sqlite={"path": db_path},
        cache={"enabled": False}
    )


@pytest.fixture
def document_store(storage_config):
    """Create document store instance"""
    store = DocumentStore(storage_config)
    store.initialize(drop_existing=True)
    yield store
    store.close()
    
    # Clean up database file
    Path(storage_config.sqlite["path"]).unlink(missing_ok=True)


@pytest.fixture
def sample_document():
    """Create sample document for testing"""
    return Document(
        id=str(uuid.uuid4()),
        path="/test/document.md",
        title="Test Document",
        content="This is test content",
        format=DocumentFormat.MARKDOWN,
        size=1024,
        content_hash="abc123",
        created_at=datetime.now(),
        modified_at=datetime.now(),
        indexed_at=datetime.now(),
        tags=["test", "sample"],
        metadata={"key": "value"}
    )


def test_store_initialization(storage_config):
    """Test document store initialization"""
    store = DocumentStore(storage_config)
    assert store is not None
    assert not store._initialized
    
    store.initialize()
    assert store._initialized
    
    store.close()
    Path(storage_config.sqlite["path"]).unlink(missing_ok=True)


def test_store_document(document_store, sample_document):
    """Test storing a document"""
    doc_id = document_store.store_document(sample_document)
    
    assert doc_id is not None
    assert doc_id == sample_document.id
    
    # Verify document was stored
    retrieved = document_store.get_document(doc_id)
    assert retrieved is not None
    assert retrieved.title == sample_document.title
    assert retrieved.content == sample_document.content


def test_get_document(document_store, sample_document):
    """Test retrieving a document"""
    # Store document first
    doc_id = document_store.store_document(sample_document)
    
    # Retrieve by ID
    doc = document_store.get_document(doc_id)
    assert doc is not None
    assert doc.id == doc_id
    assert doc.title == sample_document.title
    assert doc.path == sample_document.path
    
    # Test non-existent document
    doc = document_store.get_document("nonexistent")
    assert doc is None


def test_get_document_by_path(document_store, sample_document):
    """Test retrieving document by path"""
    document_store.store_document(sample_document)
    
    doc = document_store.get_document_by_path(sample_document.path)
    assert doc is not None
    assert doc.path == sample_document.path
    assert doc.title == sample_document.title


def test_update_document(document_store, sample_document):
    """Test updating a document"""
    doc_id = document_store.store_document(sample_document)
    
    # Update document
    updates = {
        "title": "Updated Title",
        "content": "Updated content",
        "metadata": {"updated": True}
    }
    
    success = document_store.update_document(doc_id, updates)
    assert success
    
    # Verify updates
    doc = document_store.get_document(doc_id)
    assert doc.title == "Updated Title"
    assert doc.content == "Updated content"
    assert doc.metadata["updated"] is True


def test_delete_document(document_store, sample_document):
    """Test deleting a document"""
    doc_id = document_store.store_document(sample_document)
    
    # Delete document
    success = document_store.delete_document(doc_id)
    assert success
    
    # Verify deletion
    doc = document_store.get_document(doc_id)
    assert doc is None
    
    # Try deleting non-existent document
    success = document_store.delete_document("nonexistent")
    assert not success


def test_store_scan_result(document_store):
    """Test storing documents from scan result"""
    result = ScanResult()
    
    # Add multiple documents to result
    for i in range(5):
        doc = Document(
            id=str(uuid.uuid4()),
            path=f"/test/doc{i}.txt",
            title=f"Document {i}",
            content=f"Content {i}",
            format=DocumentFormat.TEXT,
            size=100,
            content_hash=f"hash{i}",
            created_at=datetime.now(),
            modified_at=datetime.now(),
            status=DocumentStatus.INDEXED
        )
        result.documents.append(doc)
    
    # Store scan result
    stored = document_store.store_scan_result(result)
    assert stored == 5
    
    # Verify all documents were stored
    docs = document_store.list_documents(limit=10)
    assert len(docs) == 5


def test_list_documents(document_store):
    """Test listing documents with filters"""
    # Store multiple documents
    for i in range(10):
        doc = Document(
            id=str(uuid.uuid4()),
            path=f"/test/doc{i}.{'md' if i < 5 else 'txt'}",
            title=f"Document {i}",
            content=f"Content {i}",
            format=DocumentFormat.MARKDOWN if i < 5 else DocumentFormat.TEXT,
            size=100 + i,
            content_hash=f"hash{i}",
            created_at=datetime.now(),
            modified_at=datetime.now() - timedelta(hours=i),
            status=DocumentStatus.INDEXED
        )
        document_store.store_document(doc)
    
    # List all documents
    docs = document_store.list_documents(limit=20)
    assert len(docs) == 10
    
    # List with limit
    docs = document_store.list_documents(limit=5)
    assert len(docs) == 5
    
    # List with offset
    docs = document_store.list_documents(limit=5, offset=5)
    assert len(docs) == 5
    
    # Filter by format
    docs = document_store.list_documents(format="markdown")
    assert len(docs) == 5
    assert all(d.format == DocumentFormat.MARKDOWN for d in docs)
    
    # Sort by modified date
    docs = document_store.list_documents(sort_by="modified_at", sort_order="asc")
    assert docs[0].modified_at < docs[-1].modified_at


def test_count_documents(document_store):
    """Test counting documents"""
    # Store some documents
    for i in range(5):
        doc = Document(
            id=str(uuid.uuid4()),
            path=f"/test/doc{i}.txt",
            title=f"Document {i}",
            content=f"Content {i}",
            format=DocumentFormat.TEXT,
            size=100,
            content_hash=f"hash{i}",
            created_at=datetime.now(),
            modified_at=datetime.now(),
            status=DocumentStatus.INDEXED if i < 3 else DocumentStatus.PENDING
        )
        document_store.store_document(doc)
    
    # Count all documents
    count = document_store.count_documents()
    assert count == 5
    
    # Count by status
    count = document_store.count_documents(status="indexed")
    assert count == 3


def test_find_duplicates(document_store):
    """Test finding duplicate documents"""
    # Store duplicate documents
    for i in range(3):
        for j in range(2):  # Create 2 copies of each
            doc = Document(
                id=str(uuid.uuid4()),
                path=f"/test/doc{i}_copy{j}.txt",
                title=f"Document {i}",
                content=f"Content {i}",
                format=DocumentFormat.TEXT,
                size=100,
                content_hash=f"hash{i}",  # Same hash for duplicates
                created_at=datetime.now(),
                modified_at=datetime.now()
            )
            document_store.store_document(doc)
    
    # Find duplicates
    duplicates = document_store.find_duplicates()
    assert len(duplicates) == 3  # 3 groups of duplicates
    
    for group in duplicates:
        assert len(group) == 2  # Each group has 2 duplicates
        # All documents in group should have same content hash
        hashes = [d.content_hash for d in group]
        assert len(set(hashes)) == 1


def test_get_modified_since(document_store):
    """Test getting documents modified since timestamp"""
    now = datetime.now()
    
    # Store documents with different modification times
    for i in range(5):
        doc = Document(
            id=str(uuid.uuid4()),
            path=f"/test/doc{i}.txt",
            title=f"Document {i}",
            content=f"Content {i}",
            format=DocumentFormat.TEXT,
            size=100,
            content_hash=f"hash{i}",
            created_at=now - timedelta(days=5),
            modified_at=now - timedelta(days=i)
        )
        document_store.store_document(doc)
    
    # Get documents modified in last 2 days
    since = now - timedelta(days=2)
    docs = document_store.get_modified_since(since)
    assert len(docs) == 2  # Documents 0 and 1


def test_categories(document_store):
    """Test category operations"""
    # Create categories
    root_id = document_store.create_category("Documentation", color="#blue")
    api_id = document_store.create_category("API", parent_id=root_id)
    guide_id = document_store.create_category("Guides", parent_id=root_id)
    
    # List categories
    categories = document_store.list_categories()
    assert len(categories) == 1  # Only root category
    assert categories[0]["name"] == "Documentation"
    
    # List sub-categories
    subcategories = document_store.list_categories(parent_id=root_id)
    assert len(subcategories) == 2
    names = [c["name"] for c in subcategories]
    assert "API" in names
    assert "Guides" in names


def test_tags(document_store):
    """Test tag operations"""
    # Create tags
    tag1_id = document_store.create_tag("python", color="#blue")
    tag2_id = document_store.create_tag("javascript", color="#yellow")
    tag3_id = document_store.create_tag("python")  # Should return existing
    
    # List tags
    tags = document_store.list_tags()
    assert len(tags) == 2  # Only 2 unique tags
    names = [t["name"] for t in tags]
    assert "python" in names
    assert "javascript" in names


def test_document_with_tags(document_store, sample_document):
    """Test storing document with tags"""
    # Store document with tags
    document_store.store_document(sample_document)
    
    # Retrieve and check tags
    doc = document_store.get_document(sample_document.id)
    assert "test" in doc.tags
    assert "sample" in doc.tags
    
    # Check tags were created
    tags = document_store.list_tags()
    tag_names = [t["name"] for t in tags]
    assert "test" in tag_names
    assert "sample" in tag_names


def test_update_existing_document(document_store, sample_document):
    """Test updating existing document by storing again"""
    # Store document
    document_store.store_document(sample_document)
    
    # Modify and store again
    sample_document.title = "Modified Title"
    sample_document.content = "Modified Content"
    doc_id = document_store.store_document(sample_document)
    
    # Should return same ID
    assert doc_id == sample_document.id
    
    # Verify updates
    doc = document_store.get_document(doc_id)
    assert doc.title == "Modified Title"
    assert doc.content == "Modified Content"


def test_storage_stats(document_store):
    """Test getting storage statistics"""
    # Store some documents
    for i in range(5):
        doc = Document(
            id=str(uuid.uuid4()),
            path=f"/test/doc{i}.{'md' if i < 3 else 'txt'}",
            title=f"Document {i}",
            content=f"Content {i}",
            format=DocumentFormat.MARKDOWN if i < 3 else DocumentFormat.TEXT,
            size=100,
            content_hash=f"hash{i}",
            created_at=datetime.now(),
            modified_at=datetime.now()
        )
        document_store.store_document(doc)
    
    # Get stats
    stats = document_store.get_stats()
    assert stats["backend"] == "sqlite"
    assert stats["documents"] == 5
    assert "formats" in stats
    assert stats["formats"]["markdown"] == 3
    assert stats["formats"]["text"] == 2


def test_database_manager(storage_config):
    """Test database manager directly"""
    manager = DatabaseManager(storage_config)
    
    # Test initialization
    manager.initialize()
    assert manager._initialized
    
    # Test session creation
    with manager.session_scope() as session:
        assert session is not None
    
    # Test stats
    stats = manager.get_stats()
    assert stats["backend"] == "sqlite"
    assert stats["initialized"] is True
    
    # Clean up
    manager.close()
    Path(storage_config.sqlite["path"]).unlink(missing_ok=True)


def test_repository_pattern(storage_config):
    """Test repository pattern directly"""
    manager = DatabaseManager(storage_config)
    manager.initialize(drop_existing=True)
    
    with manager.session_scope() as session:
        doc_repo = DocumentRepository(session)
        
        # Create a document
        doc = Document(
            id=str(uuid.uuid4()),
            path="/test.txt",
            title="Test",
            content="Content",
            format=DocumentFormat.TEXT,
            size=100,
            content_hash="hash",
            created_at=datetime.now(),
            modified_at=datetime.now()
        )
        
        # Store via repository
        db_doc = doc_repo.create(doc)
        assert db_doc.id == doc.id
        
        # Retrieve via repository
        retrieved = doc_repo.get(doc.id)
        assert retrieved is not None
        assert retrieved.title == "Test"
    
    manager.close()
    Path(storage_config.sqlite["path"]).unlink(missing_ok=True)