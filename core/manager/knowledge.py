"""
knowledge created by manager.spliter
it is a series of files with muti-layer folders which splited by spliter module,
and formated as markdown

e.g. structure:
dv019_it_operation_guide_capdam_v2_5
├── 1 SERVICE LEVEL
│   └── 1 SERVICE LEVEL.md
├── 2 SYSTEM INFORMATION
│   ├── 2 SYSTEM INFORMATION.md
│   ├── 2.1 Workflow Diagram
│   │   ├── 2.1 Workflow Diagram.md
│   │   ├── 2.1.1 System Flow.md
│...
├── 3 START OF DAY AND END OF DAY PROCEDURE
│   ├── 3 START OF DAY AND END OF DAY PROCEDURE.md
│   ├── 3.1 Routine Job Operation
│   │   ├── 3.1 Routine Job Operation.md
│   │   ├── 3.1.1 Batch Job Specification.md
│...
│   │   └── 3.1.7 Miscellaneous.md
│   ├── 3.2 Online Job Specification
│   │   └── 3.2 Online Job Specification.md
│   ├── 3.3 Ad Hoc Operations
│   │   ├── 3.3 Ad Hoc Operations.md
│   │   ├── image3.png
│   │   ├── image4.png
│   │   └── image5.png
...
├── DOCUMENT LOCATION.md
├── DOCUMENT REVISION HISTORY.md
├── dv019_it_operation_guide_capdam_v2_5_frame.md
└── image1.png

this module is used to manage the knowledge files
"""

import os
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Any
from ..file.api import DocFile


