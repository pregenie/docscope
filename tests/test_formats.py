"""Tests for format handlers"""

import pytest
from pathlib import Path
import tempfile

from docscope.scanner.handlers import (
    MarkdownHandler,
    TextHandler,
    JSONHandler,
    YAMLHandler,
    PythonHandler,
    HTMLHandler,
)
from docscope.core.models import DocumentFormat


def test_markdown_handler():
    """Test Markdown handler"""
    handler = MarkdownHandler()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""---
title: Test Article
author: John Doe
---

# Main Title

This is a test document.

## Section 1

Content with [a link](https://example.com) and ![an image](image.png).

### Subsection

More content here.
""")
        filepath = Path(f.name)
    
    try:
        # Test can_handle
        assert handler.can_handle(filepath)
        assert not handler.can_handle(Path("test.txt"))
        
        # Test content extraction
        content = handler.extract_content(filepath)
        assert "# Main Title" in content
        assert "This is a test document" in content
        
        # Test metadata extraction
        metadata = handler.extract_metadata(filepath)
        assert 'frontmatter' in metadata
        assert metadata['frontmatter']['title'] == 'Test Article'
        assert metadata['frontmatter']['author'] == 'John Doe'
        assert len(metadata['headers']) == 3
        assert len(metadata['links']) == 1
        assert len(metadata['images']) == 1
        
        # Test title extraction
        title = handler.extract_title(filepath, content)
        assert title == "Main Title"
        
        # Test full processing
        doc = handler.process(filepath)
        assert doc.format == DocumentFormat.MARKDOWN
        assert doc.title == "Main Title"
        
    finally:
        filepath.unlink()


def test_text_handler():
    """Test Text handler"""
    handler = TextHandler()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Line 1\nLine 2\nLine 3")
        filepath = Path(f.name)
    
    try:
        assert handler.can_handle(filepath)
        
        content = handler.extract_content(filepath)
        assert content == "Line 1\nLine 2\nLine 3"
        
        metadata = handler.extract_metadata(filepath)
        assert metadata['line_count'] == 3
        assert metadata['word_count'] == 6
        
        doc = handler.process(filepath)
        assert doc.format == DocumentFormat.TEXT
        
    finally:
        filepath.unlink()


def test_json_handler():
    """Test JSON handler"""
    handler = JSONHandler()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"name": "test", "values": [1, 2, 3], "nested": {"key": "value"}}')
        filepath = Path(f.name)
    
    try:
        assert handler.can_handle(filepath)
        
        content = handler.extract_content(filepath)
        assert '"name": "test"' in content
        
        metadata = handler.extract_metadata(filepath)
        assert metadata['valid'] is True
        assert metadata['key_count'] == 3
        assert 'name' in metadata['keys']
        
        doc = handler.process(filepath)
        assert doc.format == DocumentFormat.JSON
        
    finally:
        filepath.unlink()


def test_yaml_handler():
    """Test YAML handler"""
    handler = YAMLHandler()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
name: test
values:
  - one
  - two
nested:
  key: value
""")
        filepath = Path(f.name)
    
    try:
        assert handler.can_handle(filepath)
        
        content = handler.extract_content(filepath)
        assert 'name: test' in content
        
        metadata = handler.extract_metadata(filepath)
        assert metadata['valid'] is True
        assert metadata['key_count'] == 3
        
        doc = handler.process(filepath)
        assert doc.format == DocumentFormat.YAML
        
    finally:
        filepath.unlink()


def test_python_handler():
    """Test Python handler"""
    handler = PythonHandler()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''"""Module for testing

This module contains test code.
"""

import os
import sys
from pathlib import Path

class TestClass:
    """A test class"""
    
    def method_one(self):
        pass
    
    def method_two(self):
        return True

def function_one():
    """First function"""
    pass

def function_two():
    """Second function"""
    return 42

if __name__ == "__main__":
    function_one()
