"""Documents API router"""

from typing import List, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse

from ..models import (
    DocumentCreate, DocumentUpdate, DocumentResponse,
    DocumentListResponse, ErrorResponse
)
from ..dependencies import get_storage, rate_limiter, Pagination, verify_token
from ...core.models import Document, DocumentFormat, DocumentStatus
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
    responses={404: {"model": ErrorResponse}}
)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    format: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    status: Optional[str] = None,
    pagination: Pagination = Depends(),
    storage: DocumentStore = Depends(get_storage),
    _: None = Depends(rate_limiter)
):
    """List documents with optional filters"""
    try:
        documents = storage.list_documents(
            limit=pagination.limit,
            offset=pagination.offset,
            format=format,
            status=status,
            category=category,
            tags=tags
        )
        
        total = storage.count_documents(
            format=format,
            status=status,
            category=category
        )
        
        pages = (total + pagination.page_size - 1) // pagination.page_size
        
        return DocumentListResponse(
            items=[_document_to_response(doc) for doc in documents],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pages
        )
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    storage: DocumentStore = Depends(get_storage),
    _: None = Depends(rate_limiter)
):
    """Get a specific document by ID"""
    document = storage.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    return _document_to_response(document)


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document: DocumentCreate,
    storage: DocumentStore = Depends(get_storage),
    user_id: Optional[str] = Depends(verify_token),
    _: None = Depends(rate_limiter)
):
    """Create a new document"""
    try:
        # Create document model
        doc = Document(
            id=str(uuid.uuid4()),
            path=document.path,
            title=document.title,
            content=document.content,
            format=DocumentFormat(document.format),
            size=len(document.content.encode()),
            content_hash=str(hash(document.content)),
            created_at=datetime.now(),
            modified_at=datetime.now(),
            category=document.category,
            tags=document.tags,
            metadata=document.metadata,
            status=DocumentStatus.PENDING
        )
        
        # Store document
        doc_id = storage.store_document(doc)
        
        # Retrieve and return
        stored_doc = storage.get_document(doc_id)
        
        logger.info(f"Created document {doc_id} by user {user_id}")
        
        return _document_to_response(stored_doc)
        
    except Exception as e:
        logger.error(f"Failed to create document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create document"
        )


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    update: DocumentUpdate,
    storage: DocumentStore = Depends(get_storage),
    user_id: Optional[str] = Depends(verify_token),
    _: None = Depends(rate_limiter)
):
    """Update an existing document"""
    # Check if document exists
    existing = storage.get_document(document_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    try:
        # Prepare updates
        updates = {}
        if update.title is not None:
            updates["title"] = update.title
        if update.content is not None:
            updates["content"] = update.content
            updates["size"] = len(update.content.encode())
            updates["content_hash"] = str(hash(update.content))
        if update.tags is not None:
            updates["tags"] = update.tags
        if update.category is not None:
            updates["category"] = update.category
        if update.metadata is not None:
            updates["metadata"] = update.metadata
        
        updates["modified_at"] = datetime.now()
        
        # Update document
        success = storage.update_document(document_id, updates)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update document"
            )
        
        # Retrieve and return updated document
        updated_doc = storage.get_document(document_id)
        
        logger.info(f"Updated document {document_id} by user {user_id}")
        
        return _document_to_response(updated_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update document"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    storage: DocumentStore = Depends(get_storage),
    user_id: Optional[str] = Depends(verify_token),
    _: None = Depends(rate_limiter)
):
    """Delete a document"""
    success = storage.delete_document(document_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    logger.info(f"Deleted document {document_id} by user {user_id}")


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    storage: DocumentStore = Depends(get_storage),
    user_id: Optional[str] = Depends(verify_token),
    _: None = Depends(rate_limiter)
):
    """Upload a document file"""
    try:
        # Check file extension
        import os
        _, ext = os.path.splitext(file.filename)
        
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8', errors='ignore')
        
        # Determine format from extension
        format_map = {
            '.md': DocumentFormat.MARKDOWN,
            '.txt': DocumentFormat.TEXT,
            '.json': DocumentFormat.JSON,
            '.yaml': DocumentFormat.YAML,
            '.yml': DocumentFormat.YAML,
            '.py': DocumentFormat.CODE,
            '.js': DocumentFormat.CODE,
            '.html': DocumentFormat.HTML,
            '.htm': DocumentFormat.HTML,
        }
        
        doc_format = format_map.get(ext.lower(), DocumentFormat.UNKNOWN)
        
        # Create document
        doc = Document(
            id=str(uuid.uuid4()),
            path=f"/uploads/{file.filename}",
            title=file.filename,
            content=content_str,
            format=doc_format,
            size=len(content),
            content_hash=str(hash(content_str)),
            created_at=datetime.now(),
            modified_at=datetime.now(),
            category=category,
            tags=tags or [],
            metadata={"uploaded": True, "original_name": file.filename},
            status=DocumentStatus.PENDING
        )
        
        # Store document
        doc_id = storage.store_document(doc)
        
        # Retrieve and return
        stored_doc = storage.get_document(doc_id)
        
        logger.info(f"Uploaded document {doc_id} by user {user_id}")
        
        return _document_to_response(stored_doc)
        
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    storage: DocumentStore = Depends(get_storage),
    _: None = Depends(rate_limiter)
):
    """Download a document as a file"""
    document = storage.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    
    # Create temporary file
    import tempfile
    import os
    
    # Determine file extension
    ext_map = {
        DocumentFormat.MARKDOWN: '.md',
        DocumentFormat.TEXT: '.txt',
        DocumentFormat.JSON: '.json',
        DocumentFormat.YAML: '.yaml',
        DocumentFormat.CODE: '.txt',
        DocumentFormat.HTML: '.html',
    }
    
    ext = ext_map.get(document.format, '.txt')
    
    with tempfile.NamedTemporaryFile(mode='w', suffix=ext, delete=False) as f:
        f.write(document.content)
        temp_path = f.name
    
    return FileResponse(
        path=temp_path,
        filename=f"{document.title}{ext}",
        media_type="application/octet-stream"
    )


def _document_to_response(doc: Document) -> DocumentResponse:
    """Convert Document model to API response"""
    return DocumentResponse(
        id=doc.id,
        path=doc.path,
        title=doc.title,
        content=doc.content,
        format=doc.format,
        size=doc.size,
        content_hash=doc.content_hash,
        created_at=doc.created_at,
        modified_at=doc.modified_at,
        indexed_at=doc.indexed_at,
        category=doc.category,
        tags=doc.tags,
        metadata=doc.metadata,
        status=doc.status
    )