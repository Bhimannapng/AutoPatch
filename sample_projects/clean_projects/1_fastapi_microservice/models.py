from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0.0)
    tags: List[str] = Field(default_factory=list)

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    tags: List[str]
    created_at: str
