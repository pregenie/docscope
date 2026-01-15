"""Tests for document scanner"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import time

from docscope.scanner import DocumentScanner
from docscope.scanner.handlers import (
    MarkdownHandler,
    TextHandler,
    JSONHandler,
    YAMLHandler,
    PythonHandler,
)
from docscope.core.config import ScannerConfig
from docscope.core.models import DocumentStatus, DocumentFormat


@pytest.fixture
def scanner_config():
    """Create scanner configuration for tests"""
    return ScannerConfig(
        paths=[],
        ignore=["*.tmp", "__pycache__"],
        formats={
            "markdown": {"enabled": True},
            "text": {"enabled": True},
            "json": {"enabled": True},
            "yaml": {"enabled": True},
            "code": {"enabled": True},
        },
        workers=2
    )


@pytest.fixture
def scanner(scanner_config):
    """Create scanner instance"""
    return DocumentScanner(scanner_config)


@pytest.fixture
def test_files(tmp_path):
    """Create test files of various formats"""
    files = {}
    
    # Markdown file
    md_file = tmp_path / "test.md"
    md_file.write_text("""# Test Document

This is a test markdown document.

## Section 1
Some content here.

[Link](https://example.com)
![Image](image.png)
""")
    files['markdown'] = md_file
    
    # Text file
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("This is a plain text file.\nWith multiple lines.")
    files['text'] = txt_file
    
    # JSON file
    json_file = tmp_path / "test.json"
    json_file.write_text('{"name": "test", "value": 42, "items": [1, 2, 3]}')
    files['json'] = json_file
    
    # YAML file
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text("""
name: test
value: 42
items:
  - one
  - two
  - three
""")
    files['yaml'] = yaml_file
    
    # Python file
    py_file = tmp_path / "test.py"
    py_file.write_text('''"""Test module docstring"""

import os
import sys

class TestClass:
    """Test class"""
    
    def test_method(self):
        """Test method"""
        return "test"

def test_function():
    """Test function"""
    pass
''')
    files['python'] = py_file
    
    # File to ignore
    tmp_file = tmp_path / "ignore.tmp"
    tmp_file.write_text("This should be ignored")
    files['ignore'] = tmp_file
    
    # Create subdirectory with files
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    sub_md = subdir / "sub.md"
    sub_md.write_text("# Subdirectory Document")
    files['subdir_md'] = sub_md
    
    return files


def test_scanner_initialization(scanner):
    """Test scanner initialization"""
    assert scanner is not None
    assert scanner.config is not None
    assert scanner.registry is not None
    assert len(scanner.registry.list_handlers()) > 0


def test_find_documents_file(scanner, test_files):
    """Test finding documents with single file"""
    docs = scanner.find_documents([test_files['markdown']])
    assert len(docs) == 1
    assert docs[0] == test_files['markdown']


def test_find_documents_directory(scanner, test_files):
    """Test finding documents in directory"""
    docs = scanner.find_documents([test_files['markdown'].parent], recursive=False)
    # Should find all files except the ignored one
    assert len(docs) == 5  # md, txt, json, yaml, py (not tmp)
    
    # Check that tmp file is not included
    doc_names = [d.name for d in docs]
    assert 'ignore.tmp' not in doc_names


def test_find_documents_recursive(scanner, test_files):
    """Test recursive document finding"""
    docs = scanner.find_documents([test_files['markdown'].parent], recursive=True)
    # Should find all files including subdirectory
    assert len(docs) == 6  # All files except .tmp
    
    # Check subdirectory file is included
    doc_names = [d.name for d in docs]
    assert 'sub.md' in doc_names


def test_should_ignore(scanner, test_files):
    """Test ignore pattern matching"""
    assert scanner.should_ignore(Path("test.tmp"))
    assert scanner.should_ignore(Path("__pycache__"))
    assert not scanner.should_ignore(Path("test.md"))
    assert not scanner.should_ignore(Path("test.txt"))


def test_process_markdown(scanner, test_files):
    """Test processing markdown file"""
    doc = scanner.process_document(test_files['markdown'])
    
    assert doc is not None
    assert doc.format == DocumentFormat.MARKDOWN
    assert doc.title == "Test Document"
    assert "# Test Document" in doc.content
    assert doc.status == DocumentStatus.INDEXED
    assert doc.size > 0
    assert doc.content_hash is not None
    
    # Check metadata
    assert 'headers' in doc.metadata
    assert 'links' in doc.metadata
    assert 'images' in doc.metadata
    assert len(doc.metadata['headers']) == 2
    assert len(doc.metadata['links']) == 1
    assert len(doc.metadata['images']) == 1


def test_process_text(scanner, test_files):
    """Test processing text file"""
    doc = scanner.process_document(test_files['text'])
    
    assert doc is not None
    assert doc.format == DocumentFormat.TEXT
    assert doc.content == "This is a plain text file.\nWith multiple lines."
    assert doc.status == DocumentStatus.INDEXED
    
    # Check metadata
    assert doc.metadata['line_count'] == 2
    assert doc.metadata['word_count'] == 9


def test_process_json(scanner, test_files):
    """Test processing JSON file"""
    doc = scanner.process_document(test_files['json'])
    
    assert doc is not None
    assert doc.format == DocumentFormat.JSON
    assert doc.status == DocumentStatus.INDEXED
    
    # Check metadata
    assert doc.metadata['valid'] is True
    assert 'keys' in doc.metadata
    assert doc.metadata['key_count'] == 3


def test_process_yaml(scanner, test_files):
    """Test processing YAML file"""
    doc = scanner.process_document(test_files['yaml'])
    
    assert doc is not None
    assert doc.format == DocumentFormat.YAML
    assert doc.status == DocumentStatus.INDEXED
    
    # Check metadata
    assert doc.metadata['valid'] is True
    assert 'keys' in doc.metadata


def test_process_python(scanner, test_files):
    """Test processing Python file"""
    doc = scanner.process_document(test_files['python'])
    
    assert doc is not None
    assert doc.format == DocumentFormat.CODE
    assert doc.title == "Test module docstring"
    assert doc.status == DocumentStatus.INDEXED
    
    # Check metadata
    assert doc.metadata['language'] == 'python'
    assert 'imports' in doc.metadata
    assert 'classes' in doc.metadata
    assert 'functions' in doc.metadata
    assert 'TestClass' in doc.metadata['classes']
    assert 'test_function' in doc.metadata['functions']


def test_scan_multiple_files(scanner, test_files):
    """Test scanning multiple files"""
    result = scanner.scan([test_files['markdown'].parent], recursive=False)
    
    assert result.total >= 5
    assert result.successful >= 5
    assert result.failed == 0
    assert len(result.documents) >= 5
    assert result.duration > 0
    
    # Check document formats
    formats = [doc.format for doc in result.documents]
    assert DocumentFormat.MARKDOWN in formats
    assert DocumentFormat.TEXT in formats
    assert DocumentFormat.JSON in formats


def test_scan_with_progress_callback(scanner, test_files):
    """Test scan with progress callback"""
    progress_calls = []
    
    def progress_callback(completed, total, current_file):
        progress_calls.append((completed, total, current_file))
    
    scanner.set_progress_callback(progress_callback)
    result = scanner.scan([test_files['markdown'].parent], recursive=True)
    
    assert len(progress_calls) > 0
    # Last call should have completed == total
    last_call = progress_calls[-1]
    assert last_call[0] == last_call[1]


def test_incremental_scan(scanner, test_files):
    """Test incremental scanning"""
    # Get current time
    now = datetime.now()
    
    # Scan all files first
    initial_result = scanner.scan([test_files['markdown'].parent])
    
    # Wait a moment and modify a file
    time.sleep(0.1)
    test_files['markdown'].write_text("# Updated Document\n\nUpdated content")
    
    # Run incremental scan
    incremental_result = scanner.incremental_scan(
        [test_files['markdown'].parent],
        since=now
    )
    
    # Should only find the modified file
    assert incremental_result.total == 1
    assert incremental_result.successful == 1
    
    # Check it's the markdown file
    assert incremental_result.documents[0].title == "Updated Document"


def test_scan_nonexistent_path(scanner):
    """Test scanning nonexistent path"""
    result = scanner.scan([Path("/nonexistent/path")])
    
    assert result.total == 0
    assert result.successful == 0
    assert len(result.documents) == 0


def test_scan_empty_directory(scanner, tmp_path):
    """Test scanning empty directory"""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    
    result = scanner.scan([empty_dir])
    
    assert result.total == 0
    assert result.skipped == 0
    assert len(result.documents) == 0


def test_handler_registration(scanner_config):
    """Test handler registration"""
    scanner = DocumentScanner(scanner_config)
    
    # Check handlers are registered
    handlers = scanner.registry.list_handlers()
    assert 'TextHandler' in handlers
    assert 'MarkdownHandler' in handlers
    assert 'JSONHandler' in handlers
    assert 'YAMLHandler' in handlers
    assert 'PythonHandler' in handlers
    
    # Check extensions are mapped
    extensions = scanner.get_supported_formats()
    assert '.md' in extensions
    assert '.txt' in extensions
    assert '.json' in extensions
    assert '.yaml' in extensions
    assert '.py' in extensions


def test_malformed_json(scanner, tmp_path):
    """Test handling malformed JSON file"""
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{invalid json}")
    
    doc = scanner.process_document(bad_json)
    
    # Should still process but mark as invalid
    assert doc is not None
    assert doc.format == DocumentFormat.JSON
    # Content should be the raw text since parsing failed
    assert "{invalid json}" in doc.content