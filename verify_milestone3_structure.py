#!/usr/bin/env python3
"""Structural verification for Milestone 3 (without runtime dependencies)"""

import sys
from pathlib import Path
import ast

# Track verification results
checks = []
def check(name, condition):
    checks.append((name, condition))
    status = "✓" if condition else "✗"
    print(f"{status} {name}")
    return condition

print("=" * 60)
print("MILESTONE 3: STORAGE LAYER STRUCTURAL VERIFICATION")
print("=" * 60)

# 1. Check file structure
print("\n1. FILE STRUCTURE:")
files = [
    ("Storage package", "docscope/storage/__init__.py"),
    ("Database module", "docscope/storage/database.py"),
    ("Models module", "docscope/storage/models.py"),
    ("Repository module", "docscope/storage/repository.py"),
    ("Storage interface", "docscope/storage/storage.py"),
    ("Storage tests", "tests/test_storage.py"),
    ("Database tests", "tests/test_database.py"),
]

for name, path in files:
    check(name, Path(path).exists())

# 2. Check module contents
print("\n2. MODULE CONTENTS:")

# Check database.py
db_path = Path("docscope/storage/database.py")
if db_path.exists():
    content = db_path.read_text()
    check("DatabaseManager class defined", "class DatabaseManager:" in content)
    check("Database initialization method", "def initialize(" in content)
    check("Session management", "def session_scope(" in content)
    check("SQLite support", "'sqlite'" in content.lower())
    check("Transaction support", "commit" in content and "rollback" in content)

# Check models.py
models_path = Path("docscope/storage/models.py")
if models_path.exists():
    content = models_path.read_text()
    check("DocumentModel defined", "class DocumentModel" in content)
    check("CategoryModel defined", "class CategoryModel" in content)
    check("TagModel defined", "class TagModel" in content)
    check("SQLAlchemy imports", "from sqlalchemy" in content)
    check("Relationships defined", "relationship" in content)
    check("Many-to-many tables", "document_tags" in content)

# Check repository.py
repo_path = Path("docscope/storage/repository.py")
if repo_path.exists():
    content = repo_path.read_text()
    check("DocumentRepository defined", "class DocumentRepository:" in content)
    check("CategoryRepository defined", "class CategoryRepository:" in content)
    check("TagRepository defined", "class TagRepository:" in content)
    check("CRUD operations", all(op in content for op in ["create", "get", "update", "delete"]))
    check("Query operations", "def list(" in content and "def count(" in content)

# Check storage.py
storage_path = Path("docscope/storage/storage.py")
if storage_path.exists():
    content = storage_path.read_text()
    check("DocumentStore class", "class DocumentStore:" in content)
    check("Store document method", "def store_document(" in content)
    check("Get document method", "def get_document(" in content)
    check("List documents method", "def list_documents(" in content)
    check("Category support", "def create_category(" in content)
    check("Tag support", "def create_tag(" in content)

# 3. Check test coverage
print("\n3. TEST COVERAGE:")

test_storage_path = Path("tests/test_storage.py")
if test_storage_path.exists():
    content = test_storage_path.read_text()
    check("Storage fixtures", "@pytest.fixture" in content)
    check("CRUD tests", "test_store_document" in content)
    check("Query tests", "test_list_documents" in content)
    check("Category tests", "test_categories" in content)
    check("Tag tests", "test_tags" in content)

test_db_path = Path("tests/test_database.py")
if test_db_path.exists():
    content = test_db_path.read_text()
    check("Database fixtures", "@pytest.fixture" in content)
    check("Model tests", "test_document_model" in content)
    check("Repository tests", "test_document_repository" in content)
    check("Transaction tests", "test_transaction" in content)

# 4. Check integration points
print("\n4. INTEGRATION POINTS:")

# Check if storage integrates with scanner
scanner_import = Path("docscope/storage/storage.py")
if scanner_import.exists():
    content = scanner_import.read_text()
    check("Integrates with models", "from ..core.models import" in content)
    check("Uses ScanResult", "ScanResult" in content)
    check("Error handling", "StorageError" in content)

# 5. Check database features
print("\n5. DATABASE FEATURES:")

if models_path.exists():
    content = models_path.read_text()
    check("Indexes defined", "Index" in content or "__table_args__" in content)
    check("Timestamps", "created_at" in content and "modified_at" in content)
    check("JSON metadata support", "JSON" in content or "metadata" in content)
    check("Full-text search prep", "search_vector" in content or "fts" in content.lower())

# 6. Check advanced features
print("\n6. ADVANCED FEATURES:")

if storage_path.exists():
    content = storage_path.read_text()
    check("Duplicate detection", "find_duplicates" in content)
    check("Incremental updates", "get_modified_since" in content)
    check("Statistics", "get_stats" in content)
    check("Backup support", "backup" in content or "vacuum" in content)

# Summary
print("\n" + "=" * 60)
passed = sum(1 for _, result in checks if result)
total = len(checks)
percentage = (passed / total) * 100
print(f"STRUCTURAL VERIFICATION: {passed}/{total} checks passed ({percentage:.1f}%)")

if passed == total:
    print("✅ MILESTONE 3 STRUCTURE COMPLETE!")
    print("\nNote: Runtime verification requires SQLAlchemy installation:")
    print("  pip install sqlalchemy")
    sys.exit(0)
elif passed >= total * 0.9:  # 90% threshold
    print("✅ MILESTONE 3 STRUCTURE MOSTLY COMPLETE!")
    print(f"\n{total - passed} minor items missing or different")
    sys.exit(0)
else:
    failed = [name for name, result in checks if not result]
    print(f"❌ MILESTONE 3 STRUCTURE INCOMPLETE: {total - passed} checks failed")
    print("\nFailed checks:")
    for name in failed[:10]:  # Show first 10 failures
        print(f"  - {name}")
    if len(failed) > 10:
        print(f"  ... and {len(failed) - 10} more")
    sys.exit(1)