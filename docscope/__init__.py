"""DocScope - Universal Documentation Browser & Search System"""

__version__ = "1.0.0"
__author__ = "DocScope Team"
__email__ = "team@docscope.io"

from .core.config import Config
from .core.logging import setup_logging
from .scanner import DocumentScanner
from .search import SearchEngine
from .storage import DocumentStore

__all__ = [
    "Config",
    "setup_logging",
    "DocumentScanner",
    "SearchEngine",
    "DocumentStore",
]