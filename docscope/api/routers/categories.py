"""Categories API router"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from ..models import CategoryCreate, CategoryResponse, ErrorResponse
from ..dependencies import get_storage, rate_limiter, verify_token
from ...storage import DocumentStore
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    responses={404: {"model": ErrorResponse}}
)


@router.get("", response_model=List[CategoryResponse])
async def list_categories(
    parent_id: Optional[str] = None,
    storage: DocumentStore = Depends(get_storage),
    _: None = Depends(rate_limiter)
):
    """List all categories"""
    try:
        categories = storage.list_categories(parent_id=parent_id)
        
        # Convert to response models
        return [
            CategoryResponse(
                id=cat['id'],
                name=cat['name'],
                parent_id=cat.get('parent_id'),
                description=cat.get('description'),
                color=cat.get('color'),
                icon=cat.get('icon'),
                document_count=cat.get('document_count', 0),
                children=cat.get('children', [])
            )
            for cat in categories
        ]
        
    except Exception as e:
        logger.error(f"Failed to list categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve categories"
        )


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate,
    storage: DocumentStore = Depends(get_storage),
    user_id: Optional[str] = Depends(verify_token),
    _: None = Depends(rate_limiter)
):
    """Create a new category"""
    try:
        category_id = storage.create_category(
            name=category.name,
            parent_id=category.parent_id,
            description=category.description,
            color=category.color,
            icon=category.icon
        )
        
        logger.info(f"Created category {category_id} by user {user_id}")
        
        # Return created category
        categories = storage.list_categories()
        for cat in categories:
            if cat['id'] == category_id:
                return CategoryResponse(
                    id=cat['id'],
                    name=cat['name'],
                    parent_id=cat.get('parent_id'),
                    description=cat.get('description'),
                    color=cat.get('color'),
                    icon=cat.get('icon'),
                    document_count=0,
                    children=[]
                )
        
        raise Exception("Created category not found")
        
    except Exception as e:
        logger.error(f"Failed to create category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create category"
        )


@router.get("/tree", response_model=List[CategoryResponse])
async def get_category_tree(
    storage: DocumentStore = Depends(get_storage),
    _: None = Depends(rate_limiter)
):
    """Get category tree structure"""
    try:
        # Get root categories
        root_categories = storage.list_categories(parent_id=None)
        
        # Build tree recursively
        def build_tree(parent_id: str) -> List[CategoryResponse]:
            children = storage.list_categories(parent_id=parent_id)
            result = []
            for child in children:
                cat_response = CategoryResponse(
                    id=child['id'],
                    name=child['name'],
                    parent_id=child.get('parent_id'),
                    description=child.get('description'),
                    color=child.get('color'),
                    icon=child.get('icon'),
                    document_count=child.get('document_count', 0),
                    children=build_tree(child['id'])
                )
                result.append(cat_response)
            return result
        
        # Build tree for each root
        tree = []
        for root in root_categories:
            root_response = CategoryResponse(
                id=root['id'],
                name=root['name'],
                parent_id=None,
                description=root.get('description'),
                color=root.get('color'),
                icon=root.get('icon'),
                document_count=root.get('document_count', 0),
                children=build_tree(root['id'])
            )
            tree.append(root_response)
        
        return tree
        
    except Exception as e:
        logger.error(f"Failed to get category tree: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve category tree"
        )