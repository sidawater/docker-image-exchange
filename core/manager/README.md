# Knowledge Manager

The Knowledge class provides a comprehensive solution for managing knowledge base files organized in a multi-layer folder structure.

## Features

- **Folder-based initialization**: Initialize with a folder path to scan and manage all files
- **File management**: List all files and view directory structure
- **Bulk upload/download**: Upload or download entire knowledge bases while preserving directory structure
- **Single file operations**: Upload or download individual files
- **Async operations**: All file operations are asynchronous for better performance
- **Prefix support**: Add custom prefixes to object names during upload

## Quick Start

### Initialize DocFile client

```python
from core.file.api import DocFile

DocFile.init(
    bucket_name="knowledge-base",
    backend='minio',
    endpoint="minio.example.com:9000",
    access_key="your_access_key",
    secret_key="your_secret_key",
    secure=False
)
```

### Create Knowledge instance

```python
from core.manager import Knowledge

knowledge = Knowledge("/path/to/knowledge/folder")
```

### List files

```python
# Get count
print(f"Total files: {knowledge.count_files()}")

# List all files
for file_info in knowledge.list_files():
    print(f"  {file_info['name']}: {file_info['path']}")

# Get structure
structure = knowledge.get_structure()
print(structure)
```

### Upload entire knowledge base

```python
import asyncio

async def upload_knowledge():
    # Upload all files
    await knowledge.upload_all()

    # Upload with prefix
    await knowledge.upload_all(prefix="dv019_it_operation_guide")

asyncio.run(upload_knowledge())
```

### Upload specific file

```python
import asyncio

async def upload_single():
    await knowledge.upload_file(
        "1 SERVICE LEVEL/1 SERVICE LEVEL.md",
        prefix="dv019_it_operation_guide"
    )

asyncio.run(upload_single())
```

### Download entire knowledge base

```python
import asyncio

async def download_knowledge():
    # Download to original location
    await knowledge.download_all()

    # Download to custom location
    await knowledge.download_all(destination="/path/to/download")

asyncio.run(download_knowledge())
```

### Download specific file

```python
import asyncio

async def download_single():
    await knowledge.download_file(
        "dv019_it_operation_guide/1 SERVICE LEVEL/1 SERVICE LEVEL.md",
        destination="/tmp/downloaded_file.md"
    )

asyncio.run(download_single())
```

## API Reference

### Knowledge Class

#### `__init__(base_path: str)`

Initialize the Knowledge manager.

**Parameters:**
- `base_path`: Path to the knowledge base folder (must exist and be a directory)

**Raises:**
- `FileNotFoundError`: If path doesn't exist
- `NotADirectoryError`: If path is not a directory

#### `list_files() -> List[Dict]`

Get a list of all files in the knowledge base.

**Returns:**
- List of dictionaries with 'name' and 'path' keys

#### `get_structure() -> Dict`

Get the hierarchical structure of the knowledge base.

**Returns:**
- Nested dictionary representing the directory structure

#### `count_files() -> int`

Count the total number of files.

**Returns:**
- Integer count of files

#### `async upload_all(prefix: Optional[str] = None)`

Upload all files to storage backend.

**Parameters:**
- `prefix`: Optional prefix to prepend to all object names

**Raises:**
- `RuntimeError`: If storage client is not initialized

#### `async upload_file(file_path: str, prefix: Optional[str] = None)`

Upload a specific file.

**Parameters:**
- `file_path`: Path to local file (absolute or relative to base)
- `prefix`: Optional prefix for object name

**Raises:**
- `FileNotFoundError`: If file doesn't exist
- `RuntimeError`: If storage client is not initialized

#### `async download_all(destination: Optional[str] = None)`

Download all files from storage.

**Parameters:**
- `destination`: Local destination directory (defaults to base_path)

**Raises:**
- `RuntimeError`: If storage client is not initialized

#### `async download_file(object_name: str, destination: Optional[str] = None)`

Download a specific file.

**Parameters:**
- `object_name`: Name of the object in storage
- `destination`: Local destination path

**Raises:**
- `RuntimeError`: If storage client is not initialized

#### `get_file_list_with_prefix(prefix: str = "") -> List[str]`

Get file paths with optional prefix filter.

**Parameters:**
- `prefix`: Prefix to filter files

**Returns:**
- List of relative file paths with prefix

## Directory Structure Example

The Knowledge class is designed to manage knowledge bases with the following structure:

```
knowledge_base/
├── 1 SERVICE LEVEL/
│   └── 1 SERVICE LEVEL.md
├── 2 SYSTEM INFORMATION/
│   ├── 2 SYSTEM INFORMATION.md
│   ├── 2.1 Workflow Diagram/
│   │   ├── 2.1 Workflow Diagram.md
│   │   └── 2.1.1 System Flow.md
│   └── 2.2 System Components/
├── DOCUMENT LOCATION.md
├── DOCUMENT REVISION HISTORY.md
└── image1.png
```

When uploading with prefix "dv019", the files will be stored in the bucket as:

```
dv019/1 SERVICE LEVEL/1 SERVICE LEVEL.md
dv019/2 SYSTEM INFORMATION/2 SYSTEM INFORMATION.md
dv019/2 SYSTEM INFORMATION/2.1 Workflow Diagram/2.1 Workflow Diagram.md
...
```

## Notes

- All file operations are asynchronous for better performance
- Directory structure is preserved during upload/download
- The class uses `asyncio.gather()` for concurrent operations when uploading/downloading multiple files
- Object names in storage use forward slashes (/) to represent directory structure
