"""Format handlers for various document types"""

import json
import yaml
import re
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import ast

from .format_handler import FormatHandler
from ..core.models import DocumentFormat
from ..core.logging import get_logger

logger = get_logger(__name__)


class TextHandler(FormatHandler):
    """Handler for plain text files"""
    
    format_type = DocumentFormat.TEXT
    extensions = ['.txt', '.text', '.log', '.csv', '.tsv']
    
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.extensions
    
    def extract_content(self, path: Path) -> str:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading text file {path}: {e}")
            raise
    
    def extract_metadata(self, path: Path) -> Dict:
        content = self.extract_content(path)
        lines = content.splitlines()
        return {
            'line_count': len(lines),
            'word_count': len(content.split()),
            'char_count': len(content),
            'encoding': 'utf-8'
        }


class MarkdownHandler(FormatHandler):
    """Handler for Markdown files"""
    
    format_type = DocumentFormat.MARKDOWN
    extensions = ['.md', '.markdown', '.mkd', '.mdx']
    
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.extensions
    
    def extract_content(self, path: Path) -> str:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading markdown file {path}: {e}")
            raise
    
    def extract_metadata(self, path: Path) -> Dict:
        content = self.extract_content(path)
        metadata = {
            'format': 'markdown',
            'headers': self._extract_headers(content),
            'links': self._extract_links(content),
            'images': self._extract_images(content),
        }
        
        # Check for frontmatter
        frontmatter = self._extract_frontmatter(content)
        if frontmatter:
            metadata['frontmatter'] = frontmatter
            
        return metadata
    
    def extract_title(self, path: Path, content: str) -> str:
        # Try to find H1 header
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()
        
        # Try frontmatter title
        frontmatter = self._extract_frontmatter(content)
        if frontmatter and 'title' in frontmatter:
            return frontmatter['title']
        
        # Fallback to filename
        return super().extract_title(path, content)
    
    def _extract_headers(self, content: str) -> list:
        """Extract all headers from markdown"""
        headers = []
        for match in re.finditer(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE):
            level = len(match.group(1))
            text = match.group(2).strip()
            headers.append({'level': level, 'text': text})
        return headers
    
    def _extract_links(self, content: str) -> list:
        """Extract all links from markdown"""
        links = []
        # [text](url) format
        for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content):
            links.append({'text': match.group(1), 'url': match.group(2)})
        return links
    
    def _extract_images(self, content: str) -> list:
        """Extract all images from markdown"""
        images = []
        # ![alt](url) format
        for match in re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', content):
            images.append({'alt': match.group(1), 'url': match.group(2)})
        return images
    
    def _extract_frontmatter(self, content: str) -> Optional[Dict]:
        """Extract YAML frontmatter if present"""
        if content.startswith('---'):
            try:
                end_match = re.search(r'\n---\n', content[3:])
                if end_match:
                    frontmatter_text = content[3:end_match.start() + 3]
                    return yaml.safe_load(frontmatter_text)
            except:
                pass
        return None


class JSONHandler(FormatHandler):
    """Handler for JSON files"""
    
    format_type = DocumentFormat.JSON
    extensions = ['.json', '.jsonl', '.geojson']
    
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.extensions
    
    def extract_content(self, path: Path) -> str:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Pretty print for better readability
                return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error reading JSON file {path}: {e}")
            # Try to read as text if JSON parsing fails
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
    
    def extract_metadata(self, path: Path) -> Dict:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            metadata = {
                'format': 'json',
                'valid': True,
            }
            
            if isinstance(data, dict):
                metadata['keys'] = list(data.keys())[:20]  # First 20 keys
                metadata['key_count'] = len(data)
            elif isinstance(data, list):
                metadata['array_length'] = len(data)
                
            return metadata
        except:
            return {'format': 'json', 'valid': False}


