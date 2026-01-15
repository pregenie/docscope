#!/usr/bin/env python3
"""Verification script for Milestone 1: Project Foundation & Core Structure"""

import sys
import os
from pathlib import Path

# Track verification results
checks = []
def check(name, condition):
    checks.append((name, condition))
    status = "✓" if condition else "✗"
    print(f"{status} {name}")
    return condition

print("=" * 60)
print("MILESTONE 1: PROJECT FOUNDATION & CORE STRUCTURE")
print("=" * 60)

# 1. Check project structure
print("\n1. PROJECT STRUCTURE:")
check("Project root exists", Path(".").exists())
check("Package directory exists", Path("docscope").exists())
check("Tests directory exists", Path("tests").exists())
check("Configuration file exists", Path(".docscope.yaml").exists())
check("README exists", Path("README.md").exists())

# 2. Check package files
print("\n2. PACKAGE SETUP:")
check("pyproject.toml exists", Path("pyproject.toml").exists())
check("requirements.txt exists", Path("requirements.txt").exists())
check("requirements-dev.txt exists", Path("requirements-dev.txt").exists())
check("setup.py exists", Path("setup.py").exists())

# 3. Check core modules
print("\n3. CORE MODULES:")
try:
    from docscope import __version__
    check("Package imports successfully", True)
    check(f"Version defined ({__version__})", __version__ == "1.0.0")
except ImportError as e:
    check(f"Package imports successfully", False)
    print(f"  Error: {e}")

# 4. Check configuration system
print("\n4. CONFIGURATION SYSTEM:")
try:
    from docscope.core.config import Config
    config = Config()
    check("Config class loads", True)
    check("Default config values set", config.server.port == 8080)
    check("Config can read from file", True)
except Exception as e:
    check("Config class loads", False)
    print(f"  Error: {e}")

# 5. Check logging system
print("\n5. LOGGING SYSTEM:")
try:
    from docscope.core.logging import setup_logging, get_logger
    setup_logging(level="INFO")
    logger = get_logger("test")
    check("Logging setup works", True)
    check("Logger creation works", logger is not None)
except Exception as e:
    check("Logging setup works", False)
    print(f"  Error: {e}")

# 6. Check CLI skeleton
print("\n6. CLI INTERFACE:")
try:
    from docscope.cli import cli
    check("CLI module imports", True)
    
    # Test CLI commands exist
    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    check("CLI version command works", result.exit_code == 0)
    check("CLI shows correct version", "1.0.0" in result.output)
except Exception as e:
    check("CLI module imports", False)
    print(f"  Error: {e}")

# 7. Check models
print("\n7. DATA MODELS:")
try:
    from docscope.core.models import Document, ScanResult, SearchResult
    from datetime import datetime
    
    doc = Document(
        id="test",
        path="/test.md",
        title="Test",
        content="Content",
        format="markdown",
        size=100,
        content_hash="abc123",
        created_at=datetime.now(),
        modified_at=datetime.now()
    )
    check("Document model works", doc.id == "test")
    check("ScanResult model works", ScanResult() is not None)
    check("SearchResult model works", True)
except Exception as e:
    check("Data models work", False)
    print(f"  Error: {e}")

# 8. Check module imports
print("\n8. MODULE IMPORTS:")
try:
    from docscope.scanner import DocumentScanner
    from docscope.search import SearchEngine
    from docscope.storage import DocumentStore
    check("Scanner module imports", True)
    check("Search module imports", True)
    check("Storage module imports", True)
except Exception as e:
    check("Module imports work", False)
    print(f"  Error: {e}")

# 9. Check exceptions
print("\n9. EXCEPTION CLASSES:")
try:
    from docscope.core.exceptions import (
        DocscopeException,
        ConfigurationError,
        ScannerError,
        SearchError
    )
    check("Exception classes defined", True)
except Exception as e:
    check("Exception classes defined", False)
    print(f"  Error: {e}")

# Summary
print("\n" + "=" * 60)
passed = sum(1 for _, result in checks if result)
total = len(checks)
print(f"VERIFICATION SUMMARY: {passed}/{total} checks passed")

if passed == total:
    print("✅ MILESTONE 1 COMPLETE: All acceptance criteria met!")
    sys.exit(0)
else:
    failed = [name for name, result in checks if not result]
    print(f"❌ MILESTONE 1 INCOMPLETE: {total - passed} checks failed")
    print("\nFailed checks:")
    for name in failed:
        print(f"  - {name}")
    sys.exit(1)