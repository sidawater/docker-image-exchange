from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class UpdateDocumentRequest(BaseModel):
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    tags: Optional[List[Dict[str, str]]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class StartProcessingRequest(BaseModel):
    steps: Optional[List[str]] = None


class CompleteProcessingRequest(BaseModel):
    data: Dict[str, Any]
    status: str = Field(..., pattern="^(pending|processing|failed|done)$")


class SubmitReviewRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    reviewer: Optional[str] = None
    comment: Optional[str] = None
    timestamp: Optional[datetime] = None