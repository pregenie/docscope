"""API routers"""

from .documents import router as documents_router
from .search import router as search_router
from .categories import router as categories_router
from .tags import router as tags_router
from .scanner import router as scanner_router
from .health import router as health_router
from .websocket import router as websocket_router

__all__ = [
    "documents_router",
    "search_router",
    "categories_router",
    "tags_router",
    "scanner_router",
    "health_router",
    "websocket_router",
]