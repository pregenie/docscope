"""Filesystem API router for directory browsing"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel

from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/filesystem",
    tags=["Filesystem"],
    responses={404: {"description": "Path not found"}}
)


class DirectoryItem(BaseModel):
    """Directory item model"""
    name: str
    path: str
    type: str  # 'directory' or 'file'
    size: Optional[int] = None
    modified: Optional[float] = None
    is_readable: bool = True
    is_writable: bool = False


class DirectoryListing(BaseModel):
    """Directory listing response"""
    current_path: str
    parent_path: Optional[str]
    items: List[DirectoryItem]
    home_path: str
    separator: str


@router.get("/browse", response_model=DirectoryListing)
async def browse_directory(
    path: Optional[str] = Query(None, description="Directory path to browse"),
    show_hidden: bool = Query(False, description="Show hidden files and directories")
) -> DirectoryListing:
    """Browse directory structure
    
    Returns directory contents for file picker dialog.
    If no path is provided, returns user's home directory.
    """
    try:
        # Default to home directory if no path provided
        if not path:
            browse_path = Path.home()
        else:
            browse_path = Path(path).expanduser().resolve()
        
        # Security: Don't allow access outside of home or common document directories
        allowed_roots = [
            Path.home(),
            Path("/Users"),
            Path("/Documents"),
            Path("/tmp"),
            Path("/var/tmp")
        ]
        
        # Check if path is under an allowed root
        is_allowed = False
        for root in allowed_roots:
            try:
                if root.exists():
                    browse_path.relative_to(root)
                    is_allowed = True
                    break
            except (ValueError, OSError):
                continue
        
        if not is_allowed and not browse_path.exists():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this path is not allowed"
            )
        
        if not browse_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Path does not exist: {browse_path}"
            )
        
        if not browse_path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path is not a directory: {browse_path}"
            )
        
        # Get directory contents
        items = []
        try:
            for item in browse_path.iterdir():
                # Skip hidden files if requested
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                try:
                    stat = item.stat()
                    
                    # Determine if it's readable/writable
                    is_readable = os.access(item, os.R_OK)
                    is_writable = os.access(item, os.W_OK)
                    
                    items.append(DirectoryItem(
                        name=item.name,
                        path=str(item),
                        type="directory" if item.is_dir() else "file",
                        size=stat.st_size if item.is_file() else None,
                        modified=stat.st_mtime,
                        is_readable=is_readable,
                        is_writable=is_writable
                    ))
                except (PermissionError, OSError) as e:
                    # Add item with limited info if we can't stat it
                    items.append(DirectoryItem(
                        name=item.name,
                        path=str(item),
                        type="directory" if item.is_dir() else "file",
                        is_readable=False,
                        is_writable=False
                    ))
        except PermissionError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied accessing directory: {browse_path}"
            )
        
        # Sort: directories first, then alphabetically
        items.sort(key=lambda x: (x.type != "directory", x.name.lower()))
        
        # Get parent path
        parent_path = None
        if browse_path != Path("/"):
            parent_path = str(browse_path.parent)
        
        return DirectoryListing(
            current_path=str(browse_path),
            parent_path=parent_path,
            items=items,
            home_path=str(Path.home()),
            separator=os.sep
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error browsing directory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error browsing directory: {str(e)}"
        )


@router.get("/validate-path")
async def validate_path(
    path: str = Query(..., description="Path to validate")
) -> Dict[str, Any]:
    """Validate if a path exists and is accessible
    
    Returns information about the path including whether it exists,
    is a directory, is readable, and is writable.
    """
    try:
        test_path = Path(path).expanduser().resolve()
        
        exists = test_path.exists()
        is_directory = test_path.is_dir() if exists else False
        is_readable = os.access(test_path, os.R_OK) if exists else False
        is_writable = os.access(test_path, os.W_OK) if exists else False
        
        return {
            "path": str(test_path),
            "exists": exists,
            "is_directory": is_directory,
            "is_readable": is_readable,
            "is_writable": is_writable,
            "parent_exists": test_path.parent.exists()
        }
        
    except Exception as e:
        logger.error(f"Error validating path: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating path: {str(e)}"
        )


@router.get("/recent-paths")
async def get_recent_paths() -> List[str]:
    """Get list of recently used paths
    
    Returns a list of recently accessed directories for quick access.
    """
    # TODO: Implement storage of recent paths
    # For now, return common directories
    common_paths = []
    
    paths_to_check = [
        Path.home(),
        Path.home() / "Documents",
        Path.home() / "Downloads",
        Path.home() / "Desktop",
        Path("/tmp"),
    ]
    
    for path in paths_to_check:
        if path.exists() and path.is_dir():
            common_paths.append(str(path))
    
    return common_paths