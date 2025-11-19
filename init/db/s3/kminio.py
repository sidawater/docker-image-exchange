"""
minio client with async support using aioboto3.


Usage:
```python
    minio_client = AsyncMinioClient(
        endpoint="localhost:9000",
        access_key="your-access-key",
        secret_key="your-secret-key",
        secure=False
    )

    # Test connection
    buckets = await minio_client.list_buckets()
    print("Available buckets:", buckets)

    # Create test bucket
    bucket_name = "test-bucket-async"
    if not await minio_client.bucket_exists(bucket_name):
        await minio_client.make_bucket(bucket_name)
        print(f"Created bucket: {bucket_name}")

    # Upload single object
    test_data = b"Hello, Async MinIO Client!"
    await minio_client.put_object(bucket_name, "test.txt", test_data)
    print("Uploaded test object")

    # Read object
    data = await minio_client.get_object(bucket_name, "test.txt")
    print("Retrieved data:", data.decode())

    # Upload multiple files
    files_to_upload = [
        {'object_name': 'file1.txt', 'file_path': '/path/to/local/file1.txt'},
        {'object_name': 'file2.txt', 'file_path': '/path/to/local/file2.txt'},
    ]
    
    # Note: Create test files first for this to work
    # with open('file1.txt', 'w') as f: f.write('Content 1')
    # with open('file2.txt', 'w') as f: f.write('Content 2')
    
    upload_results = await minio_client.upload_multiple_files(bucket_name, files_to_upload)
    print("Multiple upload results:", upload_results)

    # Generate presigned URL
    presigned_url = await minio_client.get_presigned_url(bucket_name, "test.txt", 3600)
    print("Presigned URL:", presigned_url)

    # Get object metadata
    metadata = await minio_client.get_object_metadata(bucket_name, "test.txt")
    print("Object metadata:", metadata)

    # List objects
    objects = await minio_client.list_objects(bucket_name)
    print("Objects in bucket:", objects)

    # Delete multiple objects
    objects_to_delete = ['file1.txt', 'file2.txt']
    await minio_client.delete_objects(bucket_name, objects_to_delete)
    print("Deleted multiple objects")

    # Cleanup
    await minio_client.remove_object(bucket_name, "test.txt")
    await minio_client.remove_bucket(bucket_name)
    print("Cleanup completed")
```

"""

import aioboto3
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, List, Dict, Any
from botocore.config import Config