class Knowledge:
    """
    Knowledge base manager.

    Manages a collection of knowledge files organized in a multi-layer folder structure.
    Supports uploading and downloading the entire knowledge base while preserving
    the original directory structure.
    """

    def __init__(self, base_path: str):
        """
        Initialize the Knowledge manager with a base folder path.

        :param base_path: Path to the knowledge base folder
        :type base_path: str
        """
        self.base_path = Path(base_path).resolve()
        if not self.base_path.exists():
            raise FileNotFoundError(f"Knowledge base path does not exist: {base_path}")
        if not self.base_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {base_path}")

        self._files: List[Path] = []
        self._structure: Dict[str, Any] = {}
        self._scan()

    def _scan(self) -> None:
        """
        Scan the knowledge base directory and build the file structure.
        """
        self._files = []
        self._structure = {
            'root': self.base_path.name,
            'path': str(self.base_path),
            'files': [],
            'directories': {}
        }

        for root, _, files in os.walk(self.base_path):
            root_path = Path(root)
            relative_root = root_path.relative_to(self.base_path)

            # Add files
            for file in files:
                file_path = root_path / file
                self._files.append(file_path)

                # Add to structure
                if str(relative_root) == '.':
                    self._structure['files'].append({
                        'name': file,
                        'path': str(file_path),
                        'relative_path': str(relative_root / file)
                    })
                else:
                    self._add_to_structure(
                        self._structure,
                        str(relative_root).split(os.sep),
                        file,
                        str(file_path),
                        str(relative_root / file)
                    )

    def _add_to_structure(
        self,
        structure: Dict,
        path_parts: List[str],
        file_name: str,
        full_path: str,
        relative_path: str
    ) -> None:
        """
        Add a file to the nested directory structure.

        :param structure: The structure dict to add to
        :type structure: Dict
        :param path_parts: List of directory path parts
        :type path_parts: List[str]
        :param file_name: Name of the file
        :type file_name: str
        :param full_path: Full filesystem path
        :type full_path: str
        :param relative_path: Relative path from base
        :type relative_path: str
        """
        current = structure
        for part in path_parts:
            if part not in current['directories']:
                current['directories'][part] = {
                    'files': [],
                    'directories': {}
                }
            current = current['directories'][part]

        current['files'].append({
            'name': file_name,
            'path': full_path,
            'relative_path': relative_path
        })

    def list_files(self) -> List[Dict]:
        """
        Get a list of all files in the knowledge base.

        :returns: List of file information dictionaries
        :rtype: List[Dict]
        """
        return [{'name': f.name, 'path': str(f)} for f in self._files]

    def get_structure(self) -> Dict:
        """
        Get the hierarchical structure of the knowledge base.

        :returns: Nested dictionary representing the directory structure
        :rtype: Dict
        """
        return self._structure

    def count_files(self) -> int:
        """
        Count the total number of files in the knowledge base.

        :returns: Number of files
        :rtype: int
        """
        return len(self._files)

    async def upload_all(self, prefix: Optional[str] = None) -> None:
        """
        Upload all files in the knowledge base to the storage backend.

        :param prefix: Optional prefix to prepend to all object names
        :type prefix: Optional[str]

        :raises RuntimeError: If storage client is not initialized
        """
        client = DocFile.client()

        tasks = []
        for file_path in self._files:
            # Calculate object name (relative path from base)
            relative_path = file_path.relative_to(self.base_path)

            # Add prefix if provided
            if prefix:
                object_name = str(Path(prefix) / relative_path)
            else:
                object_name = str(relative_path)

            tasks.append(
                client.fput_object(
                    object_name=object_name,
                    file_path=str(file_path)
                )
            )

        # Upload all files concurrently
        await asyncio.gather(*tasks)
        print(f"Uploaded {len(tasks)} files to storage")

    async def download_all(self, destination: Optional[str] = None) -> None:
        """
        Download all files from the knowledge base storage to a local directory.

        :param destination: Local destination directory path.
                          Defaults to the original base_path.
        :type destination: Optional[str]

        :raises RuntimeError: If storage client is not initialized
        """
        if destination:
            dest_path = Path(destination)
        else:
            dest_path = self.base_path

        # Ensure destination directory exists
        dest_path.mkdir(parents=True, exist_ok=True)

        client = DocFile.client()

        # List all objects
        objects = await client.list_objects(recursive=True)

        # Download tasks
        tasks = []
        for obj in objects:
            object_name = obj.object_name

            # Calculate local file path
            local_path = dest_path / object_name

            # Ensure parent directory exists
            local_path.parent.mkdir(parents=True, exist_ok=True)

            tasks.append(
                client.fget_object(
                    object_name=object_name,
                    file_path=str(local_path)
                )
            )

        # Download all files concurrently
        await asyncio.gather(*tasks)
        print(f"Downloaded {len(tasks)} files to {dest_path}")

    async def upload_file(self, file_path: str, prefix: Optional[str] = None) -> None:
        """
        Upload a specific file to the storage backend.

        :param file_path: Path to the local file (absolute or relative to base)
        :type file_path: str
        :param prefix: Optional prefix to prepend to the object name
        :type prefix: Optional[str]

        :raises FileNotFoundError: If the file does not exist
        :raises RuntimeError: If storage client is not initialized
        """
        client = DocFile.client()

        # Resolve the file path
        if os.path.isabs(file_path):
            resolved_path = Path(file_path)
        else:
            resolved_path = self.base_path / file_path

        if not resolved_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Calculate object name
        relative_path = resolved_path.relative_to(self.base_path)

        if prefix:
            object_name = str(Path(prefix) / relative_path)
        else:
            object_name = str(relative_path)

        await client.fput_object(
            object_name=object_name,
            file_path=str(resolved_path)
        )
        print(f"Uploaded file: {file_path} -> {object_name}")

    async def download_file(self, object_name: str, destination: Optional[str] = None) -> None:
        """
        Download a specific file from storage to a local path.

        :param object_name: Name of the object in storage
        :type object_name: str
        :param destination: Local destination path. If not provided,
                          uses the original relative path.
        :type destination: Optional[str]

        :raises RuntimeError: If storage client is not initialized
        """
        client = DocFile.client()

        if destination:
            dest_path = Path(destination)
        else:
            dest_path = self.base_path / object_name

        # Ensure parent directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        await client.fget_object(
            object_name=object_name,
            file_path=str(dest_path)
        )
        print(f"Downloaded file: {object_name} -> {dest_path}")

    def get_file_list_with_prefix(self, prefix: str = "") -> List[str]:
        """
        Get a list of all file relative paths with an optional prefix filter.

        :param prefix: Filter files by prefix (default: "")
        :type prefix: str

        :returns: List of relative file paths
        :rtype: List[str]
        """
        return [
            str(Path(prefix) / f['relative_path'])
            for f in self._structure['files']
        ]

    def __repr__(self) -> str:
        """
        String representation of the Knowledge instance.

        :returns: String representation
        :rtype: str
        """
        return f"Knowledge(base_path='{self.base_path}', files={len(self._files)})"
