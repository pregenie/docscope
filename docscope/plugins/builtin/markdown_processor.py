"""Markdown Processor Plugin for DocScope"""

import re
from typing import Dict, Any, List
import logging

from ..base import ProcessorPlugin, PluginMetadata, PluginCapability, PluginHook

logger = logging.getLogger(__name__)


class MarkdownProcessorPlugin(ProcessorPlugin):
    """Plugin for processing and enhancing Markdown documents"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.extract_toc = config.get('extract_toc', True) if config else True
        self.extract_links = config.get('extract_links', True) if config else True
        self.extract_code_blocks = config.get('extract_code_blocks', True) if config else True
        self.add_reading_time = config.get('add_reading_time', True) if config else True
    
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return PluginMetadata(
            name="markdown_processor",
            version="1.0.0",
            author="DocScope Team",
            description="Process and enhance Markdown documents with metadata extraction",
            capabilities=[PluginCapability.PROCESSOR],
            hooks=[PluginHook.BEFORE_INDEX],
            tags=["markdown", "processor", "toc", "metadata"],
            config_schema={
                'extract_toc': {
                    'type': bool,
                    'default': True,
                    'description': 'Extract table of contents from headers'
                },
                'extract_links': {
                    'type': bool,
                    'default': True,
                    'description': 'Extract all links from document'
                },
                'extract_code_blocks': {
                    'type': bool,
                    'default': True,
                    'description': 'Extract and categorize code blocks'
                },
                'add_reading_time': {
                    'type': bool,
                    'default': True,
                    'description': 'Calculate estimated reading time'
                }
            }
        )
    
    def initialize(self) -> bool:
        """Initialize the plugin"""
        # Register hook for processing before indexing
        self.register_hook(PluginHook.BEFORE_INDEX, self.process_before_index)
        logger.info("Markdown Processor plugin initialized")
        return True
    
    def shutdown(self) -> None:
        """Cleanup when plugin is disabled"""
        logger.info("Markdown Processor plugin shutdown")
    
    def should_process(self, document: Dict[str, Any]) -> bool:
        """Check if this processor should handle the document"""
        return document.get('format') in ['markdown', 'md']
    
    def process_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Process a Markdown document and add metadata"""
        if not self.should_process(document):
            return document
        
        content = document.get('content', '')
        metadata = document.get('metadata', {})
        
        # Extract table of contents
        if self.extract_toc:
            toc = self._extract_toc(content)
            if toc:
                metadata['table_of_contents'] = toc
        
        # Extract links
        if self.extract_links:
            links = self._extract_links(content)
            if links:
                metadata['links'] = links
                metadata['external_links'] = [l for l in links if l.startswith('http')]
                metadata['internal_links'] = [l for l in links if not l.startswith('http')]
        
        # Extract code blocks
        if self.extract_code_blocks:
            code_blocks = self._extract_code_blocks(content)
            if code_blocks:
                metadata['code_blocks'] = code_blocks
                metadata['languages'] = list(set(cb.get('language', 'plain') for cb in code_blocks))
        
        # Calculate reading time
        if self.add_reading_time:
            reading_time = self._calculate_reading_time(content)
            metadata['reading_time_minutes'] = reading_time
        
        # Extract front matter if present
        front_matter = self._extract_front_matter(content)
        if front_matter:
            metadata['front_matter'] = front_matter
            # Remove front matter from content
            content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
        
        # Update document
        document['content'] = content
        document['metadata'] = metadata
        
        logger.debug(f"Processed Markdown document: {document.get('title', 'untitled')}")
        return document
    
    def process_before_index(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Hook handler for processing before indexing"""
        return self.process_document(document)
    
    def _extract_toc(self, content: str) -> List[Dict[str, Any]]:
        """Extract table of contents from headers"""
        toc = []
        header_pattern = r'^(#{1,6})\s+(.+)$'
        
        for match in re.finditer(header_pattern, content, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()
            anchor = re.sub(r'[^\w\s-]', '', title.lower())
            anchor = re.sub(r'\s+', '-', anchor)
            
            toc.append({
                'level': level,
                'title': title,
                'anchor': anchor
            })
        
        return toc
    
    def _extract_links(self, content: str) -> List[str]:
        """Extract all links from Markdown content"""
        links = []
        
        # Markdown links [text](url)
        md_link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        for match in re.finditer(md_link_pattern, content):
            links.append(match.group(2))
        
        # Reference links [text][ref]
        ref_link_pattern = r'^\[([^\]]+)\]:\s+(.+)$'
        for match in re.finditer(ref_link_pattern, content, re.MULTILINE):
            links.append(match.group(2))
        
        # Plain URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        for match in re.finditer(url_pattern, content):
            links.append(match.group(0))
        
        return list(set(links))  # Remove duplicates
    
    def _extract_code_blocks(self, content: str) -> List[Dict[str, str]]:
        """Extract code blocks from Markdown"""
        code_blocks = []
        
        # Fenced code blocks ```language\ncode\n```
        fenced_pattern = r'```(\w+)?\n(.*?)\n```'
        for match in re.finditer(fenced_pattern, content, re.DOTALL):
            language = match.group(1) or 'plain'
            code = match.group(2)
            code_blocks.append({
                'language': language,
                'code': code,
                'lines': len(code.splitlines())
            })
        
        return code_blocks
    
    def _extract_front_matter(self, content: str) -> Dict[str, Any]:
        """Extract YAML front matter from Markdown"""
        front_matter_pattern = r'^---\n(.*?)\n---'
        match = re.match(front_matter_pattern, content, re.DOTALL)
        
        if match:
            try:
                import yaml
                return yaml.safe_load(match.group(1))
            except Exception as e:
                logger.warning(f"Failed to parse front matter: {e}")
                return {}
        
        return {}
    
    def _calculate_reading_time(self, content: str) -> int:
        """Calculate estimated reading time in minutes"""
        # Average reading speed: 200-250 words per minute
        words_per_minute = 225
        
        # Remove code blocks for more accurate count
        text_content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        
        # Count words
        word_count = len(text_content.split())
        
        # Calculate reading time (minimum 1 minute)
        reading_time = max(1, round(word_count / words_per_minute))
        
        return reading_time