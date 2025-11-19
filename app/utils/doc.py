from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from core.schema import Document, Tag
from app.models import Document, Tag, DocumentAlias, DocumentTagAssociation


class DocumentRepository:
    """
    Repository for document database operations with manual relationship handling
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_document(self, document: Document) -> Document:
        """
        Create a new document in database
        
        :param document: Document, document ORM object to create
        :returns: Document, created document
        """
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document
    
    async def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """
        Get document by ID
        
        :param document_id: str, document ID
        :returns: Optional[Document], document if found
        """
        stmt = select(Document).where(Document.id == document_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_document_by_storage_key(self, storage_key: str) -> Optional[Document]:
        """
        Get document by storage key
        
        :param storage_key: str, storage key in MinIO
        :returns: Optional[Document], document if found
        """
        stmt = select(Document).where(Document.storage_key == storage_key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_document_by_alias(self, alias: str) -> Optional[Document]:
        """
        Get document by alias
        
        :param alias: str, document alias
        :returns: Optional[Document], document if found
        """
        # First find the alias record
        alias_stmt = select(DocumentAlias).where(DocumentAlias.alias == alias)
        alias_result = await self.session.execute(alias_stmt)
        document_alias = alias_result.scalar_one_or_none()
        
        if not document_alias:
            return None
        
        # Then get the document
        return await self.get_document_by_id(document_alias.document_id)
    
    async def list_documents(
        self, 
        skip: int = 0, 
        limit: int = 100,
        name_filter: Optional[str] = None
    ) -> List[Document]:
        """
        List documents with pagination and filtering
        
        :param skip: int, number of records to skip
        :param limit: int, maximum number of records to return
        :param name_filter: Optional[str], filter by document name
        :returns: List[Document], list of documents
        """
        stmt = select(Document)
        
        if name_filter:
            stmt = stmt.where(Document.name.ilike(f"%{name_filter}%"))
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update_document_metadata(
        self, 
        document_id: str, 
        **kwargs
    ) -> Optional[Document]:
        """
        Update document metadata
        
        :param document_id: str, document ID to update
        :param kwargs: dict, fields to update
        :returns: Optional[Document], updated document if found
        """
        # Remove None values
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        
        if not update_data:
            return await self.get_document_by_id(document_id)
        
        # Always update the updated_at timestamp
        update_data['updated_at'] = datetime.utcnow()
        
        stmt = update(Document).where(Document.id == document_id).values(**update_data)
        await self.session.execute(stmt)
        await self.session.commit()
        
        return await self.get_document_by_id(document_id)
    
    async def get_document_tags(self, document_id: str) -> List[Tag]:
        """
        Get tags for a document
        
        :param document_id: str, document ID
        :returns: List[Tag], list of tags
        """
        # Get association records
        assoc_stmt = select(DocumentTagAssociation).where(
            DocumentTagAssociation.document_id == document_id
        )
        assoc_result = await self.session.execute(assoc_stmt)
        associations = list(assoc_result.scalars().all())
        
        if not associations:
            return []
        
        # Get tag IDs
        tag_ids = [assoc.tag_id for assoc in associations]
        
        # Get tags
        tag_stmt = select(Tag).where(Tag.id.in_(tag_ids))
        tag_result = await self.session.execute(tag_stmt)
        return list(tag_result.scalars().all())
    
    async def add_tag_to_document(self, document_id: str, tag: Tag) -> bool:
        """
        Add tag to document
        
        :param document_id: str, document ID
        :param tag: Tag, tag to add
        :returns: bool, True if successful
        """
        # Check if document exists
        document = await self.get_document_by_id(document_id)
        if not document:
            return False
        
        # Check if tag already exists by name
        existing_tag_stmt = select(Tag).where(Tag.name == tag.name)
        existing_tag_result = await self.session.execute(existing_tag_stmt)
        existing_tag = existing_tag_result.scalar_one_or_none()
        
        if existing_tag:
            tag_id = existing_tag.id
        else:
            # Create new tag
            self.session.add(tag)
            await self.session.commit()
            await self.session.refresh(tag)
            tag_id = tag.id
        
        # Check if association already exists
        assoc_stmt = select(DocumentTagAssociation).where(
            DocumentTagAssociation.document_id == document_id,
            DocumentTagAssociation.tag_id == tag_id
        )
        assoc_result = await self.session.execute(assoc_stmt)
        existing_assoc = assoc_result.scalar_one_or_none()
        
        if existing_assoc:
            return True  # Association already exists
        
        # Create association
        association = DocumentTagAssociation(
            document_id=document_id,
            tag_id=tag_id
        )
        self.session.add(association)
        await self.session.commit()
        
        return True
    
    async def remove_tag_from_document(self, document_id: str, tag_name: str) -> bool:
        """
        Remove tag from document
        
        :param document_id: str, document ID
        :param tag_name: str, tag name to remove
        :returns: bool, True if successful
        """
        # Find tag by name
        tag_stmt = select(Tag).where(Tag.name == tag_name)
        tag_result = await self.session.execute(tag_stmt)
        tag = tag_result.scalar_one_or_none()
        
        if not tag:
            return False
        
        # Delete association
        stmt = delete(DocumentTagAssociation).where(
            DocumentTagAssociation.document_id == document_id,
            DocumentTagAssociation.tag_id == tag.id
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0
    
    async def get_document_aliases(self, document_id: str) -> List[str]:
        """
        Get aliases for a document
        
        :param document_id: str, document ID
        :returns: List[str], list of aliases
        """
        stmt = select(DocumentAlias).where(DocumentAlias.document_id == document_id)
        result = await self.session.execute(stmt)
        aliases = list(result.scalars().all())
        return [alias.alias for alias in aliases]
    
    async def add_alias_to_document(self, document_id: str, alias: str) -> bool:
        """
        Add alias to document
        
        :param document_id: str, document ID
        :param alias: str, alias to add
        :returns: bool, True if successful
        """
        # Check if document exists
        document = await self.get_document_by_id(document_id)
        if not document:
            return False
        
        # Check if alias already exists
        existing_alias_stmt = select(DocumentAlias).where(DocumentAlias.alias == alias)
        existing_alias_result = await self.session.execute(existing_alias_stmt)
        existing_alias = existing_alias_result.scalar_one_or_none()
        
        if existing_alias:
            return False  # Alias must be unique
        
        # Create alias
        document_alias = DocumentAlias(alias=alias, document_id=document_id)
        self.session.add(document_alias)
        await self.session.commit()
        return True
    
    async def remove_alias_from_document(self, document_id: str, alias: str) -> bool:
        """
        Remove alias from document
        
        :param document_id: str, document ID
        :param alias: str, alias to remove
        :returns: bool, True if successful
        """
        stmt = delete(DocumentAlias).where(
            DocumentAlias.alias == alias,
            DocumentAlias.document_id == document_id
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete document and its associations
        
        :param document_id: str, document ID to delete
        :returns: bool, True if document was deleted
        """
        document = await self.get_document_by_id(document_id)
        if not document:
            return False
        
        # Delete tag associations
        tag_assoc_stmt = delete(DocumentTagAssociation).where(
            DocumentTagAssociation.document_id == document_id
        )
        await self.session.execute(tag_assoc_stmt)
        
        # Delete aliases
        alias_stmt = delete(DocumentAlias).where(
            DocumentAlias.document_id == document_id
        )
        await self.session.execute(alias_stmt)
        
        # Delete document
        await self.session.delete(document)
        await self.session.commit()
        return True


class TagRepository:
    """
    Repository for tag database operations
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_or_create_tag(self, name: str, display_name: str) -> Tag:
        """
        Get existing tag or create new one
        
        :param name: str, tag name
        :param display_name: str, tag display name
        :returns: Tag, tag object
        """
        stmt = select(Tag).where(Tag.name == name)
        result = await self.session.execute(stmt)
        existing_tag = result.scalar_one_or_none()
        
        if existing_tag:
            return existing_tag
        
        new_tag = Tag(name=name, display_name=display_name)
        self.session.add(new_tag)
        await self.session.commit()
        await self.session.refresh(new_tag)
        return new_tag
    
    async def list_tags(self) -> List[Tag]:
        """
        List all tags
        
        :returns: List[Tag], list of tags
        """
        stmt = select(Tag)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_tags_by_document(self, document_id: str) -> List[Tag]:
        """
        Get tags for a specific document
        
        :param document_id: str, document ID
        :returns: List[Tag], list of tags
        """
        # This method is kept for backward compatibility
        # In practice, you'd use DocumentRepository.get_document_tags
        doc_repo = DocumentRepository(self.session)
        return await doc_repo.get_document_tags(document_id)
