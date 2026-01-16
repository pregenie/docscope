"""Document scanner with multi-threading and progress tracking"""

import os
import fnmatch
from pathlib import Path
from typing import List, Optional, Set, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .format_handler import FormatRegistry
from .handlers import (
    MarkdownHandler,
    TextHandler,
    JSONHandler,
    YAMLHandler,
    PythonHandler,
    HTMLHandler,
)
from ..core.models import Document, ScanResult, DocumentStatus, DocumentFormat
from ..core.config import ScannerConfig
from ..core.logging import get_logger

logger = get_logger(__name__)


class DocumentScanner:
    """Multi-threaded document scanner with format detection and metadata extraction"""
    
    def __init__(self, config: ScannerConfig):
        """Initialize scanner with configuration
        
        Args:
            config: Scanner configuration
        """
        self.config = config
        self.registry = FormatRegistry()
        self.progress_callback: Optional[Callable] = None
        
        # Register default handlers
        self._register_default_handlers()
        
        # Compile ignore patterns
        self.ignore_patterns = self._compile_ignore_patterns()
        
    def _register_default_handlers(self):
        """Register built-in format handlers"""
        handlers = [
            TextHandler(),
            MarkdownHandler(),
            JSONHandler(),
            YAMLHandler(),
            PythonHandler(),
            HTMLHandler(),
        ]
        
        for handler in handlers:
            # Check if format is enabled in config
            formats = getattr(self.config.scanner, 'formats', {}) if hasattr(self.config, 'scanner') else {}
            format_config = formats.get(handler.format_type.value, {})
            if format_config.get('enabled', True):
                self.registry.register(handler)
                
        logger.info(f"Registered {len(self.registry.list_handlers())} format handlers")
        logger.debug(f"Supported extensions: {self.registry.list_extensions()}")
    
    def _compile_ignore_patterns(self) -> List[str]:
        """Compile ignore patterns from config"""
        patterns = self.config.ignore.copy()
        
        # Add common patterns if not present
        default_patterns = [
            '.*',  # Hidden files
            '*.pyc',
            '__pycache__',
            '*.swp',
            '*.tmp',
            '.DS_Store',
            'Thumbs.db',
        ]
        
        for pattern in default_patterns:
            if pattern not in patterns:
                patterns.append(pattern)
                
        return patterns
    
    def should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored
        
        Args:
            path: Path to check
            
        Returns:
            True if path should be ignored
        """
        # Check against ignore patterns
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(path.name, pattern):
                return True
            # Also check full path pattern
            if fnmatch.fnmatch(str(path), pattern):
                return True
        
        return False
    
    def find_documents(self, paths: List[Path], recursive: bool = True, formats: Optional[List[str]] = None) -> List[Path]:
        """Find all documents to scan
        
        Args:
            paths: List of paths to scan
            recursive: Whether to scan recursively
            formats: List of file extensions to include (e.g., ['md', 'txt', 'pdf'])
            
        Returns:
            List of document paths
        """
        documents = []
        seen_paths: Set[Path] = set()
        
        # Get supported extensions if formats specified
        allowed_extensions = set()
        if formats:
            for fmt in formats:
                # Add dot if not present
                ext = fmt if fmt.startswith('.') else f'.{fmt}'
                allowed_extensions.add(ext.lower())
        
        for path in paths:
            path = Path(path).resolve()
            
            if path in seen_paths:
                continue
                
            if path.is_file():
                if not self.should_ignore(path):
                    documents.append(path)
                    seen_paths.add(path)
                    
            elif path.is_dir():
                if recursive:
                    # Walk directory recursively
                    for root, dirs, files in os.walk(path):
                        root_path = Path(root)
                        
                        # Filter out ignored directories
                        dirs[:] = [d for d in dirs if not self.should_ignore(root_path / d)]
                        
                        for file in files:
                            file_path = root_path / file
                            
                            # Skip if already seen
                            if file_path in seen_paths:
                                continue
                            
                            # Check format FIRST if filter is specified
                            if formats:
                                if file_path.suffix.lower() not in allowed_extensions:
                                    continue
                            else:
                                # If no format filter, check if we have a handler for this file
                                if not self.registry.get_handler(file_path):
                                    continue
                            
                            # Then check ignore patterns
                            if not self.should_ignore(file_path):
                                documents.append(file_path)
                                seen_paths.add(file_path)
                else:
                    # Only scan immediate children
                    for file_path in path.iterdir():
                        if file_path.is_file():
                            # Skip if already seen
                            if file_path in seen_paths:
                                continue
                            
                            # Check format FIRST if filter is specified
                            if formats:
                                if file_path.suffix.lower() not in allowed_extensions:
                                    continue
                            else:
                                # If no format filter, check if we have a handler for this file
                                if not self.registry.get_handler(file_path):
                                    continue
                            
                            # Then check ignore patterns
                            if not self.should_ignore(file_path):
                                documents.append(file_path)
                                seen_paths.add(file_path)
        
        logger.info(f"Found {len(documents)} documents to scan (formats: {formats}, paths: {[str(p) for p in paths]})")
        return documents
    
    def process_document(self, path: Path) -> Optional[Document]:
        """Process a single document
        
        Args:
            path: Path to document
            
        Returns:
            Document object if successful, None otherwise
        """
        try:
            # Get appropriate handler
            handler = self.registry.get_handler(path)
            if not handler:
                logger.debug(f"No handler found for {path}")
                return None
            
            # Process document
            doc = handler.process(path)
            doc.status = DocumentStatus.INDEXED
            doc.indexed_at = datetime.now()
            
            return doc
            
        except Exception as e:
            logger.error(f"Error processing {path}: {e}")
            # Create error document
            doc = Document(
                id=str(path),
                path=str(path),
                title=path.name,
                content="",
                format=DocumentFormat.UNKNOWN,
                size=0,
                content_hash="",
                created_at=datetime.now(),
                modified_at=datetime.now(),
                status=DocumentStatus.FAILED,
                error=str(e)
            )
            return doc
    
    def scan(self, paths: List[Path], recursive: bool = True, formats: Optional[List[str]] = None) -> ScanResult:
        """Scan documents in parallel with progress tracking
        
        Args:
            paths: List of paths to scan
            recursive: Whether to scan recursively
            
        Returns:
            ScanResult with scanned documents
        """
        start_time = time.time()
        result = ScanResult()
        
        # Convert string paths to Path objects
        path_objects = []
        for p in paths:
            if isinstance(p, str):
                path_objects.append(Path(p))
            else:
                path_objects.append(p)
        
        # Find all documents
        documents = self.find_documents(path_objects, recursive, formats)
        
        if not documents:
            logger.info("No documents found to scan")
            return result
        
        # Process documents in parallel
        with ThreadPoolExecutor(max_workers=self.config.workers) as executor:
            # Submit all tasks
            future_to_path = {
                executor.submit(self.process_document, path): path 
                for path in documents
            }
            
            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                completed += 1
                
                try:
                    doc = future.result()
                    if doc:
                        if doc.status == DocumentStatus.INDEXED:
                            result.successful += 1
                        elif doc.status == DocumentStatus.FAILED:
                            result.failed += 1
                            if doc.error:
                                result.add_error(str(path), doc.error)
                        
                        result.documents.append(doc)
                        result.total += 1
                    else:
                        result.skipped += 1
                        
                except Exception as e:
                    logger.error(f"Error processing {path}: {e}")
                    result.add_error(str(path), str(e))
                
                # Call progress callback if set
                if self.progress_callback:
                    self.progress_callback(completed, len(documents), str(path))
        
        # Calculate duration
        result.duration = time.time() - start_time
        
        logger.info(
            f"Scan complete: {result.successful} successful, "
            f"{result.failed} failed, {result.skipped} skipped "
            f"in {result.duration:.2f}s"
        )
        
        return result
    
    def incremental_scan(self, paths: List[Path], since: datetime) -> ScanResult:
        """Scan only modified documents since timestamp
        
        Args:
            paths: List of paths to scan
            since: Timestamp to scan from
            
        Returns:
            ScanResult with modified documents
        """
        start_time = time.time()
        result = ScanResult()
        
        # Convert string paths to Path objects
        path_objects = []
        for p in paths:
            if isinstance(p, str):
                path_objects.append(Path(p))
            else:
                path_objects.append(p)
        
        # Find all documents
        all_documents = self.find_documents(path_objects, recursive=True)
        
        # Filter to only modified documents
        modified_documents = []
        for path in all_documents:
            try:
                stat = path.stat()
                modified_time = datetime.fromtimestamp(stat.st_mtime)
                if modified_time > since:
                    modified_documents.append(path)
            except:
                pass
        
        logger.info(f"Found {len(modified_documents)} modified documents since {since}")
        
        if not modified_documents:
            return result
        
        # Process modified documents
        with ThreadPoolExecutor(max_workers=self.config.workers) as executor:
            future_to_path = {
                executor.submit(self.process_document, path): path 
                for path in modified_documents
            }
            
            completed = 0
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                completed += 1
                
                try:
                    doc = future.result()
                    if doc:
                        if doc.status == DocumentStatus.INDEXED:
                            result.successful += 1
                        elif doc.status == DocumentStatus.FAILED:
                            result.failed += 1
                            if doc.error:
                                result.add_error(str(path), doc.error)
                        
                        result.documents.append(doc)
                        result.total += 1
                    else:
                        result.skipped += 1
                        
                except Exception as e:
                    logger.error(f"Error processing {path}: {e}")
                    result.add_error(str(path), str(e))
                
                if self.progress_callback:
                    self.progress_callback(completed, len(modified_documents), str(path))
        
        result.duration = time.time() - start_time
        
        logger.info(
            f"Incremental scan complete: {result.successful} updated "
            f"in {result.duration:.2f}s"
        )
        
        return result
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Set a callback for progress updates
        
        Args:
            callback: Function called with (completed, total, current_file)
        """
        self.progress_callback = callback
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats
        
        Returns:
            List of supported extensions
        """
        return self.registry.list_extensions()