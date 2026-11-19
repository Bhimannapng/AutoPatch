from fastapi import APIRouter, HTTPException, status
from typing import List
from models import ItemCreate, ItemResponse
from datetime import datetime

router = APIRouter(prefix="/items", tags=["items"])

# In-memory storage with thread safety consideration
ITEMS_DB: List[ItemResponse] = []

@router.get("/", response_model=List[ItemResponse])
def list_items():
    return ITEMS_DB

@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int):
    for item in ITEMS_DB:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate):
    new_id = len(ITEMS_DB) + 1
    item = ItemResponse(
        id=new_id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        tags=list(payload.tags),
        created_at=datetime.utcnow().isoformat()
    )
    ITEMS_DB.append(item)
    return item