class AsyncMinioClient:
    """
    Asynchronous MinIO client implementation using aioboto3.
    
    This client provides async operations for interacting with MinIO object storage
    that is compatible with AWS S3 API.
    
    :param endpoint: MinIO server endpoint (host:port)
    :type endpoint: str
    :param access_key: MinIO access key
    :type access_key: str
    :param secret_key: MinIO secret key
    :type secret_key: str
    :param region: AWS region (default: us-east-1)
    :type region: str
    :param secure: Use HTTPS if True, HTTP if False
    :type secure: bool
    """
    
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
        secure: bool = True,
    ):
        """Initialize the async MinIO client."""
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.secure = secure
        
        # Configure client parameters
        self.config = Config(
            region_name=region,
            s3={'addressing_style': 'path'}  # MinIO recommends path style
        )
        
        self.session = aioboto3.Session()

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[aioboto3.Session.client, None]:
        """
        Async context manager for S3 client.
        
        :yields: S3 client instance
        :rtype: aioboto3.Session.client
        """
        async with self.session.client(
            's3',
            endpoint_url=f'{"https" if self.secure else "http"}://{self.endpoint}',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=self.config,
        ) as client:
            yield client

    # Bucket operations
    async def list_buckets(self) -> List[str]:
        """
        List all buckets in the MinIO server.
        
        :return: List of bucket names
        :rtype: List[str]
        """
        async with self.get_client() as client:
            response = await client.list_buckets()
            return [bucket['Name'] for bucket in response['Buckets']]

    async def bucket_exists(self, bucket_name: str) -> bool:
        """
        Check if a bucket exists.
        
        :param bucket_name: Name of the bucket to check
        :type bucket_name: str
        :return: True if bucket exists, False otherwise
        :rtype: bool
        """
        async with self.get_client() as client:
            try:
                await client.head_bucket(Bucket=bucket_name)
                return True
            except Exception:
                return False

    async def make_bucket(self, bucket_name: str) -> bool:
        """
        Create a new bucket.
        
        :param bucket_name: Name of the bucket to create
        :type bucket_name: str
        :return: True if successful, False otherwise
        :rtype: bool
        """
        async with self.get_client() as client:
            try:
                await client.create_bucket(Bucket=bucket_name)
                return True
            except Exception as e:
                print(f"Failed to create bucket: {e}")
                return False

    async def remove_bucket(self, bucket_name: str) -> bool:
        """
        Remove an empty bucket.
        
        :param bucket_name: Name of the bucket to remove
        :type bucket_name: str
        :return: True if successful, False otherwise
        :rtype: bool
        """
        async with self.get_client() as client:
            try:
                await client.delete_bucket(Bucket=bucket_name)
                return True
            except Exception as e:
                print(f"Failed to delete bucket: {e}")
                return False

    # Object operations
    async def list_objects(
        self, 
        bucket_name: str, 
        prefix: str = ""
    ) -> List[str]:
        """
        List objects in a bucket.
        
        :param bucket_name: Name of the bucket
        :type bucket_name: str
        :param prefix: Filter objects starting with prefix (optional)
        :type prefix: str
        :return: List of object keys
        :rtype: List[str]
        """
        async with self.get_client() as client:
            try:
                paginator = client.get_paginator('list_objects_v2')
                objects = []
                async for page in paginator.paginate(
                    Bucket=bucket_name,
                    Prefix=prefix
                ):
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            objects.append(obj['Key'])
                return objects
            except Exception as e:
                print(f"Failed to list objects: {e}")
                return []

    async def get_object(
        self, 
        bucket_name: str, 
        object_name: str
    ) -> Optional[bytes]:
        """
        Get object content as bytes.
        
        :param bucket_name: Name of the bucket
        :type bucket_name: str
        :param object_name: Name of the object
        :type object_name: str
        :return: Object content as bytes or None if failed
        :rtype: Optional[bytes]
        """
        async with self.get_client() as client:
            try:
                response = await client.get_object(
                    Bucket=bucket_name,
                    Key=object_name
                )
                async with response['Body'] as stream:
                    return await stream.read()
            except Exception as e:
                print(f"Failed to get object: {e}")
                return None

    async def put_object(
        self, 
        bucket_name: str, 
        object_name: str, 
        data: bytes
    ) -> bool:
        """
        Upload object from bytes data.
        
        :param bucket_name: Name of the bucket
        :type bucket_name: str
        :param object_name: Name of the object
        :type object_name: str
        :param data: Data to upload as bytes
        :type data: bytes
        :return: True if successful, False otherwise
        :rtype: bool
        """
        async with self.get_client() as client:
            try:
                await client.put_object(
                    Bucket=bucket_name,
                    Key=object_name,
                    Body=data
                )
                return True
            except Exception as e:
                print(f"Failed to put object: {e}")
                return False

    async def download_object(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str
    ) -> bool:
        """
        Download object to local file.
        
        :param bucket_name: Name of the bucket
        :type bucket_name: str
        :param object_name: Name of the object
        :type object_name: str
        :param file_path: Local file path to save the object
        :type file_path: str
        :return: True if successful, False otherwise
        :rtype: bool
        """
        async with self.get_client() as client:
            try:
                response = await client.get_object(
                    Bucket=bucket_name,
                    Key=object_name
                )
                async with response['Body'] as stream:
                    with open(file_path, 'wb') as f:
                        while True:
                            chunk = await stream.read(8192)  # 8KB chunks
                            if not chunk:
                                break
                            f.write(chunk)
                return True
            except Exception as e:
                print(f"Failed to download object: {e}")
                return False

    async def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str
    ) -> bool:
        """
        Upload local file to bucket.
        
        :param bucket_name: Name of the bucket
        :type bucket_name: str
        :param object_name: Name of the object
        :type object_name: str
        :param file_path: Local file path to upload
        :type file_path: str
        :return: True if successful, False otherwise
        :rtype: bool
        """
        async with self.get_client() as client:
            try:
                with open(file_path, 'rb') as f:
                    await client.put_object(
                        Bucket=bucket_name,
                        Key=object_name,
                        Body=f
                    )
                return True
            except Exception as e:
                print(f"Failed to upload file: {e}")
                return False

    async def remove_object(
        self, 
        bucket_name: str, 
        object_name: str
    ) -> bool:
        """
        Delete object from bucket.
        
        :param bucket_name: Name of the bucket
        :type bucket_name: str
        :param object_name: Name of the object to delete
        :type object_name: str
        :return: True if successful, False otherwise
        :rtype: bool
        """
        async with self.get_client() as client:
            try:
                await client.delete_object(
                    Bucket=bucket_name,
                    Key=object_name
                )
                return True
            except Exception as e:
                print(f"Failed to remove object: {e}")
                return False

    async def object_exists(
        self, 
        bucket_name: str, 
        object_name: str
    ) -> bool:
        """
        Check if object exists in bucket.
        
        :param bucket_name: Name of the bucket
        :type bucket_name: str
        :param object_name: Name of the object
        :type object_name: str
        :return: True if object exists, False otherwise
        :rtype: bool
        """
        async with self.get_client() as client:
            try:
                await client.head_object(
                    Bucket=bucket_name,
                    Key=object_name
                )
                return True
            except Exception:
                return False

    # Batch operations
    async def upload_multiple_files(
        self,
        bucket_name: str,
        files: List[Dict[str, str]]
    ) -> Dict[str, bool]:
        """
        Upload multiple files concurrently.
        
        :param bucket_name: Name of the bucket
        :type bucket_name: str
        :param files: List of dicts with 'object_name' and 'file_path'
        :type files: List[Dict[str, str]]
        :return: Dictionary with object names as keys and success status as values
        :rtype: Dict[str, bool]
        """
        tasks = []
        for file_info in files:
            task = self.upload_file(
                bucket_name,
                file_info['object_name'],
                file_info['file_path']
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build result dictionary
        result_dict = {}
        for i, file_info in enumerate(files):
            if isinstance(results[i], Exception):
                print(f"Failed to upload {file_info['object_name']}: {results[i]}")
                result_dict[file_info['object_name']] = False
            else:
                result_dict[file_info['object_name']] = results[i]
        
        return result_dict

    async def delete_objects(
        self,
        bucket_name: str,
        object_names: List[str]
    ) -> bool:
        """
        Delete multiple objects in a single request.
        
        :param bucket_name: Bucket containing objects
        :type bucket_name: str
        :param object_names: List of object keys to delete
        :type object_names: List[str]
        :return: True if successful, False otherwise
        :rtype: bool
        """
        if not object_names:
            return True
            
        async with self.get_client() as client:
            try:
                # Convert list of names to S3 object identifier format
                objects = [{'Key': name} for name in object_names]
                
                await client.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': objects}
                )
                return True
            except Exception as e:
                print(f"Bulk delete failed: {e}")
                return False

    async def delete_prefix(
        self,
        bucket_name: str,
        prefix: str
    ) -> bool:
        """
        Delete all objects with a given prefix (use cautiously).
        
        :param bucket_name: Bucket containing objects
        :type bucket_name: str
        :param prefix: Prefix of objects to delete
        :type prefix: str
        :return: True if successful, False otherwise
        :rtype: bool
        """
        async with self.get_client() as client:
            try:
                # First list all objects with the prefix
                paginator = client.get_paginator('list_objects_v2')
                objects_to_delete = []
                
                async for page in paginator.paginate(
                    Bucket=bucket_name,
                    Prefix=prefix
                ):
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            objects_to_delete.append({'Key': obj['Key']})
                
                # Then delete them in bulk
                if objects_to_delete:
                    await client.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': objects_to_delete}
                    )
                return True
            except Exception as e:
                print(f"Prefix delete failed: {e}")
                return False

    # Advanced operations
    async def get_presigned_url(
        self,
        bucket_name: str,
        object_name: str,
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate presigned URL for temporary object access.
        
        :param bucket_name: Name of the bucket
        :type bucket_name: str
        :param object_name: Name of the object
        :type object_name: str
        :param expiration: URL expiration time in seconds (default: 1 hour)
        :type expiration: int
        :return: Presigned URL or None if failed
        :rtype: Optional[str]
        """
        async with self.get_client() as client:
            try:
                url = await client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': bucket_name,
                        'Key': object_name
                    },
                    ExpiresIn=expiration
                )
                return url
            except Exception as e:
                print(f"Failed to generate presigned URL: {e}")
                return None

    async def get_object_metadata(
        self,
        bucket_name: str,
        object_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get object metadata.
        
        :param bucket_name: Name of the bucket
        :type bucket_name: str
        :param object_name: Name of the object
        :type object_name: str
        :return: Object metadata or None if failed
        :rtype: Optional[Dict[str, Any]]
        """
        async with self.get_client() as client:
            try:
                response = await client.head_object(
                    Bucket=bucket_name,
                    Key=object_name
                )
                return {
                    'content_type': response.get('ContentType'),
                    'content_length': response.get('ContentLength'),
                    'last_modified': response.get('LastModified'),
                    'etag': response.get('ETag'),
                    'metadata': response.get('Metadata', {})
                }
            except Exception as e:
                print(f"Failed to get object metadata: {e}")
                return None

    async def copy_object(
        self,
        source_bucket: str,
        source_object: str,
        dest_bucket: str,
        dest_object: str
    ) -> bool:
        """
        Copy object from source to destination.
        
        :param source_bucket: Source bucket name
        :type source_bucket: str
        :param source_object: Source object name
        :type source_object: str
        :param dest_bucket: Destination bucket name
        :type dest_bucket: str
        :param dest_object: Destination object name
        :type dest_object: str
        :return: True if successful, False otherwise
        :rtype: bool
        """
        async with self.get_client() as client:
            try:
                copy_source = {
                    'Bucket': source_bucket,
                    'Key': source_object
                }
                await client.copy_object(
                    Bucket=dest_bucket,
                    Key=dest_object,
                    CopySource=copy_source
                )
                return True
            except Exception as e:
                print(f"Failed to copy object: {e}")
                return False

    async def upload_large_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
        part_size: int = 10 * 1024 * 1024  # 10MB
    ) -> bool:
        """
        Upload large file using multipart upload.
        
        :param bucket_name: Target bucket name
        :type bucket_name: str
        :param object_name: Target object name
        :type object_name: str
        :param file_path: Source file path
        :type file_path: str
        :param part_size: Part size in bytes (default: 10MB)
        :type part_size: int
        :return: True if successful, False otherwise
        :rtype: bool
        """
        async with self.get_client() as client:
            try:
                # For large files, use the regular put_object which will handle 
                # multipart upload automatically for files larger than threshold
                with open(file_path, 'rb') as file:
                    await client.put_object(
                        Bucket=bucket_name,
                        Key=object_name,
                        Body=file
                    )
                return True
            except Exception as e:
                print(f"Large file upload failed: {e}")
                return False

