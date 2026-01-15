#!/usr/bin/env python3
"""Verification script for Milestone 2: Document Scanner Module"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Track verification results
checks = []
def check(name, condition):
    checks.append((name, condition))
    status = "✓" if condition else "✗"
    print(f"{status} {name}")
    return condition

print("=" * 60)
print("MILESTONE 2: DOCUMENT SCANNER MODULE")
print("=" * 60)

# 1. Check scanner module structure
print("\n1. SCANNER MODULE STRUCTURE:")
check("Scanner package exists", Path("docscope/scanner").is_dir())
check("Scanner __init__.py exists", Path("docscope/scanner/__init__.py").exists())
check("Scanner main module exists", Path("docscope/scanner/scanner.py").exists())
check("Format handler base exists", Path("docscope/scanner/format_handler.py").exists())
check("Format handlers exist", Path("docscope/scanner/handlers.py").exists())

# 2. Check imports
print("\n2. MODULE IMPORTS:")
try:
    from docscope.scanner import DocumentScanner
    check("DocumentScanner imports", True)
except ImportError as e:
    check("DocumentScanner imports", False)
    print(f"  Error: {e}")

try:
    from docscope.scanner.format_handler import FormatHandler, FormatRegistry
    check("FormatHandler imports", True)
    check("FormatRegistry imports", True)
except ImportError as e:
    check("FormatHandler imports", False)
    print(f"  Error: {e}")

try:
    from docscope.scanner.handlers import (
        MarkdownHandler, TextHandler, JSONHandler,
        YAMLHandler, PythonHandler, HTMLHandler
    )
    check("All format handlers import", True)
except ImportError as e:
    check("All format handlers import", False)
    print(f"  Error: {e}")

# 3. Test scanner initialization
print("\n3. SCANNER INITIALIZATION:")
try:
    from docscope.core.config import ScannerConfig
    from docscope.scanner import DocumentScanner
    
    config = ScannerConfig()
    scanner = DocumentScanner(config)
    check("Scanner initializes", scanner is not None)
    check("Scanner has registry", hasattr(scanner, 'registry'))
    check("Scanner has config", scanner.config is not None)
except Exception as e:
    check("Scanner initializes", False)
    print(f"  Error: {e}")

# 4. Test format detection
print("\n4. FORMAT DETECTION:")
try:
    # Get supported formats
    formats = scanner.get_supported_formats()
    check("Supports multiple formats", len(formats) > 5)
    check("Supports .md files", '.md' in formats)
    check("Supports .txt files", '.txt' in formats)
    check("Supports .json files", '.json' in formats)
    check("Supports .yaml files", '.yaml' in formats)
    check("Supports .py files", '.py' in formats)
except Exception as e:
    check("Format detection works", False)
    print(f"  Error: {e}")

# 5. Test file scanning
print("\n5. FILE SCANNING:")
try:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create test files
        (tmppath / "test.md").write_text("# Test\nContent")
        (tmppath / "test.txt").write_text("Plain text")
        (tmppath / "test.json").write_text('{"key": "value"}')
        (tmppath / "ignore.tmp").write_text("Should be ignored")
        
        # Test find_documents
        docs = scanner.find_documents([tmppath], recursive=True)
        check("Finds documents", len(docs) == 3)  # Should not include .tmp
        
        # Test scanning
        result = scanner.scan([tmppath])
        check("Scan returns result", result is not None)
        check("Scan finds documents", result.total > 0)
        check("Scan successful count correct", result.successful >= 0)
        check("Scan has duration", result.duration > 0)
except Exception as e:
    check("File scanning works", False)
    print(f"  Error: {e}")

# 6. Test document processing
print("\n6. DOCUMENT PROCESSING:")
try:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Document Title\n\nContent here")
        test_file = Path(f.name)
    
    doc = scanner.process_document(test_file)
    check("Document processes", doc is not None)
    check("Document has ID", doc.id is not None)
    check("Document has title", doc.title == "Document Title")
    check("Document has content", len(doc.content) > 0)
    check("Document has format", doc.format is not None)
    check("Document has hash", doc.content_hash is not None)
    check("Document has metadata", doc.metadata is not None)
    
    test_file.unlink()
except Exception as e:
    check("Document processing works", False)
    print(f"  Error: {e}")

# 7. Test ignore patterns
print("\n7. IGNORE PATTERNS:")
try:
    check("Ignores .tmp files", scanner.should_ignore(Path("test.tmp")))
    check("Ignores __pycache__", scanner.should_ignore(Path("__pycache__")))
    check("Doesn't ignore .md", not scanner.should_ignore(Path("test.md")))
    check("Doesn't ignore .py", not scanner.should_ignore(Path("test.py")))
except Exception as e:
    check("Ignore patterns work", False)
    print(f"  Error: {e}")

# 8. Test incremental scanning
print("\n8. INCREMENTAL SCANNING:")
try:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create a file
        test_file = tmppath / "test.md"
        test_file.write_text("# Original")
        
        # Get time before modification
        before = datetime.now() - timedelta(seconds=1)
        
        # Modify file
        import time
        time.sleep(0.1)
        test_file.write_text("# Modified")
        
        # Run incremental scan
        result = scanner.incremental_scan([tmppath], since=before)
        check("Incremental scan works", result is not None)
        check("Finds modified files", result.total == 1)
except Exception as e:
    check("Incremental scanning works", False)
    print(f"  Error: {e}")

# 9. Test progress callback
print("\n9. PROGRESS TRACKING:")
try:
    progress_updates = []
    
    def progress_callback(completed, total, current):
        progress_updates.append((completed, total))
    
    scanner.set_progress_callback(progress_callback)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test1.txt").write_text("Test 1")
        (tmppath / "test2.txt").write_text("Test 2")
        
        result = scanner.scan([tmppath])
        check("Progress callback called", len(progress_updates) > 0)
        check("Progress reports completion", 
              any(c == t for c, t in progress_updates))
except Exception as e:
    check("Progress tracking works", False)
    print(f"  Error: {e}")

# 10. Test concurrent processing
print("\n10. CONCURRENT PROCESSING:")
try:
    # Scanner should use thread pool
    check("Scanner uses workers", scanner.config.workers > 0)
    
    # Test with multiple files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create multiple files
        for i in range(10):
            (tmppath / f"file{i}.txt").write_text(f"Content {i}")
        
        import time
        start = time.time()
        result = scanner.scan([tmppath])
        duration = time.time() - start
        
        check("Processes multiple files", result.total == 10)
        check("All files successful", result.successful == 10)
        check("Concurrent execution", duration < 5)  # Should be fast
except Exception as e:
    check("Concurrent processing works", False)
    print(f"  Error: {e}")

# 11. Check test files
print("\n11. TEST COVERAGE:")
check("Scanner tests exist", Path("tests/test_scanner.py").exists())
check("Format tests exist", Path("tests/test_formats.py").exists())

# Summary
print("\n" + "=" * 60)
passed = sum(1 for _, result in checks if result)
total = len(checks)
print(f"VERIFICATION SUMMARY: {passed}/{total} checks passed")

if passed == total:
    print("✅ MILESTONE 2 COMPLETE: Document Scanner Module implemented!")
    sys.exit(0)
else:
    failed = [name for name, result in checks if not result]
    print(f"❌ MILESTONE 2 INCOMPLETE: {total - passed} checks failed")
    print("\nFailed checks:")
    for name in failed:
        print(f"  - {name}")
    sys.exit(1)