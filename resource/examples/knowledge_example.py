"""
Example usage of the Knowledge class.

This example demonstrates how to use the Knowledge class to manage
a knowledge base with uploading and downloading capabilities.
"""

import asyncio
from pathlib import Path
from core.manager import Knowledge
from core.file.api import DocFile


async def main():
    """
    Example demonstrating Knowledge class functionality.
    """
    # Initialize DocFile client (MinIO)
    DocFile.init(
        bucket_name="knowledge-base",
        backend='minio',
        endpoint="minio.example.com:9000",
        access_key="your_access_key",
        secret_key="your_secret_key",
        secure=False
    )

    # Initialize Knowledge manager with a folder path
    knowledge = Knowledge("/path/to/knowledge/folder")

    # Display knowledge base information
    print(f"Knowledge base: {knowledge}")
    print(f"Total files: {knowledge.count_files()}")

    # List all files
    print("\nAll files:")
    for file_info in knowledge.list_files():
        print(f"  - {file_info['name']}: {file_info['path']}")

    # Display structure
    print("\nDirectory structure:")
    print(knowledge.get_structure())

    # Upload all files to storage
    print("\n--- Uploading all files ---")
    await knowledge.upload_all(prefix="dv019_it_operation_guide")

    # Upload a specific file
    print("\n--- Uploading specific file ---")
    await knowledge.upload_file(
        "1 SERVICE LEVEL/1 SERVICE LEVEL.md",
        prefix="dv019_it_operation_guide"
    )

    # Download all files
    print("\n--- Downloading all files ---")
    await knowledge.download_all(destination="/path/to/download/folder")

    # Download a specific file
    print("\n--- Downloading specific file ---")
    await knowledge.download_file(
        "dv019_it_operation_guide/1 SERVICE LEVEL/1 SERVICE LEVEL.md",
        destination="/path/to/specific/file.md"
    )

    # Get file list with prefix
    print("\n--- File list with prefix ---")
    files = knowledge.get_file_list_with_prefix("dv019_it_operation_guide")
    for file in files:
        print(f"  - {file}")


if __name__ == "__main__":
    asyncio.run(main())
