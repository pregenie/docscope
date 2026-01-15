"""Health check API router"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends

from ..dependencies import get_storage, get_search_engine, get_scanner
from ...storage import DocumentStore
from ...search import SearchEngine
from ...scanner import DocumentScanner
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/health",
    tags=["Health"]
)


@router.get("")
async def health_check() -> Dict[str, Any]:
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "DocScope API",
        "version": "1.0.0"
    }


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """Kubernetes liveness probe"""
    return {"status": "alive"}


@router.get("/ready")
async def readiness_check(
    storage: DocumentStore = Depends(get_storage),
    search_engine: SearchEngine = Depends(get_search_engine),
    scanner: DocumentScanner = Depends(get_scanner)
) -> Dict[str, Any]:
    """Kubernetes readiness probe - checks all dependencies"""
    checks = {
        "storage": False,
        "search": False,
        "scanner": False
    }
    
    try:
        # Check storage
        storage.count_documents()
        checks["storage"] = True
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
    
    try:
        # Check search engine
        search_engine.get_index_stats()
        checks["search"] = True
    except Exception as e:
        logger.error(f"Search health check failed: {e}")
    
    try:
        # Check scanner
        scanner.get_supported_formats()
        checks["scanner"] = True
    except Exception as e:
        logger.error(f"Scanner health check failed: {e}")
    
    all_healthy = all(checks.values())
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/stats")
async def get_stats(
    storage: DocumentStore = Depends(get_storage),
    search_engine: SearchEngine = Depends(get_search_engine)
) -> Dict[str, Any]:
    """Get system statistics"""
    try:
        # Get document stats
        total_documents = storage.count_documents()
        
        # Get format distribution
        format_stats = {}
        for format_type in ["markdown", "text", "json", "yaml", "code", "html"]:
            format_stats[format_type] = storage.count_documents(format=format_type)
        
        # Get search stats
        search_stats = search_engine.get_index_stats()
        
        # Get storage stats
        categories = storage.list_categories()
        tags = storage.list_tags()
        
        return {
            "documents": {
                "total": total_documents,
                "by_format": format_stats
            },
            "search": search_stats,
            "organization": {
                "categories": len(categories),
                "tags": len(tags)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {
            "error": "Failed to retrieve statistics",
            "timestamp": datetime.now().isoformat()
        }


@router.get("/metrics")
async def get_metrics() -> str:
    """Prometheus metrics endpoint"""
    # Return metrics in Prometheus format
    metrics = []
    
    try:
        # Add basic metrics
        metrics.append("# HELP docscope_api_up API availability")
        metrics.append("# TYPE docscope_api_up gauge")
        metrics.append("docscope_api_up 1")
        
        # Add timestamp
        metrics.append("# HELP docscope_api_last_check_timestamp Last health check timestamp")
        metrics.append("# TYPE docscope_api_last_check_timestamp gauge")
        metrics.append(f"docscope_api_last_check_timestamp {datetime.now().timestamp()}")
        
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
    
    return "\n".join(metrics)