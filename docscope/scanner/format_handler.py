"""Base format handler and registry"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Type
import hashlib
from datetime import datetime

from ..core.models import Document, DocumentFormat
from ..core.logging import get_logger

logger = get_logger(__name__)


class FormatHandler(ABC):
    """Abstract base class for format handlers"""
    
    format_type: DocumentFormat
    extensions: List[str] = []
    mime_types: List[str] = []
    
    @abstractmethod
    def can_handle(self, path: Path) -> bool:
        """Check if this handler can process the file
        
        Args:
            path: Path to the file
            
        Returns:
            True if handler can process this file
        """
        pass
    
    @abstractmethod
    def extract_content(self, path: Path) -> str:
        """Extract text content from the file
        
        Args:
            path: Path to the file
            
        Returns:
            Extracted text content
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, path: Path) -> Dict:
        """Extract metadata from the file
        
        Args:
            path: Path to the file
            
        Returns:
            Dictionary of metadata
        """
        pass
    
    def extract_title(self, path: Path, content: str) -> str:
        """Extract or generate a title for the document
        
        Args:
            path: Path to the file
            content: Document content
            
        Returns:
            Document title
        """
        # Default: use filename without extension
        return path.stem.replace('_', ' ').replace('-', ' ').title()
    
    def process(self, path: Path) -> Document:
        """Process a file and create a Document object
        
        Args:
            path: Path to the file
            
        Returns:
            Document object
        """
        try:
            # Extract content
            content = self.extract_content(path)
            
            # Extract metadata
            metadata = self.extract_metadata(path)
            
            # Extract or generate title
            title = self.extract_title(path, content)
            
            # Get file stats
            stat = path.stat()
            
            # Calculate content hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Create document
            doc = Document(
                id=hashlib.md5(str(path).encode()).hexdigest(),
                path=str(path.absolute()),
                title=title,
                content=content,
                format=self.format_type,
                size=stat.st_size,
                content_hash=content_hash,
                created_at=datetime.fromtimestamp(stat.st_ctime),
                modified_at=datetime.fromtimestamp(stat.st_mtime),
                metadata=metadata
            )
            
            logger.debug(f"Processed {path} with {self.__class__.__name__}")
            return doc
            
        except Exception as e:
            logger.error(f"Error processing {path}: {e}")
            raise


class FormatRegistry:
    """Registry for format handlers"""
    
    def __init__(self):
        self._handlers: Dict[str, FormatHandler] = {}
        self._extension_map: Dict[str, str] = {}
        
    def register(self, handler: FormatHandler) -> None:
        """Register a format handler
        
        Args:
            handler: Format handler instance
        """
        handler_name = handler.__class__.__name__
        self._handlers[handler_name] = handler
        
        # Map extensions to handler
        for ext in handler.extensions:
            self._extension_map[ext.lower()] = handler_name
            
        logger.debug(f"Registered {handler_name} for extensions: {handler.extensions}")
    
    def get_handler(self, path: Path) -> Optional[FormatHandler]:
        """Get appropriate handler for a file
        
        Args:
            path: Path to the file
            
        Returns:
            Format handler if found, None otherwise
        """
        # Try by extension first
        ext = path.suffix.lower()
        if ext in self._extension_map:
            handler_name = self._extension_map[ext]
            return self._handlers[handler_name]
        
        # Try each handler's can_handle method
        for handler in self._handlers.values():
            if handler.can_handle(path):
                return handler
        
        return None
    
    def list_handlers(self) -> List[str]:
        """List registered handler names
        
        Returns:
            List of handler names
        """
        return list(self._handlers.keys())
    
    def list_extensions(self) -> List[str]:
        """List supported file extensions
        
        Returns:
            List of file extensions
        """
        return list(self._extension_map.keys())