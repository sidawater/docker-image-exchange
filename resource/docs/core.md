# Document Manager API Documentation

## Overview

The Document Manager provides a comprehensive system for managing documents in memory while coordinating with MinIO for file storage. It handles document creation, upload, download, metadata management, and presigned URL generation.

---

## Class: DocumentManager

### `__init__(storage_prefix: str = "documents")`
Initialize the Document Manager.

**Parameters:**
- `storage_prefix`: str, prefix for storage paths in MinIO (default: "documents")

**Usage:**
```python
manager = DocumentManager(storage_prefix="user-documents")
```

### `create_document(filename, content_type, size, description=None, tags=None, custom_fields=None, document_key=None, aliases=None)`
Create new document object (in memory only).

**Parameters:**
- `filename`: str, original filename
- `content_type`: str, MIME type of the file
- `size`: int, file size in bytes
- `description`: Optional[str], document description (default: None)
- `tags`: List[Tag], list of document tags (default: None)
- `custom_fields`: Optional[Dict[str, Any]], custom metadata fields (default: None)
- `document_key`: Optional[str], custom document identifier (default: None, auto-generated)
- `aliases`: List[str], list of document aliases (default: None)

**Returns:**
- Document: created document object

**Raises:**
- ValueError: if document key already exists

### `upload_from_file(file_path, filename, content_type, description=None, tags=None, custom_fields=None, aliases=None, document_key=None)`
Upload from local file and create document.

**Parameters:**
- `file_path`: str, path to local file
- `filename`: str, original filename
- `content_type`: str, MIME type of the file
- `description`: Optional[str], document description (default: None)
- `tags`: List[Tag], list of document tags (default: None)
- `custom_fields`: Optional[Dict[str, Any]], custom metadata fields (default: None)
- `aliases`: List[str], list of document aliases (default: None)
- `document_key`: Optional[str], custom document identifier (default: None, auto-generated)

**Returns:**
- Document: created document object

**Raises:**
- Exception: if file upload fails

### `upload_from_stream(data, filename, content_type, size, description=None, tags=None, custom_fields=None, aliases=None, document_key=None)`
Upload from data stream and create document.

**Parameters:**
- `data`: BinaryIO, binary data stream
- `filename`: str, original filename
- `content_type`: str, MIME type of the file
- `size`: int, data size in bytes
- `description`: Optional[str], document description (default: None)
- `tags`: List[Tag], list of document tags (default: None)
- `custom_fields`: Optional[Dict[str, Any]], custom metadata fields (default: None)
- `aliases`: List[str], list of document aliases (default: None)
- `document_key`: Optional[str], custom document identifier (default: None, auto-generated)

**Returns:**
- Document: created document object

**Raises:**
- Exception: if stream upload fails

### `download_to_file(document_key, file_path)`
Download document to local file.

**Parameters:**
- `document_key`: str, unique document identifier
- `file_path`: str, local path to save file

**Raises:**
- ValueError: if document not found

### `get_content(document_key)`
Get document content as bytes.

**Parameters:**
- `document_key`: str, unique document identifier

**Returns:**
- bytes: file content

**Raises:**
- ValueError: if document not found

### `get_document(document_key)`
Get document object.

**Parameters:**
- `document_key`: str, unique document identifier

**Returns:**
- Optional[Document]: document object or None if not found

### `list_documents(prefix="", limit=100)`
List document objects in memory.

**Parameters:**
- `prefix`: str, filter documents by key prefix (default: "")
- `limit`: int, maximum number of documents to return (default: 100)

**Returns:**
- List[Document]: list of document objects

### `update_metadata(document_key, description=None, tags=None, custom_fields=None, aliases=None)`
Update document metadata (in memory).

**Parameters:**
- `document_key`: str, unique document identifier
- `description`: Optional[str], new description (default: None)
- `tags`: Optional[List[Tag]], new tags list (default: None)
- `custom_fields`: Optional[Dict[str, Any]], new custom fields (default: None)
- `aliases`: Optional[List[str]], new aliases list (default: None)

