"""Scanner API router"""

from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

from ..models import ScanRequest, ScanResponse, ErrorResponse
from ..dependencies import get_scanner, get_storage, get_search_engine, verify_token, rate_limiter
from ...scanner import DocumentScanner
from ...storage import DocumentStore
from ...search import SearchEngine
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/scanner",
    tags=["Scanner"],
    responses={400: {"model": ErrorResponse}}
)


@router.post("/scan", response_model=ScanResponse)
async def scan_documents(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    scanner: DocumentScanner = Depends(get_scanner),
    storage: DocumentStore = Depends(get_storage),
    search_engine: SearchEngine = Depends(get_search_engine),
    user_id: Optional[str] = Depends(verify_token),
    _: None = Depends(rate_limiter)
):
    """Scan documents and add them to the system"""
    try:
        # Convert paths to Path objects
        paths = [Path(p) for p in request.paths]
        
        # Validate paths
        for path in paths:
            if not path.exists():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Path does not exist: {path}"
                )
        
        # Perform scan
        if request.incremental and request.since:
            result = scanner.incremental_scan(paths, since=request.since)
        else:
            # Pass formats if provided
            formats = request.formats if hasattr(request, 'formats') else None
            result = scanner.scan(paths, recursive=request.recursive, formats=formats)
        
        # Store documents in database
        stored = storage.store_scan_result(result)
        
        # Index documents in background
        background_tasks.add_task(
            index_scanned_documents,
            result.documents,
            search_engine
        )
        
        logger.info(
            f"Scanned {result.total} documents, "
            f"{result.successful} successful, "
            f"{result.failed} failed by user {user_id}"
        )
        
        return ScanResponse(
            total=result.total,
            successful=result.successful,
            failed=result.failed,
            skipped=result.skipped,
            errors=result.errors,
            duration=result.duration,
            documents_found=result.total,
            new_documents=stored,
            updated_documents=0  # TODO: track updates
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Scan operation failed"
        )


@router.get("/formats")
async def get_supported_formats(
    scanner: DocumentScanner = Depends(get_scanner),
    _: None = Depends(rate_limiter)
):
    """Get list of supported document formats"""
    try:
        formats = scanner.get_supported_formats()
        
        return {
            "formats": formats,
            "total": len(formats)
        }
        
    except Exception as e:
        logger.error(f"Failed to get formats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve supported formats"
        )


@router.post("/watch")
async def watch_directory(
    path: str,
    scanner: DocumentScanner = Depends(get_scanner),
    user_id: Optional[str] = Depends(verify_token),
    _: None = Depends(rate_limiter)
):
    """Start watching a directory for changes"""
    try:
        # This would integrate with a file watcher service
        # For now, just return a placeholder response
        
        logger.info(f"Started watching {path} by user {user_id}")
        
        return {
            "message": f"Started watching directory: {path}",
            "status": "watching"
        }
        
    except Exception as e:
        logger.error(f"Failed to start watching: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start watching directory"
        )


async def index_scanned_documents(documents, search_engine: SearchEngine):
    """Background task to index scanned documents"""
    try:
        indexed = search_engine.index_documents(documents)
        logger.info(f"Indexed {indexed} scanned documents")
    except Exception as e:
        logger.error(f"Failed to index scanned documents: {e}")