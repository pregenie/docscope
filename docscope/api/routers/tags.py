"""Tags API router"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query

from ..models import TagCreate, TagResponse, ErrorResponse
from ..dependencies import get_storage, rate_limiter, verify_token
from ...storage import DocumentStore
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/tags",
    tags=["Tags"],
    responses={404: {"model": ErrorResponse}}
)


@router.get("", response_model=List[TagResponse])
async def list_tags(
    limit: int = Query(100, ge=1, le=500),
    storage: DocumentStore = Depends(get_storage),
    _: None = Depends(rate_limiter)
):
    """List all tags"""
    try:
        tags = storage.list_tags(limit=limit)
        
        # Convert to response models
        return [
            TagResponse(
                id=tag['id'],
                name=tag['name'],
                color=tag.get('color'),
                description=tag.get('description'),
                document_count=tag.get('document_count', 0),
                usage_count=tag.get('usage_count', 0)
            )
            for tag in tags
        ]
        
    except Exception as e:
        logger.error(f"Failed to list tags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tags"
        )


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag: TagCreate,
    storage: DocumentStore = Depends(get_storage),
    user_id: Optional[str] = Depends(verify_token),
    _: None = Depends(rate_limiter)
):
    """Create a new tag"""
    try:
        tag_id = storage.create_tag(
            name=tag.name,
            color=tag.color,
            description=tag.description
        )
        
        logger.info(f"Created tag {tag_id} by user {user_id}")
        
        # Return created tag
        tags = storage.list_tags()
        for t in tags:
            if t['id'] == tag_id:
                return TagResponse(
                    id=t['id'],
                    name=t['name'],
                    color=t.get('color'),
                    description=t.get('description'),
                    document_count=0,
                    usage_count=0
                )
        
        raise Exception("Created tag not found")
        
    except Exception as e:
        logger.error(f"Failed to create tag: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tag"
        )


@router.get("/popular", response_model=List[TagResponse])
async def get_popular_tags(
    limit: int = Query(20, ge=1, le=100),
    storage: DocumentStore = Depends(get_storage),
    _: None = Depends(rate_limiter)
):
    """Get most popular tags"""
    try:
        # Get all tags and sort by usage
        tags = storage.list_tags(limit=limit * 2)
        
        # Sort by document count
        sorted_tags = sorted(
            tags,
            key=lambda t: t.get('document_count', 0),
            reverse=True
        )[:limit]
        
        # Convert to response models
        return [
            TagResponse(
                id=tag['id'],
                name=tag['name'],
                color=tag.get('color'),
                description=tag.get('description'),
                document_count=tag.get('document_count', 0),
                usage_count=tag.get('usage_count', 0)
            )
            for tag in sorted_tags
        ]
        
    except Exception as e:
        logger.error(f"Failed to get popular tags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve popular tags"
        )


@router.get("/cloud")
async def get_tag_cloud(
    limit: int = Query(50, ge=1, le=200),
    storage: DocumentStore = Depends(get_storage),
    _: None = Depends(rate_limiter)
):
    """Get tag cloud data with weights"""
    try:
        tags = storage.list_tags(limit=limit)
        
        # Calculate weights based on document count
        max_count = max((t.get('document_count', 1) for t in tags), default=1)
        
        tag_cloud = []
        for tag in tags:
            count = tag.get('document_count', 0)
            weight = (count / max_count) if max_count > 0 else 0
            
            tag_cloud.append({
                "name": tag['name'],
                "weight": weight,
                "count": count,
                "color": tag.get('color')
            })
        
        # Sort by weight
        tag_cloud.sort(key=lambda t: t['weight'], reverse=True)
        
        return {
            "tags": tag_cloud,
            "total": len(tag_cloud)
        }
        
    except Exception as e:
        logger.error(f"Failed to get tag cloud: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tag cloud"
        )