''')
        filepath = Path(f.name)
    
    try:
        assert handler.can_handle(filepath)
        
        content = handler.extract_content(filepath)
        assert 'class TestClass:' in content
        
        metadata = handler.extract_metadata(filepath)
        assert metadata['language'] == 'python'
        assert len(metadata['imports']) == 3
        assert 'TestClass' in metadata['classes']
        assert 'function_one' in metadata['functions']
        assert 'function_two' in metadata['functions']
        assert 'docstring' in metadata
        
        title = handler.extract_title(filepath, content)
        assert title == "Module for testing"
        
        doc = handler.process(filepath)
        assert doc.format == DocumentFormat.CODE
        assert doc.title == "Module for testing"
        
    finally:
        filepath.unlink()


def test_html_handler():
    """Test HTML handler"""
    handler = HTMLHandler()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <meta name="description" content="A test page">
    <meta name="author" content="John Doe">
</head>
<body>
    <h1>Main Heading</h1>
    <p>This is a paragraph with <a href="https://example.com">a link</a>.</p>
    <img src="image.jpg" alt="An image">
    <script>console.log('test');</script>
    <style>body { color: red; }</style>
</body>
</html>
""")
        filepath = Path(f.name)
    
    try:
        assert handler.can_handle(filepath)
        
        content = handler.extract_content(filepath)
        # Script and style should be removed
        assert 'console.log' not in content
        assert 'color: red' not in content
        # Text content should be present
        assert 'Main Heading' in content
        assert 'This is a paragraph' in content
        
        metadata = handler.extract_metadata(filepath)
        assert metadata['html_title'] == 'Test Page'
        assert 'meta_tags' in metadata
        assert metadata['meta_tags']['description'] == 'A test page'
        assert metadata['link_count'] == 1
        assert metadata['image_count'] == 1
        assert metadata['heading_count'] == 1
        
        title = handler.extract_title(filepath, content)
        assert title == "Test Page"
        
        doc = handler.process(filepath)
        assert doc.format == DocumentFormat.HTML
        assert doc.title == "Test Page"
        
    finally:
        filepath.unlink()


def test_handler_with_invalid_encoding():
    """Test handler with file that has encoding issues"""
    handler = TextHandler()
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
        # Write some bytes that might cause encoding issues
        f.write(b'Valid text \x80\x81 more text')
        filepath = Path(f.name)
    
    try:
        # Should handle encoding errors gracefully
        content = handler.extract_content(filepath)
        assert 'Valid text' in content
        assert 'more text' in content
        
    finally:
        filepath.unlink()


def test_markdown_without_frontmatter():
    """Test Markdown handler without frontmatter"""
    handler = MarkdownHandler()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Simple Document

Just a simple markdown document without frontmatter.
""")
        filepath = Path(f.name)
    
    try:
        metadata = handler.extract_metadata(filepath)
        assert 'frontmatter' not in metadata or metadata['frontmatter'] is None
        
        content = handler.extract_content(filepath)
        title = handler.extract_title(filepath, content)
        assert title == "Simple Document"
        
    finally:
        filepath.unlink()


def test_json_handler_with_array():
    """Test JSON handler with array as root"""
    handler = JSONHandler()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('[1, 2, 3, 4, 5]')
        filepath = Path(f.name)
    
    try:
        metadata = handler.extract_metadata(filepath)
        assert metadata['valid'] is True
        assert metadata['array_length'] == 5
        assert 'keys' not in metadata
        
    finally:
        filepath.unlink()


def test_python_handler_without_docstring():
    """Test Python handler without module docstring"""
    handler = PythonHandler()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""import os

def main():
    pass
""")
        filepath = Path(f.name)
    
    try:
        content = handler.extract_content(filepath)
        title = handler.extract_title(filepath, content)
        # Should fall back to filename-based title
        assert title != ""
        
        metadata = handler.extract_metadata(filepath)
        assert 'docstring' not in metadata or not metadata['docstring']
        
    finally:
        filepath.unlink()