"""
Query rewrite related data structure definitions
"""

from typing import Optional, List
from pydantic import BaseModel


class QueryRewriteResult(BaseModel):
    """
    Query rewrite result

    Attributes:
        rewritten_query: Rewritten query
    """
    rewritten_query: str
