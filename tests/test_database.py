"""Tests for database operations"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
import uuid

from docscope.storage.database import DatabaseManager
from docscope.storage.models import DocumentModel, CategoryModel, TagModel, Base
from docscope.storage.repository import DocumentRepository, CategoryRepository, TagRepository
from docscope.core.config import StorageConfig
from sqlalchemy.orm import Session


@pytest.fixture
def db_config():
    """Create database configuration for tests"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    return StorageConfig(
        backend="sqlite",
        sqlite={"path": db_path}
    )


@pytest.fixture
def db_manager(db_config):
    """Create database manager"""
    manager = DatabaseManager(db_config)
    manager.initialize(drop_existing=True)
    yield manager
    manager.close()
    Path(db_config.sqlite["path"]).unlink(missing_ok=True)


def test_database_initialization(db_config):
    """Test database initialization"""
    manager = DatabaseManager(db_config)
    
    assert not manager._initialized
    manager.initialize()
    assert manager._initialized
    
    # Test that tables are created
    with manager.session_scope() as session:
        # Try to query tables
        doc_count = session.query(DocumentModel).count()
        assert doc_count == 0
        
        cat_count = session.query(CategoryModel).count()
        assert cat_count == 0
        
        tag_count = session.query(TagModel).count()
        assert tag_count == 0
    
    manager.close()
    Path(db_config.sqlite["path"]).unlink(missing_ok=True)


def test_database_url_generation(db_config):
    """Test database URL generation"""
    manager = DatabaseManager(db_config)
    
    url = manager.get_database_url()
    assert url.startswith("sqlite:///")
    assert db_config.sqlite["path"] in url


def test_session_management(db_manager):
    """Test session creation and management"""
    # Get session
    session = db_manager.get_session()
    assert isinstance(session, Session)
    session.close()
    
    # Test session scope
    with db_manager.session_scope() as session:
        assert isinstance(session, Session)
        # Session should auto-close after context


def test_document_model(db_manager):
    """Test document model operations"""
    with db_manager.session_scope() as session:
        # Create document
        doc = DocumentModel(
            id="test-id",
            path="/test/path.txt",
            title="Test Document",
            content="Test content",
            content_hash="hash123",
            format="text",
            size=100,
            metadata={"key": "value"}
        )
        
        session.add(doc)
        session.flush()
        
        # Query document
        retrieved = session.query(DocumentModel).filter_by(id="test-id").first()
        assert retrieved is not None
        assert retrieved.title == "Test Document"
        assert retrieved.metadata["key"] == "value"
        
        # Test to_dict method
        doc_dict = retrieved.to_dict()
        assert doc_dict["id"] == "test-id"
        assert doc_dict["title"] == "Test Document"


def test_category_model(db_manager):
    """Test category model operations"""
    with db_manager.session_scope() as session:
        # Create parent category
        parent = CategoryModel(
            id="parent-id",
            name="Parent Category",
            description="Parent description"
        )
        session.add(parent)
        session.flush()
        
        # Create child category
        child = CategoryModel(
            id="child-id",
            name="Child Category",
            parent_id="parent-id"
        )
        session.add(child)
        session.flush()
        
        # Test relationships
        retrieved_parent = session.query(CategoryModel).filter_by(id="parent-id").first()
        assert len(retrieved_parent.children) == 1
        assert retrieved_parent.children[0].name == "Child Category"
        
        # Test get_path method
        retrieved_child = session.query(CategoryModel).filter_by(id="child-id").first()
        assert retrieved_child.get_path() == "Parent Category/Child Category"


def test_tag_model(db_manager):
    """Test tag model operations"""
    with db_manager.session_scope() as session:
        # Create tag
        tag = TagModel(
            id="tag-id",
            name="test-tag",
            color="#blue",
            description="Test tag"
        )
        session.add(tag)
        session.flush()
        
        # Query tag
        retrieved = session.query(TagModel).filter_by(id="tag-id").first()
        assert retrieved is not None
        assert retrieved.name == "test-tag"
        assert retrieved.color == "#blue"


