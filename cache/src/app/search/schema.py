"""
Search related data structure definitions
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class SearchResult(BaseModel):
    """
    Search result

    Attributes:
        status: Search status, success or failed
        documentations: List of document names
        results: List of search results
        error: Error message (optional)
    """
    status: str
    documentations: List[str]
    results: List[Dict[str, Any]]
    error: Optional[str] = None


class ReferenceItem(BaseModel):
    """
    Reference item

    Attributes:
        id: Reference ID
        title: Title
        url: Link
        anchor_id: Anchor ID
        doc_key: Document key
        score: Score
        preview: Preview text
        source_query: Source query
    """
    id: str
    title: str
    url: str
    anchor_id: str
    doc_key: str
    score: float
    preview: str
    source_query: str
