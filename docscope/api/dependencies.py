"""API dependencies for dependency injection"""

from typing import Generator, Optional
from functools import lru_cache
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..storage import DocumentStore
from ..storage.database import DatabaseManager
from ..search import SearchEngine
from ..scanner import DocumentScanner
from ..core.config import Config, StorageConfig, ScannerConfig
from ..core.logging import get_logger
from .config import api_config

logger = get_logger(__name__)


# Security
security = HTTPBearer(auto_error=False)


def init_dependencies():
    """Initialize dependencies on startup"""
    # Initialize storage
    storage = get_storage()
    storage.initialize()
    
    # Initialize search engine
    search = get_search_engine()
    search.initialize()
    
    logger.info("Dependencies initialized")


def cleanup_dependencies():
    """Cleanup dependencies on shutdown"""
    # Cleanup can be added here if needed
    logger.info("Dependencies cleaned up")


@lru_cache()
def get_config() -> Config:
    """Get application configuration (cached)"""
    return Config()


def get_db_manager() -> DatabaseManager:
    """Get database manager instance"""
    config = get_config()
    return DatabaseManager(config.storage)


def get_db() -> Generator:
    """Get database session"""
    db_manager = get_db_manager()
    db_manager.initialize()
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


@lru_cache()
def get_storage() -> DocumentStore:
    """Get document storage instance (cached)"""
    config = get_config()
    store = DocumentStore(config.storage)
    store.initialize()
    return store


@lru_cache()
def get_search_engine() -> SearchEngine:
    """Get search engine instance (cached)"""
    return SearchEngine(index_dir=api_config.search_index_dir)


@lru_cache()
def get_scanner() -> DocumentScanner:
    """Get document scanner instance (cached)"""
    config = get_config()
    return DocumentScanner(config.scanner)


def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """Verify authentication token
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User ID if authenticated, None if auth disabled
        
    Raises:
        HTTPException: If authentication fails
    """
    if not api_config.auth_enabled:
        return None
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Implement actual token verification
    # For now, just check if token exists
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return "user123"  # Placeholder user ID


class RateLimiter:
    """Simple rate limiter dependency"""
    
    def __init__(self):
        self.requests = {}
    
    def __call__(self, user_id: Optional[str] = Depends(verify_token)):
        """Check rate limit for user
        
        Args:
            user_id: User ID from authentication
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        if not api_config.rate_limit_enabled:
            return
        
        # TODO: Implement actual rate limiting with Redis or similar
        # For now, this is a placeholder
        pass


# Create rate limiter instance
rate_limiter = RateLimiter()


class Pagination:
    """Pagination parameters dependency"""
    
    def __init__(
        self,
        page: int = 1,
        page_size: int = api_config.default_page_size
    ):
        """Initialize pagination parameters
        
        Args:
            page: Page number (1-indexed)
            page_size: Items per page
        """
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be >= 1"
            )
        
        if page_size < 1 or page_size > api_config.max_page_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Page size must be between 1 and {api_config.max_page_size}"
            )
        
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
        self.limit = page_size