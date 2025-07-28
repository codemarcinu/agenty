from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db

router = APIRouter()


# Pydantic models for request/response
class PantryItemCreate(BaseModel):
    name: str
    quantity: float
    unit: str
    category: str
    expiry_date: date | None = None
    notes: str | None = None


class PantryItemUpdate(BaseModel):
    name: str | None = None
    quantity: float | None = None
    unit: str | None = None
    category: str | None = None
    expiry_date: date | None = None
    notes: str | None = None


class PantryItemResponse(BaseModel):
    id: str
    name: str
    quantity: float
    unit: str
    category: str
    expiry_date: date | None = None
    added_date: datetime
    notes: str | None = None


# Sample data for development (replace with database queries)
SAMPLE_PANTRY_ITEMS = []


@router.get("/products", response_model=list[dict])
async def get_pantry_products(db: AsyncSession = Depends(get_db)) -> list[dict]:
    """
    Get all pantry items for the current user.
    In a real implementation, this would filter by user_id.
    """
    try:
        # For now, return sample data
        # TODO: Implement database queries with user filtering
        return SAMPLE_PANTRY_ITEMS
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to fetch pantry items", "error": str(e)},
        )


@router.post("/add", response_model=dict)
async def add_pantry_item(
    item: PantryItemCreate, db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Add a new item to the pantry.
    """
    try:
        # Create new pantry item
        new_item = {
            "id": str(len(SAMPLE_PANTRY_ITEMS) + 1),
            "name": item.name,
            "quantity": item.quantity,
            "unit": item.unit,
            "category": item.category,
            "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None,
            "added_date": datetime.now().isoformat(),
            "notes": item.notes,
        }

        # In a real implementation, save to database
        SAMPLE_PANTRY_ITEMS.append(new_item)

        return {
            "status_code": 200,
            "message": "Item added successfully",
            "data": new_item,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to add pantry item", "error": str(e)},
        )


@router.put("/update/{item_id}", response_model=dict)
async def update_pantry_item(
    item_id: str, item_update: PantryItemUpdate, db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Update an existing pantry item.
    """
    try:
        # Find the item to update
        item_index = None
        for i, item in enumerate(SAMPLE_PANTRY_ITEMS):
            if item["id"] == item_id:
                item_index = i
                break

        if item_index is None:
            raise HTTPException(
                status_code=404,
                detail={"message": "Pantry item not found", "item_id": item_id},
            )

        # Update the item
        updated_item = SAMPLE_PANTRY_ITEMS[item_index].copy()
        update_data = item_update.dict(exclude_unset=True)

        for key, value in update_data.items():
            if key == "expiry_date" and value:
                updated_item[key] = value.isoformat()
            else:
                updated_item[key] = value

        SAMPLE_PANTRY_ITEMS[item_index] = updated_item

        return {
            "status_code": 200,
            "message": "Item updated successfully",
            "data": updated_item,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to update pantry item", "error": str(e)},
        )


@router.delete("/delete/{item_id}", response_model=dict)
async def delete_pantry_item(item_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """
    Delete a pantry item.
    """
    try:
        # Find the item to delete
        item_index = None
        for i, item in enumerate(SAMPLE_PANTRY_ITEMS):
            if item["id"] == item_id:
                item_index = i
                break

        if item_index is None:
            raise HTTPException(
                status_code=404,
                detail={"message": "Pantry item not found", "item_id": item_id},
            )

        # Remove the item
        deleted_item = SAMPLE_PANTRY_ITEMS.pop(item_index)

        return {
            "status_code": 200,
            "message": "Item deleted successfully",
            "data": {"deleted_item": deleted_item},
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to delete pantry item", "error": str(e)},
        )


@router.get("/expiring-soon", response_model=list[dict])
async def get_expiring_items(
    days: int = 7, db: AsyncSession = Depends(get_db)
) -> list[dict]:
    """
    Get items that are expiring soon (within specified days).
    """
    try:
        today = date.today()
        expiring_items = []

        for item in SAMPLE_PANTRY_ITEMS:
            if item["expiry_date"]:
                expiry_date = datetime.fromisoformat(item["expiry_date"]).date()
                days_until_expiry = (expiry_date - today).days

                if 0 <= days_until_expiry <= days:
                    expiring_items.append(
                        {**item, "days_until_expiry": days_until_expiry}
                    )

        return expiring_items
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to fetch expiring items", "error": str(e)},
        )


@router.get("/expired", response_model=list[dict])
async def get_expired_items(db: AsyncSession = Depends(get_db)) -> list[dict]:
    """
    Get items that have expired.
    """
    try:
        today = date.today()
        expired_items = []

        for item in SAMPLE_PANTRY_ITEMS:
            if item["expiry_date"]:
                expiry_date = datetime.fromisoformat(item["expiry_date"]).date()

                if expiry_date < today:
                    expired_items.append(
                        {**item, "days_expired": (today - expiry_date).days}
                    )

        return expired_items
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to fetch expired items", "error": str(e)},
        )


@router.get("/categories", response_model=list[str])
async def get_pantry_categories(db: AsyncSession = Depends(get_db)) -> list[str]:
    """
    Get all unique categories in the pantry.
    """
    try:
        categories = list({item["category"] for item in SAMPLE_PANTRY_ITEMS})
        return sorted(categories)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to fetch categories", "error": str(e)},
        )


@router.get("/statistics", response_model=dict)
async def get_pantry_statistics(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Get pantry statistics.
    """
    try:
        today = date.today()
        total_items = len(SAMPLE_PANTRY_ITEMS)
        expiring_soon = 0
        expired = 0
        categories_count = len({item["category"] for item in SAMPLE_PANTRY_ITEMS})

        for item in SAMPLE_PANTRY_ITEMS:
            if item["expiry_date"]:
                expiry_date = datetime.fromisoformat(item["expiry_date"]).date()
                days_until_expiry = (expiry_date - today).days

                if days_until_expiry < 0:
                    expired += 1
                elif days_until_expiry <= 7:
                    expiring_soon += 1

        return {
            "total_items": total_items,
            "expiring_soon": expiring_soon,
            "expired": expired,
            "categories_count": categories_count,
            "last_updated": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": "Failed to fetch statistics", "error": str(e)},
        )