def test_document_tags_relationship(db_manager):
    """Test many-to-many relationship between documents and tags"""
    with db_manager.session_scope() as session:
        # Create document
        doc = DocumentModel(
            id="doc-1",
            path="/test.txt",
            title="Test",
            content="Content",
            format="text",
            size=100,
            content_hash="hash"
        )
        
        # Create tags
        tag1 = TagModel(id="tag-1", name="python")
        tag2 = TagModel(id="tag-2", name="tutorial")
        
        # Associate tags with document
        doc.tags.append(tag1)
        doc.tags.append(tag2)
        
        session.add(doc)
        session.flush()
        
        # Query and verify relationships
        retrieved_doc = session.query(DocumentModel).filter_by(id="doc-1").first()
        assert len(retrieved_doc.tags) == 2
        tag_names = [tag.name for tag in retrieved_doc.tags]
        assert "python" in tag_names
        assert "tutorial" in tag_names
        
        # Verify reverse relationship
        retrieved_tag = session.query(TagModel).filter_by(name="python").first()
        assert len(retrieved_tag.documents) == 1
        assert retrieved_tag.documents[0].title == "Test"


def test_document_categories_relationship(db_manager):
    """Test many-to-many relationship between documents and categories"""
    with db_manager.session_scope() as session:
        # Create document
        doc = DocumentModel(
            id="doc-1",
            path="/test.txt",
            title="Test",
            content="Content",
            format="text",
            size=100,
            content_hash="hash"
        )
        
        # Create categories
        cat1 = CategoryModel(id="cat-1", name="Documentation")
        cat2 = CategoryModel(id="cat-2", name="API")
        
        # Associate categories with document
        doc.categories.append(cat1)
        doc.categories.append(cat2)
        
        session.add(doc)
        session.flush()
        
        # Query and verify relationships
        retrieved_doc = session.query(DocumentModel).filter_by(id="doc-1").first()
        assert len(retrieved_doc.categories) == 2
        cat_names = [cat.name for cat in retrieved_doc.categories]
        assert "Documentation" in cat_names
        assert "API" in cat_names


def test_document_repository(db_manager):
    """Test document repository operations"""
    with db_manager.session_scope() as session:
        repo = DocumentRepository(session)
        
        # Create document via repository
        from docscope.core.models import Document, DocumentFormat
        
        doc = Document(
            id=str(uuid.uuid4()),
            path="/repo-test.txt",
            title="Repository Test",
            content="Test content",
            format=DocumentFormat.TEXT,
            size=100,
            content_hash="hash",
            created_at=datetime.now(),
            modified_at=datetime.now(),
            tags=["test", "repository"]
        )
        
        db_doc = repo.create(doc)
        assert db_doc.id == doc.id
        
        # Get document
        retrieved = repo.get(doc.id)
        assert retrieved.title == "Repository Test"
        
        # Update document
        updates = {"title": "Updated Title", "content": "Updated content"}
        updated = repo.update(doc.id, updates)
        assert updated.title == "Updated Title"
        
        # List documents
        docs = repo.list(limit=10)
        assert len(docs) == 1
        
        # Count documents
        count = repo.count()
        assert count == 1
        
        # Delete document
        success = repo.delete(doc.id)
        assert success
        assert repo.get(doc.id) is None


def test_category_repository(db_manager):
    """Test category repository operations"""
    with db_manager.session_scope() as session:
        repo = CategoryRepository(session)
        
        # Create category
        cat = repo.create("Test Category", description="Test")
        assert cat.name == "Test Category"
        
        # Get category
        retrieved = repo.get(cat.id)
        assert retrieved.name == "Test Category"
        
        # Get by name
        by_name = repo.get_by_name("Test Category")
        assert by_name.id == cat.id
        
        # Create child category
        child = repo.create("Child", parent_id=cat.id)
        assert child.parent_id == cat.id
        
        # List categories
        roots = repo.list(parent_id=None)
        assert len(roots) == 1
        
        children = repo.list(parent_id=cat.id)
        assert len(children) == 1
        
        # Get tree
        tree = repo.get_tree()
        assert len(tree) == 1
        assert len(tree[0].children) == 1


