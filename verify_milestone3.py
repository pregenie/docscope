#!/usr/bin/env python3
"""Verification script for Milestone 3: Storage Layer & Database"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime
import uuid

# Track verification results
checks = []
def check(name, condition):
    checks.append((name, condition))
    status = "✓" if condition else "✗"
    print(f"{status} {name}")
    return condition

print("=" * 60)
print("MILESTONE 3: STORAGE LAYER & DATABASE")
print("=" * 60)

# 1. Check storage module structure
print("\n1. STORAGE MODULE STRUCTURE:")
check("Storage package exists", Path("docscope/storage").is_dir())
check("Storage __init__.py exists", Path("docscope/storage/__init__.py").exists())
check("Database module exists", Path("docscope/storage/database.py").exists())
check("Models module exists", Path("docscope/storage/models.py").exists())
check("Repository module exists", Path("docscope/storage/repository.py").exists())
check("Storage interface exists", Path("docscope/storage/storage.py").exists())

# 2. Check imports
print("\n2. MODULE IMPORTS:")
try:
    from docscope.storage import DocumentStore
    check("DocumentStore imports", True)
except ImportError as e:
    check("DocumentStore imports", False)
    print(f"  Error: {e}")

try:
    from docscope.storage.database import DatabaseManager
    check("DatabaseManager imports", True)
except ImportError as e:
    check("DatabaseManager imports", False)
    print(f"  Error: {e}")

try:
    from docscope.storage.models import DocumentModel, CategoryModel, TagModel
    check("Database models import", True)
except ImportError as e:
    check("Database models import", False)
    print(f"  Error: {e}")

try:
    from docscope.storage.repository import (
        DocumentRepository, CategoryRepository, TagRepository
    )
    check("Repository classes import", True)
except ImportError as e:
    check("Repository classes import", False)
    print(f"  Error: {e}")

# 3. Test storage initialization
print("\n3. STORAGE INITIALIZATION:")
try:
    from docscope.core.config import StorageConfig
    from docscope.storage import DocumentStore
    
    # Use temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    config = StorageConfig(backend="sqlite", sqlite={"path": db_path})
    store = DocumentStore(config)
    check("Storage initializes", store is not None)
    
    store.initialize()
    check("Database creates", Path(db_path).exists())
    check("Storage initialized flag", store._initialized)
    
    store.close()
    Path(db_path).unlink()
except Exception as e:
    check("Storage initialization works", False)
    print(f"  Error: {e}")

# 4. Test document CRUD operations
print("\n4. DOCUMENT CRUD OPERATIONS:")
try:
    from docscope.core.models import Document, DocumentFormat, DocumentStatus
    
    # Create temporary store
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    config = StorageConfig(backend="sqlite", sqlite={"path": db_path})
    store = DocumentStore(config)
    store.initialize(drop_existing=True)
    
    # Test Create
    doc = Document(
        id=str(uuid.uuid4()),
        path="/test/doc.txt",
        title="Test Document",
        content="Test content",
        format=DocumentFormat.TEXT,
        size=100,
        content_hash="hash123",
        created_at=datetime.now(),
        modified_at=datetime.now()
    )
    
    doc_id = store.store_document(doc)
    check("Document creates", doc_id is not None)
    
    # Test Read
    retrieved = store.get_document(doc_id)
    check("Document retrieves", retrieved is not None)
    check("Document data correct", retrieved.title == "Test Document")
    
    # Test Update
    success = store.update_document(doc_id, {"title": "Updated"})
    check("Document updates", success)
    
    updated = store.get_document(doc_id)
    check("Update persists", updated.title == "Updated")
    
    # Test Delete
    success = store.delete_document(doc_id)
    check("Document deletes", success)
    
    deleted = store.get_document(doc_id)
    check("Deletion confirmed", deleted is None)
    
    store.close()
    Path(db_path).unlink()
except Exception as e:
    check("CRUD operations work", False)
    print(f"  Error: {e}")

# 5. Test document listing and filtering
print("\n5. DOCUMENT LISTING & FILTERING:")
try:
    # Create temporary store with multiple documents
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    config = StorageConfig(backend="sqlite", sqlite={"path": db_path})
    store = DocumentStore(config)
    store.initialize(drop_existing=True)
    
    # Add multiple documents
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
        store.store_document(doc)
    
    # Test listing
    docs = store.list_documents(limit=10)
    check("Documents list", len(docs) == 5)
    
    # Test filtering
    md_docs = store.list_documents(format="markdown")
    check("Format filter works", len(md_docs) == 3)
    
    # Test counting
    count = store.count_documents()
    check("Document count works", count == 5)
    
    store.close()
    Path(db_path).unlink()
except Exception as e:
    check("Listing and filtering work", False)
    print(f"  Error: {e}")

# 6. Test categories and tags
print("\n6. CATEGORIES & TAGS:")
try:
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    config = StorageConfig(backend="sqlite", sqlite={"path": db_path})
    store = DocumentStore(config)
    store.initialize(drop_existing=True)
    
    # Create category
    cat_id = store.create_category("Documentation")
    check("Category creates", cat_id is not None)
    
    # List categories
    categories = store.list_categories()
    check("Categories list", len(categories) == 1)
    
    # Create tag
    tag_id = store.create_tag("python")
    check("Tag creates", tag_id is not None)
    
    # List tags
    tags = store.list_tags()
    check("Tags list", len(tags) == 1)
    
    store.close()
    Path(db_path).unlink()
except Exception as e:
    check("Categories and tags work", False)
    print(f"  Error: {e}")

# 7. Test database backend
print("\n7. DATABASE BACKEND:")
try:
    from docscope.storage.database import DatabaseManager
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    config = StorageConfig(backend="sqlite", sqlite={"path": db_path})
    manager = DatabaseManager(config)
    
    check("Database manager creates", manager is not None)
    
    manager.initialize()
    check("Database initializes", manager._initialized)
    
    # Test session
    with manager.session_scope() as session:
        check("Session creates", session is not None)
    
    # Test stats
    stats = manager.get_stats()
    check("Stats available", "backend" in stats)
    check("Backend is SQLite", stats["backend"] == "sqlite")
    
    manager.close()
    Path(db_path).unlink()
except Exception as e:
    check("Database backend works", False)
    print(f"  Error: {e}")

# 8. Test SQLAlchemy models
print("\n8. SQLALCHEMY MODELS:")
try:
    from docscope.storage.models import DocumentModel, CategoryModel, TagModel
    
    check("DocumentModel has required fields", 
          hasattr(DocumentModel, 'id') and 
          hasattr(DocumentModel, 'path') and
          hasattr(DocumentModel, 'content'))
    
    check("CategoryModel has relationships", 
          hasattr(CategoryModel, 'documents') and
          hasattr(CategoryModel, 'parent'))
    
    check("TagModel has relationships", 
          hasattr(TagModel, 'documents'))
    
    check("Models have to_dict method",
          hasattr(DocumentModel, 'to_dict') and
          hasattr(CategoryModel, 'to_dict') and
          hasattr(TagModel, 'to_dict'))
except Exception as e:
    check("SQLAlchemy models work", False)
    print(f"  Error: {e}")

# 9. Test repositories
print("\n9. REPOSITORY PATTERN:")
try:
    from docscope.storage.repository import DocumentRepository
    from docscope.storage.database import DatabaseManager
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    config = StorageConfig(backend="sqlite", sqlite={"path": db_path})
    manager = DatabaseManager(config)
    manager.initialize(drop_existing=True)
    
    with manager.session_scope() as session:
        repo = DocumentRepository(session)
        check("Repository creates", repo is not None)
        check("Repository has CRUD methods",
              hasattr(repo, 'create') and
              hasattr(repo, 'get') and
              hasattr(repo, 'update') and
              hasattr(repo, 'delete'))
        check("Repository has query methods",
              hasattr(repo, 'list') and
              hasattr(repo, 'count'))
    
    manager.close()
    Path(db_path).unlink()
except Exception as e:
    check("Repository pattern works", False)
    print(f"  Error: {e}")

# 10. Test transaction support
print("\n10. TRANSACTION SUPPORT:")
try:
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    config = StorageConfig(backend="sqlite", sqlite={"path": db_path})
    store = DocumentStore(config)
    store.initialize(drop_existing=True)
    
    # Test transaction rollback
    doc = Document(
        id="test-rollback",
        path="/rollback.txt",
        title="Rollback Test",
        content="Content",
        format=DocumentFormat.TEXT,
        size=100,
        content_hash="hash",
        created_at=datetime.now(),
        modified_at=datetime.now()
    )
    
    # This should work in a transaction
    doc_id = store.store_document(doc)
    check("Transaction commits", doc_id is not None)
    
    # Verify it was saved
    retrieved = store.get_document(doc_id)
    check("Transaction persisted", retrieved is not None)
    
    store.close()
    Path(db_path).unlink()
except Exception as e:
    check("Transaction support works", False)
    print(f"  Error: {e}")

# 11. Check test files
print("\n11. TEST COVERAGE:")
check("Storage tests exist", Path("tests/test_storage.py").exists())
check("Database tests exist", Path("tests/test_database.py").exists())

# Summary
print("\n" + "=" * 60)
passed = sum(1 for _, result in checks if result)
total = len(checks)
print(f"VERIFICATION SUMMARY: {passed}/{total} checks passed")

if passed == total:
    print("✅ MILESTONE 3 COMPLETE: Storage Layer & Database implemented!")
    sys.exit(0)
else:
    failed = [name for name, result in checks if not result]
    print(f"❌ MILESTONE 3 INCOMPLETE: {total - passed} checks failed")
    print("\nFailed checks:")
    for name in failed:
        print(f"  - {name}")
    sys.exit(1)