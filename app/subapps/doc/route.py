from fastapi import APIRouter
from .handle import (
    upload_document,
    get_document,
    list_documents,
    get_document_by_alias,
    download_document,
    get_presigned_url,
    update_document,
    check_document_exists,
    get_processing_status,
    start_processing,
    complete_processing,
    get_review_status,
    submit_review
)

router = APIRouter(prefix="/documents", tags=["documents"])

router.add_api_route(
    "/upload",
    upload_document,
    methods=["POST"],
    summary="Upload a document",
    description="Upload a document to the system with optional metadata"
)

router.add_api_route(
    "/{document_key}",
    get_document,
    methods=["GET"],
    summary="Get document metadata",
    description="Retrieve a single document's metadata"
)

router.add_api_route(
    "",
    list_documents,
    methods=["GET"],
    summary="List documents",
    description="List documents with optional filtering and pagination"
)

router.add_api_route(
    "/alias/{alias}",
    get_document_by_alias,
    methods=["GET"],
    summary="Find documents by alias",
    description="Find documents by alias"
)

router.add_api_route(
    "/{document_key}/download",
    download_document,
    methods=["GET"],
    summary="Download document",
    description="Download the file content directly or redirect to a presigned URL"
)

router.add_api_route(
    "/{document_key}/presigned",
    get_presigned_url,
    methods=["GET"],
    summary="Generate presigned download URL",
    description="Generate a presigned download URL for a document"
)

router.add_api_route(
    "/{document_key}",
    update_document,
    methods=["PATCH"],
    summary="Partially update document metadata",
    description="Partially update document metadata (does not modify stored file)"
)

router.add_api_route(
    "/{document_key}",
    check_document_exists,
    methods=["HEAD"],
    summary="Check document existence",
    description="Quick existence check for a document"
)

router.add_api_route(
    "/{document_key}/processing",
    get_processing_status,
    methods=["GET"],
    summary="Get processing status",
    description="Retrieve the current processing status and recent processing data"
)

router.add_api_route(
    "/{document_key}/processing/start",
    start_processing,
    methods=["POST"],
    summary="Start processing",
    description="Explicitly start or retry processing for a document"
)

router.add_api_route(
    "/{document_key}/processing/complete",
    complete_processing,
    methods=["POST"],
    summary="Complete processing",
    description="Mark processing as complete for a document"
)

router.add_api_route(
    "/{document_key}/review",
    get_review_status,
    methods=["GET"],
    summary="Get review status",
    description="Query the document review state and last review record"
)

router.add_api_route(
    "/{document_key}/review",
    submit_review,
    methods=["POST"],
    summary="Submit review decision",
    description="Submit a human review decision"
)