class YAMLHandler(FormatHandler):
    """Handler for YAML files"""
    
    format_type = DocumentFormat.YAML
    extensions = ['.yaml', '.yml']
    
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.extensions
    
    def extract_content(self, path: Path) -> str:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                # Convert back to YAML for consistent formatting
                return yaml.dump(data, default_flow_style=False, sort_keys=False)
        except Exception as e:
            logger.error(f"Error reading YAML file {path}: {e}")
            # Read as text if YAML parsing fails
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
    
    def extract_metadata(self, path: Path) -> Dict:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            metadata = {
                'format': 'yaml',
                'valid': True,
            }
            
            if isinstance(data, dict):
                metadata['keys'] = list(data.keys())[:20]  # First 20 keys
                metadata['key_count'] = len(data)
            elif isinstance(data, list):
                metadata['array_length'] = len(data)
                
            return metadata
        except:
            return {'format': 'yaml', 'valid': False}


class PythonHandler(FormatHandler):
    """Handler for Python source files"""
    
    format_type = DocumentFormat.CODE
    extensions = ['.py', '.pyw', '.pyi']
    
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.extensions
    
    def extract_content(self, path: Path) -> str:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading Python file {path}: {e}")
            raise
    
    def extract_metadata(self, path: Path) -> Dict:
        content = self.extract_content(path)
        
        metadata = {
            'language': 'python',
            'line_count': len(content.splitlines()),
        }
        
        # Extract imports
        imports = []
        for line in content.splitlines():
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                imports.append(line.strip())
        metadata['imports'] = imports[:20]  # First 20 imports
        
        # Extract classes and functions
        try:
            tree = ast.parse(content)
            classes = []
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
            
            metadata['classes'] = classes[:20]
            metadata['functions'] = functions[:20]
        except:
            pass
        
        # Extract docstring
        docstring_match = re.match(r'^\s*"""(.*?)"""', content, re.DOTALL)
        if not docstring_match:
            docstring_match = re.match(r"^\s*'''(.*?)'''", content, re.DOTALL)
        if docstring_match:
            metadata['docstring'] = docstring_match.group(1).strip()[:500]
        
        return metadata
    
    def extract_title(self, path: Path, content: str) -> str:
        # Try to extract from module docstring
        docstring_match = re.match(r'^\s*"""(.*?)"""', content, re.DOTALL)
        if not docstring_match:
            docstring_match = re.match(r"^\s*'''(.*?)'''", content, re.DOTALL)
        
        if docstring_match:
            first_line = docstring_match.group(1).strip().split('\n')[0]
            if first_line and len(first_line) < 100:
                return first_line
        
        return super().extract_title(path, content)


class HTMLHandler(FormatHandler):
    """Handler for HTML files"""
    
    format_type = DocumentFormat.HTML
    extensions = ['.html', '.htm', '.xhtml']
    
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.extensions
    
    def extract_content(self, path: Path) -> str:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            # Try to extract text from HTML
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text
                text = soup.get_text()
                
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)
                
                return text
            except ImportError:
                # If BeautifulSoup not available, return raw HTML
                return html_content
                
        except Exception as e:
            logger.error(f"Error reading HTML file {path}: {e}")
            raise
    
    def extract_metadata(self, path: Path) -> Dict:
        metadata = {'format': 'html'}
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            if title_tag:
                metadata['html_title'] = title_tag.get_text().strip()
            
            # Extract meta tags
            meta_tags = {}
            for tag in soup.find_all('meta'):
                if tag.get('name'):
                    meta_tags[tag['name']] = tag.get('content', '')
                elif tag.get('property'):
                    meta_tags[tag['property']] = tag.get('content', '')
            
            if meta_tags:
                metadata['meta_tags'] = meta_tags
            
            # Count elements
            metadata['link_count'] = len(soup.find_all('a'))
            metadata['image_count'] = len(soup.find_all('img'))
            metadata['heading_count'] = len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
            
        except:
            pass
        
        return metadata
    
    def extract_title(self, path: Path, content: str) -> str:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try <title> tag
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
                if title:
                    return title
            
            # Try first H1
            h1_tag = soup.find('h1')
            if h1_tag:
                title = h1_tag.get_text().strip()
                if title:
                    return title
        except:
            pass
        
        return super().extract_title(path, content)