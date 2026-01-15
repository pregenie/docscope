"""Main FastAPI application"""

from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import get_settings
from .routers import (
    documents_router,
    search_router,
    scanner_router,
    categories_router,
    tags_router,
    health_router,
    websocket_router,
    filesystem_router
)
from .dependencies import init_dependencies, cleanup_dependencies
from ..core.logging import get_logger
from ..web import mount_web_ui

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting DocScope API server...")
    await init_dependencies()
    logger.info("DocScope API server started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down DocScope API server...")
    await cleanup_dependencies()
    logger.info("DocScope API server stopped")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="DocScope - Universal Documentation Browser & Search API",
        docs_url="/api/docs" if not settings.production else None,
        redoc_url="/api/redoc" if not settings.production else None,
        openapi_url="/api/openapi.json" if not settings.production else None,
        lifespan=lifespan
    )
    
    # Add middleware
    configure_middleware(app)
    
    # Add routers
    configure_routers(app)
    
    # Add exception handlers
    configure_exception_handlers(app)
    
    # Mount Web UI
    mount_web_ui(app)
    
    return app


def configure_middleware(app: FastAPI) -> None:
    """Configure application middleware"""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Trusted host middleware
    if settings.production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts
        )
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all incoming requests"""
        import time
        start_time = time.time()
        
        # Log request
        logger.info(f"{request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} "
            f"completed in {process_time:.3f}s "
            f"with status {response.status_code}"
        )
        
        # Add custom headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-API-Version"] = settings.version
        
        return response


def configure_routers(app: FastAPI) -> None:
    """Configure API routers"""
    
    # Add API v1 routers
    api_v1_prefix = "/api/v1"
    
    app.include_router(
        health_router,
        prefix=api_v1_prefix
    )
    
    app.include_router(
        documents_router,
        prefix=api_v1_prefix
    )
    
    app.include_router(
        search_router,
        prefix=api_v1_prefix
    )
    
    app.include_router(
        scanner_router,
        prefix=api_v1_prefix
    )
    
    app.include_router(
        categories_router,
        prefix=api_v1_prefix
    )
    
    app.include_router(
        tags_router,
        prefix=api_v1_prefix
    )
    
    app.include_router(
        websocket_router,
        prefix=api_v1_prefix
    )
    
    app.include_router(
        filesystem_router,
        prefix=api_v1_prefix
    )
    
    # API info endpoint (moved from root to /api to avoid conflict with web UI)
    @app.get("/api")
    async def api_info() -> Dict[str, Any]:
        """API information endpoint"""
        return {
            "name": settings.app_name,
            "version": settings.version,
            "status": "running",
            "docs": "/api/docs" if not settings.production else None,
            "api": {
                "v1": "/api/v1",
                "health": "/api/v1/health",
                "docs": "/api/v1/documents",
                "search": "/api/v1/search"
            }
        }


def configure_exception_handlers(app: FastAPI) -> None:
    """Configure exception handlers"""
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url)
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors"""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "detail": exc.errors(),
                "body": exc.body
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions"""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        if settings.production:
            # Don't expose internal errors in production
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "status_code": 500
                }
            )
        else:
            # Show more detail in development
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": str(exc),
                    "type": type(exc).__name__,
                    "status_code": 500,
                    "path": str(request.url)
                }
            )


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "docscope.api.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if settings.debug else "error"
    )