def test_tag_repository(db_manager):
    """Test tag repository operations"""
    with db_manager.session_scope() as session:
        repo = TagRepository(session)
        
        # Create tag
        tag = repo.create("python", color="#blue")
        assert tag.name == "python"
        
        # Get tag
        retrieved = repo.get(tag.id)
        assert retrieved.name == "python"
        
        # Get by name
        by_name = repo.get_by_name("python")
        assert by_name.id == tag.id
        
        # Get or create (existing)
        existing = repo.get_or_create("python")
        assert existing.id == tag.id
        
        # Get or create (new)
        new_tag = repo.get_or_create("javascript", color="#yellow")
        assert new_tag.name == "javascript"
        assert new_tag.id != tag.id
        
        # List tags
        tags = repo.list(limit=10)
        assert len(tags) == 2
        
        # Merge tags
        tag3 = repo.create("js")
        success = repo.merge(tag3.id, new_tag.id)
        assert success
        assert repo.get(tag3.id) is None


def test_database_stats(db_manager):
    """Test database statistics"""
    with db_manager.session_scope() as session:
        # Add some data
        for i in range(5):
            doc = DocumentModel(
                id=f"doc-{i}",
                path=f"/test{i}.txt",
                title=f"Document {i}",
                content="Content",
                format="text",
                size=100,
                content_hash=f"hash{i}"
            )
            session.add(doc)
        
        cat = CategoryModel(id="cat-1", name="Test Category")
        session.add(cat)
        
        tag = TagModel(id="tag-1", name="test-tag")
        session.add(tag)
    
    # Get stats
    stats = db_manager.get_stats()
    assert stats["backend"] == "sqlite"
    assert stats["initialized"] is True
    assert stats["documents"] == 5
    assert stats["categories"] == 1
    assert stats["tags"] == 1
    assert "size_mb" in stats


def test_sqlite_fts_index(db_manager):
    """Test SQLite full-text search index creation"""
    # FTS index should be created automatically for SQLite
    with db_manager.engine.connect() as conn:
        # Check if FTS table exists
        from sqlalchemy import text
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='documents_fts'"
        ))
        assert result.fetchone() is not None


def test_database_vacuum(db_manager):
    """Test database vacuum operation"""
    # Add and delete some data to create fragmentation
    with db_manager.session_scope() as session:
        for i in range(10):
            doc = DocumentModel(
                id=f"doc-{i}",
                path=f"/test{i}.txt",
                title=f"Document {i}",
                content="Content" * 100,  # Larger content
                format="text",
                size=1000,
                content_hash=f"hash{i}"
            )
            session.add(doc)
    
    # Delete half the documents
    with db_manager.session_scope() as session:
        docs = session.query(DocumentModel).limit(5).all()
        for doc in docs:
            session.delete(doc)
    
    # Vacuum database
    db_manager.vacuum()
    
    # Database should still work after vacuum
    with db_manager.session_scope() as session:
        count = session.query(DocumentModel).count()
        assert count == 5


def test_transaction_rollback(db_manager):
    """Test transaction rollback on error"""
    try:
        with db_manager.session_scope() as session:
            # Add a document
            doc = DocumentModel(
                id="test-doc",
                path="/test.txt",
                title="Test",
                content="Content",
                format="text",
                size=100,
                content_hash="hash"
            )
            session.add(doc)
            session.flush()
            
            # Force an error
            raise Exception("Test error")
    except Exception:
        pass
    
    # Document should not be saved due to rollback
    with db_manager.session_scope() as session:
        doc = session.query(DocumentModel).filter_by(id="test-doc").first()
        assert doc is None