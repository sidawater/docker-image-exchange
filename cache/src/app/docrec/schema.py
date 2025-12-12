"""
Document recognition related data structure definitions
"""

from typing import List
from pydantic import BaseModel


class DocumentRecognitionResult(BaseModel):
    """
    Document recognition result

    Attributes:
        documents: List of recognized document names
    """
    documents: List[str]