**Returns:**
- Optional[Document]: updated document object or None if not found

### `get_presigned_url(document_key, expires=3600)`
Generate presigned URL for document download.

**Parameters:**
- `document_key`: str, unique document identifier
- `expires`: int, URL expiration time in seconds (default: 3600)

**Returns:**
- Optional[str]: presigned URL or None if document not found

### `document_exists(document_key)`
Check if document exists in memory.

**Parameters:**
- `document_key`: str, unique document identifier

**Returns:**
- bool: True if document exists

### `get_document_by_alias(alias)`
Find document by alias.

**Parameters:**
- `alias`: str, document alias to search for

**Returns:**
- Optional[Document]: document object or None if not found

### `clear()`
Clear all document objects from memory.

---

## Schema Classes

### Class: Tag

Represents a document tag with name and display name.

**Attributes:**
- `name`: str, internal tag name
- `display_name`: str, human-readable tag name

**Methods:**
- `to_dict()`: Convert Tag to dictionary
- `from_dict(data)`: Create Tag from dictionary

### Class: DocumentMetadata

Document metadata with file information and custom fields.

**Attributes:**
- `name`: str, filename
- `content_type`: str, MIME type of the file
- `size`: int, file size in bytes
- `created_at`: datetime, creation time (UTC)
- `updated_at`: datetime, last update time (UTC)
- `description`: Optional[str], document description
- `tags`: List[Tag], list of document tags
- `custom_fields`: Optional[Dict[str, Any]], custom metadata fields
- `aliases`: List[str], list of document aliases

**Methods:**
- `to_dict()`: Convert DocumentMetadata to serializable dictionary
- `from_dict(data)`: Create DocumentMetadata from dictionary

### Class: Document

Document object containing metadata and storage information.

**Attributes:**
- `key`: str, unique document identifier
- `metadata`: DocumentMetadata, document metadata and file information
- `storage_key`: str, storage path in MinIO (object key)

**Methods:**
- `to_dict()`: Convert Document to serializable dictionary
- `from_dict(data)`: Create Document from dictionary

---

## Usage Examples

### Basic Document Upload and Download
```python
# Initialize manager
manager = DocumentManager(storage_prefix="user-docs")

# Upload from file
document = await manager.upload_from_file(
    file_path="/path/to/file.pdf",
    filename="report.pdf",
    content_type="application/pdf",
    description="Quarterly report",
    aliases=["q3-report", "financials"]
)

# Download content
content = await manager.get_content(document.key)

# Get download URL
url = await manager.get_presigned_url(document.key, expires=7200)
```

### Working with Metadata
```python
# Create document with tags
tags = [Tag(name="finance", display_name="Finance")]
document = manager.create_document(
    filename="budget.xlsx",
    content_type="application/vnd.ms-excel",
    size=2048,
    tags=tags,
    aliases=["2024-budget", "spreadsheet"]
)

# Update metadata
updated_doc = manager.update_metadata(
    document_key=document.key,
    description="Updated budget forecast",
    aliases=["2024-budget-v2"]
)

# Find by alias
doc_by_alias = manager.get_document_by_alias("2024-budget-v2")
```

### Document Management
```python
# List documents
documents = manager.list_documents(prefix="2024", limit=50)

# Check existence
if manager.document_exists("doc-123"):
    doc = manager.get_document("doc-123")

# Clear all documents (memory only)
manager.clear()
```

---

## Error Handling

The Document Manager raises the following exceptions:

- **ValueError**: When document key already exists or document not found
- **Exception**: When file operations (upload/download) fail
- **RuntimeError**: When DocFile client is not properly initialized

## Notes

- All datetime values are stored in UTC
- Document objects are stored in memory only (not persisted)
- File content is stored in MinIO using the configured storage backend
- The manager coordinates between schema definitions and file storage operations
- Aliases provide alternative identifiers for document lookup
- Tags support both internal names and display names for flexibility