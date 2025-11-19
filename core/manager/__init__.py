import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, BinaryIO
from core.client.api import DocFile
from core.client.schema import Document, Tag, DocumentMetadata

logger = logging.getLogger(__name__)


class DocumentManager:
    """
    Document Manager - Coordinates business logic between schema and file layers
    Manages Document objects in memory, no persistent storage involved
    """
    
    def __init__(self, storage_prefix: str = "documents"):
        """
        Initialize the Document Manager
        
        :param storage_prefix: str, prefix for storage paths in MinIO
        """
        self.storage_prefix = storage_prefix.rstrip('/')
        self._documents: Dict[str, Document] = {}
    
    def _generate_document_key(self) -> str:
        """
        Generate unique document identifier
        
        :returns: str, unique document key
        """
        return str(uuid.uuid4())
    
    def _generate_storage_key(self, document_key: str, filename: str) -> str:
        """
        Generate storage path for MinIO
        
        :param document_key: str, unique document identifier
        :param filename: str, original filename
        :returns: str, storage key for MinIO
        """
        return f"{self.storage_prefix}/{document_key}/{filename}"
    
    def create_document(
        self,
        filename: str,
        content_type: str,
        size: int,
        description: Optional[str] = None,
        tags: List[Tag] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        document_key: Optional[str] = None,
        aliases: List[str] = None
    ) -> Document:
        """
        Create new document object (in memory only)
        
        :param filename: str, original filename
        :param content_type: str, MIME type of the file
        :param size: int, file size in bytes
        :param description: Optional[str], document description
        :param tags: List[Tag], list of document tags
        :param custom_fields: Optional[Dict[str, Any]], custom metadata fields
        :param document_key: Optional[str], custom document identifier
        :param aliases: List[str], list of document aliases
        :returns: Document, created document object
        :raises ValueError: if document key already exists
        """
        if document_key is None:
            document_key = self._generate_document_key()
        
        if document_key in self._documents:
            raise ValueError(f"Document with key '{document_key}' already exists")
        
        storage_key = self._generate_storage_key(document_key, filename)
        now = datetime.utcnow()
        
        metadata = DocumentMetadata(
            name=filename,
            content_type=content_type,
            size=size,
            created_at=now,
            updated_at=now,
            description=description,
            tags=tags or [],
            custom_fields=custom_fields or {},
            aliases=aliases or []
        )
        
        document = Document(
            key=document_key,
            metadata=metadata,
            storage_key=storage_key
        )
        
        self._documents[document_key] = document
        logger.info(f"Document created in memory: {document_key}")
        return document
    
    async def upload_from_file(
        self,
        file_path: str,
        filename: str,
        content_type: str,
        description: Optional[str] = None,
        tags: List[Tag] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        aliases: List[str] = None,
        document_key: Optional[str] = None
    ) -> Document:
        """
        Upload from local file and create document
        
        :param file_path: str, path to local file
        :param filename: str, original filename
        :param content_type: str, MIME type of the file
        :param description: Optional[str], document description
        :param tags: List[Tag], list of document tags
        :param custom_fields: Optional[Dict[str, Any]], custom metadata fields
        :param aliases: List[str], list of document aliases
        :param document_key: Optional[str], custom document identifier
        :returns: Document, created document object
        :raises Exception: if file upload fails
        """
        import os
        
        size = os.path.getsize(file_path)
        
        document = self.create_document(
            filename=filename,
            content_type=content_type,
            size=size,
            description=description,
            tags=tags,
            custom_fields=custom_fields,
            aliases=aliases,
            document_key=document_key
        )
        
        try:
            await DocFile.client().fput_object(
                object_name=document.storage_key,
                file_path=file_path,
                content_type=content_type,
                metadata={
                    "document_key": document.key,
                    "filename": filename,
                    "aliases": ",".join(aliases) if aliases else ""
                }
            )
            logger.info(f"File uploaded successfully: {document.storage_key}")
            return document
            
        except Exception as e:
            if document.key in self._documents:
                del self._documents[document.key]
            logger.error(f"File upload failed: {e}")
            raise
    
    async def upload_from_stream(
        self,
        data: BinaryIO,
        filename: str,
        content_type: str,
        size: int,
        description: Optional[str] = None,
        tags: List[Tag] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        aliases: List[str] = None,
        document_key: Optional[str] = None
    ) -> Document:
        """
        Upload from data stream and create document
        
        :param data: BinaryIO, binary data stream
        :param filename: str, original filename
        :param content_type: str, MIME type of the file
        :param size: int, data size in bytes
        :param description: Optional[str], document description
        :param tags: List[Tag], list of document tags
        :param custom_fields: Optional[Dict[str, Any]], custom metadata fields
        :param aliases: List[str], list of document aliases
        :param document_key: Optional[str], custom document identifier
        :returns: Document, created document object
        :raises Exception: if stream upload fails
        """
        document = self.create_document(
            filename=filename,
            content_type=content_type,
            size=size,
            description=description,
            tags=tags,
            custom_fields=custom_fields,
            aliases=aliases,
            document_key=document_key
        )
        
        try:
            await DocFile.client().put_object(
                object_name=document.storage_key,
                data=data,
                length=size,
                content_type=content_type,
                metadata={
                    "document_key": document.key,
                    "filename": filename,
                    "aliases": ",".join(aliases) if aliases else ""
                }
            )
            logger.info(f"Stream uploaded successfully: {document.storage_key}")
            return document
            
        except Exception as e:
            if document.key in self._documents:
                del self._documents[document.key]
            logger.error(f"Stream upload failed: {e}")
            raise
    
    async def download_to_file(
        self, 
        document_key: str, 
        file_path: str
    ) -> None:
        """
        Download document to local file
        
        :param document_key: str, unique document identifier
        :param file_path: str, local path to save file
        :raises ValueError: if document not found
        """
        document = self._documents.get(document_key)
        if not document:
            raise ValueError(f"Document not found: {document_key}")
        
        await DocFile.client().fget_object(
            object_name=document.storage_key,
            file_path=file_path
        )
        logger.info(f"Document downloaded to: {file_path}")
    
    async def get_content(self, document_key: str) -> bytes:
        """
        Get document content as bytes
        
        :param document_key: str, unique document identifier
        :returns: bytes, file content
        :raises ValueError: if document not found
        """
        document = self._documents.get(document_key)
        if not document:
            raise ValueError(f"Document not found: {document_key}")
        
        response = await DocFile.client().get_object(
            object_name=document.storage_key
        )
        
        try:
            content = response.read()
            return content
        finally:
            response.close()
            response.release_conn()
    
    def get_document(self, document_key: str) -> Optional[Document]:
        """
        Get document object
        
        :param document_key: str, unique document identifier
        :returns: Optional[Document], document object or None if not found
        """
        return self._documents.get(document_key)
    
    def list_documents(
        self, 
        prefix: str = "",
        limit: int = 100
    ) -> List[Document]:
        """
        List document objects in memory
        
        :param prefix: str, filter documents by key prefix
        :param limit: int, maximum number of documents to return
        :returns: List[Document], list of document objects
        """
        documents = [
            doc for doc in self._documents.values() 
            if doc.key.startswith(prefix)
        ]
        return documents[:limit]
    
    def update_metadata(
        self,
        document_key: str,
        description: Optional[str] = None,
        tags: Optional[List[Tag]] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        aliases: Optional[List[str]] = None
    ) -> Optional[Document]:
        """
        Update document metadata (in memory)
        
        :param document_key: str, unique document identifier
        :param description: Optional[str], new description
        :param tags: Optional[List[Tag]], new tags list
        :param custom_fields: Optional[Dict[str, Any]], new custom fields
        :param aliases: Optional[List[str]], new aliases list
        :returns: Optional[Document], updated document object or None if not found
        """
        document = self._documents.get(document_key)
        if not document:
            return None
        
        new_metadata = DocumentMetadata(
            name=document.metadata.name,
            content_type=document.metadata.content_type,
            size=document.metadata.size,
            created_at=document.metadata.created_at,
            updated_at=datetime.utcnow(),
            description=description or document.metadata.description,
            tags=tags or document.metadata.tags,
            custom_fields=custom_fields or document.metadata.custom_fields,
            aliases=aliases or document.metadata.aliases
        )
        
        updated_document = Document(
            key=document.key,
            metadata=new_metadata,
            storage_key=document.storage_key
        )
        
        self._documents[document_key] = updated_document
        logger.info(f"Document metadata updated: {document_key}")
        return updated_document
    
    async def get_presigned_url(
        self, 
        document_key: str, 
        expires: int = 3600
    ) -> Optional[str]:
        """
        Generate presigned URL for document download
        
        :param document_key: str, unique document identifier
        :param expires: int, URL expiration time in seconds
        :returns: Optional[str], presigned URL or None if document not found
        """
        document = self._documents.get(document_key)
        if not document:
            return None
        
        return await DocFile.client().presigned_get_object(
            object_name=document.storage_key,
            expires=expires
        )
    
    def document_exists(self, document_key: str) -> bool:
        """
        Check if document exists in memory
        
        :param document_key: str, unique document identifier
        :returns: bool, True if document exists
        """
        return document_key in self._documents
    
    def get_document_by_alias(self, alias: str) -> Optional[Document]:
        """
        Find document by alias
        
        :param alias: str, document alias to search for
        :returns: Optional[Document], document object or None if not found
        """
        for document in self._documents.values():
            if alias in document.metadata.aliases:
                return document
        return None
    
    def clear(self) -> None:
        """Clear all document objects from memory"""
        self._documents.clear()
        logger.info("All documents cleared from memory")
