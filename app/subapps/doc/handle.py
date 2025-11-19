

import json
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import UploadFile, File, Form, HTTPException, Query, Body
from core.schema import Document as DocumentSchema, DocumentMetadata, Tag as SchemaTag
from .form import (
    UpdateDocumentRequest,
    StartProcessingRequest,
    CompleteProcessingRequest,
    SubmitReviewRequest
)


async def upload_document(
    file: UploadFile = File(...),
    filename: Optional[str] = Form(None),
    content_type: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    custom_fields: Optional[str] = Form(None),
    aliases: Optional[str] = Form(None),
    document_key: Optional[str] = Form(None),
) -> Dict[str, Any]:
    """
    Upload a document to the system

    This endpoint handles file uploads and creates the necessary database records
    for the document, including tags, aliases, and processing status.
    """
    try:
        # Parse JSON fields
        parsed_tags = []
        if tags:
            try:
                parsed_tags = json.loads(tags)
                parsed_tags = [SchemaTag(name=tag["name"], display_name=tag.get("display_name", tag["name"]))
                              for tag in parsed_tags]
            except (json.JSONDecodeError, KeyError):
                raise HTTPException(status_code=400, detail="Invalid tags JSON format")

        parsed_custom_fields = None
        if custom_fields:
            try:
                parsed_custom_fields = json.loads(custom_fields)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid custom_fields JSON format")

        parsed_aliases = []
        if aliases:
            try:
                parsed_aliases = json.loads(aliases)
                if not isinstance(parsed_aliases, list):
                    raise HTTPException(status_code=400, detail="Aliases must be a JSON array")
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid aliases JSON format")

        # Use provided filename or default to uploaded filename
        actual_filename = filename or file.filename
        if not actual_filename:
            raise HTTPException(status_code=400, detail="Filename is required")

        # Determine content type
        actual_content_type = content_type or file.content_type
        if not actual_content_type:
            raise HTTPException(status_code=400, detail="Content type is required")

        # Create document metadata
        metadata = DocumentMetadata(
            name=actual_filename,
            content_type=actual_content_type,
            size=file.size or 0,  # File size might be unknown for streaming uploads
            created_at=datetime.now(),
            updated_at=datetime.now(),
            description=description,
            tags=parsed_tags,
            custom_fields=parsed_custom_fields,
            aliases=parsed_aliases
        )

        # Create document schema object
        doc_key = document_key or str(uuid.uuid4())
        doc_schema = DocumentSchema(
            key=doc_key,
            storage_key=f"documents/{datetime.now().strftime('%Y/%m')}/{doc_key}.{actual_filename.split('.')[-1] if '.' in actual_filename else 'bin'}",
            metadata=metadata
        )

        # Upload to document manager
        # First, get file size by reading it into memory for the upload
        file_content = await file.read()
        # Reset file to beginning for actual upload
        import io
        file.file = io.BytesIO(file_content)  # Update the file object to contain the content

        # Use create_document_from_schema method
        result = await manager.create_document_from_schema(
            document_schema=doc_schema,
            file=file.file
        )

        return result.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


async def get_document(
    document_key: str,
    include_presigned: Optional[bool] = Query(None),
    expires: Optional[int] = Query(3600),
) -> Dict[str, Any]:
    """
    Get a document's metadata by its key

    Optionally includes a presigned download URL if requested.
    """
    try:
        document = await manager.get_document(document_key)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        result = document.to_dict()

        # Add presigned URL if requested
        if include_presigned:
            presigned_url = await manager.generate_presigned_url(document_key, expires)
            result["presigned_url"] = presigned_url

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document: {str(e)}")


async def list_documents(
    prefix: Optional[str] = Query(None),
    alias: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """
    List documents with optional filtering and pagination
    """
    try:
        # Get documents with filters
        documents, total = await manager.list_documents(
            prefix=prefix,
            alias=alias,
            tag=tag,
            offset=offset,
            size=size
        )

        return {
            "items": [doc.to_dict() for doc in documents],
            "total": total,
            "offset": offset,
            "size": size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


async def get_document_by_alias(
    alias: str,
) -> Dict[str, Any]:
    """
    Find documents by alias
    """
    try:
        documents = await manager.get_documents_by_alias(alias)

        return {
            "items": [doc.to_dict() for doc in documents]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents by alias: {str(e)}")


async def download_document(
    document_key: str,
):
    """
    Download document content directly or redirect to presigned URL
    """
    try:
        # For now, redirect to presigned URL
        presigned_url = await manager.generate_presigned_url(document_key)
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=presigned_url, status_code=302)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading document: {str(e)}")


async def get_presigned_url(
    document_key: str,
    expires: Optional[int] = Query(3600),
) -> Dict[str, Any]:
    """
    Generate a presigned download URL for a document
    """
    try:
        presigned_url = await manager.generate_presigned_url(document_key, expires)

        return {
            "presigned_url": presigned_url,
            "expires_in": expires
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating presigned URL: {str(e)}")


async def update_document(
    document_key: str,
    update_data: UpdateDocumentRequest = Body(...),
) -> Dict[str, Any]:
    """
    Partially update document metadata
    """
    try:
        document = await manager.get_document(document_key)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Update fields that were provided
        if update_data.description is not None:
            document.metadata.description = update_data.description

        if update_data.aliases is not None:
            document.metadata.aliases = update_data.aliases

        if update_data.tags is not None:
            document.metadata.tags = [
                SchemaTag(name=tag["name"], display_name=tag.get("display_name", tag["name"]))
                for tag in update_data.tags
            ]

        if update_data.custom_fields is not None:
            document.metadata.custom_fields = update_data.custom_fields

        # Update the updated_at timestamp
        document.metadata.updated_at = datetime.now()

        # Update in the manager
        updated_document = await manager.update_document(document)

        return updated_document.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating document: {str(e)}")


async def check_document_exists(
    document_key: str,
) -> None:
    """
    Check if a document exists (HEAD request equivalent)
    """
    try:
        document = await manager.get_document(document_key)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        # Return 204 No Content if document exists
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking document existence: {str(e)}")


async def get_processing_status(
    document_key: str,
) -> Dict[str, Any]:
    """
    Get the current processing status of a document
    """
    try:
        processing_status = await manager.get_processing_status(document_key)
        if not processing_status:
            raise HTTPException(status_code=404, detail="Processing status not found")

        return processing_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving processing status: {str(e)}")


async def start_processing(
    document_key: str,
    config: StartProcessingRequest = Body(None),
) -> Dict[str, Any]:
    """
    Explicitly start or retry processing for a document
    """
    try:
        processing_status = await manager.start_processing(document_key, config.steps if config else None)

        return processing_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting processing: {str(e)}")


async def complete_processing(
    document_key: str,
    request: CompleteProcessingRequest,
) -> Dict[str, Any]:
    """
    Mark processing as complete for a document
    """
    try:
        processing_status = await manager.complete_processing(document_key, request.data, request.status)

        return processing_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing processing: {str(e)}")


async def get_review_status(
    document_key: str,
) -> Dict[str, Any]:
    """
    Get the review status of a document
    """
    try:
        review_status = await manager.get_review_status(document_key)
        if not review_status:
            raise HTTPException(status_code=404, detail="Review status not found")

        return review_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving review status: {str(e)}")


async def submit_review(
    document_key: str,
    request: SubmitReviewRequest,
) -> Dict[str, Any]:
    """
    Submit a review decision for a document
    """
    try:
        review_status = await manager.submit_review(document_key, request.action, request.reviewer, request.comment, request.timestamp)

        return review_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting review: {str(e)}")
