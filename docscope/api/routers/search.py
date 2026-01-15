"""Search API router"""

from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query

from ..models import SearchRequest, SearchResponse, SearchResultItem, ErrorResponse
from ..dependencies import get_search_engine, get_storage, rate_limiter
from ...search import SearchEngine
from ...storage import DocumentStore
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/search",
    tags=["Search"],
    responses={400: {"model": ErrorResponse}}
)


@router.post("", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    search_engine: SearchEngine = Depends(get_search_engine),
    storage: DocumentStore = Depends(get_storage),
    _: None = Depends(rate_limiter)
):
    """Search for documents"""
    try:
        # Execute search
        results = search_engine.search(
            query=request.query,
            filters=request.filters,
            limit=request.limit,
            offset=request.offset,
            sort_by=request.sort_by,
            facets=request.facets,
            highlight=request.highlight
        )
        
        # Convert to response model
        response = SearchResponse(
            query=results.query,
            results=[
                SearchResultItem(
                    document_id=r.document_id,
                    title=r.title,
                    path=r.path,
                    score=r.score,
                    snippet=r.snippet,
                    format=r.format,
                    category=r.category,
                    tags=r.tags,
                    highlights=r.highlights or []
                )
                for r in results.results
            ],
            total=results.total,
            facets=results.facets,
            suggestions=results.suggestions,
            duration=results.duration
        )
        
        logger.info(f"Search '{request.query}' returned {results.total} results")
        
        return response
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search operation failed"
        )


@router.get("", response_model=SearchResponse)
async def search_documents_get(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    format: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: Optional[str] = None,
    facets: bool = True,
    highlight: bool = True,
    search_engine: SearchEngine = Depends(get_search_engine),
    _: None = Depends(rate_limiter)
):
    """Search for documents (GET method for simple queries)"""
    try:
        # Build filters
        filters = {}
        if format:
            filters["format"] = format
        if category:
            filters["category"] = category
        if tags:
            filters["tags"] = tags
        
        # Execute search
        results = search_engine.search(
            query=q,
            filters=filters if filters else None,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            facets=facets,
            highlight=highlight
        )
        
        # Convert to response model
        response = SearchResponse(
            query=results.query,
            results=[
                SearchResultItem(
                    document_id=r.document_id,
                    title=r.title,
                    path=r.path,
                    score=r.score,
                    snippet=r.snippet,
                    format=r.format,
                    category=r.category,
                    tags=r.tags,
                    highlights=r.highlights or []
                )
                for r in results.results
            ],
            total=results.total,
            facets=results.facets,
            suggestions=results.suggestions,
            duration=results.duration
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search operation failed"
        )


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query("", max_length=100, description="Partial query for suggestions"),
    limit: int = Query(10, ge=1, le=50),
    search_engine: SearchEngine = Depends(get_search_engine),
    _: None = Depends(rate_limiter)
):
    """Get search suggestions/autocomplete"""
    try:
        suggestions = search_engine.get_suggestions(q, limit)
        
        return {
            "query": q,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get suggestions"
        )


@router.get("/similar/{document_id}", response_model=SearchResponse)
async def find_similar_documents(
    document_id: str,
    limit: int = Query(10, ge=1, le=50),
    search_engine: SearchEngine = Depends(get_search_engine),
    storage: DocumentStore = Depends(get_storage),
    _: None = Depends(rate_limiter)
):
    """Find documents similar to a given document"""
    # Check if document exists
    document = storage.get_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    try:
        # Find similar documents
        results = search_engine.search_similar(document_id, limit)
        
        # Convert to response model
        response = SearchResponse(
            query=f"similar:{document_id}",
            results=[
                SearchResultItem(
                    document_id=r.document_id,
                    title=r.title,
                    path=r.path,
                    score=r.score,
                    snippet=r.snippet,
                    format=r.format,
                    category=r.category,
                    tags=r.tags,
                    highlights=[]
                )
                for r in results.results
            ],
            total=results.total,
            facets=None,
            suggestions=None,
            duration=results.duration
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Similar search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Similar search operation failed"
        )


@router.post("/reindex")
async def reindex_all_documents(
    search_engine: SearchEngine = Depends(get_search_engine),
    storage: DocumentStore = Depends(get_storage),
    _: None = Depends(rate_limiter)
):
    """Reindex all documents in the search engine"""
    try:
        # Clear existing index
        search_engine.clear_index()
        
        # Get all documents from storage
        documents = storage.list_documents(limit=10000)  # TODO: Handle pagination
        
        # Reindex documents
        indexed = search_engine.index_documents(documents)
        
        # Optimize index
        search_engine.optimize_index()
        
        logger.info(f"Reindexed {indexed} documents")
        
        return {
            "message": "Reindexing completed",
            "documents_indexed": indexed
        }
        
    except Exception as e:
        logger.error(f"Reindexing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Reindexing operation failed"
        )