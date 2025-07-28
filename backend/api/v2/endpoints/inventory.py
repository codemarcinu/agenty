"""
Inventory Management API Endpoints

This module provides API endpoints for managing inventory items:
- List inventory items
- Get inventory item details
- Add inventory items
- Update inventory items
- Delete inventory items
- Inventory statistics
"""

from datetime import date, datetime
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.database import get_db
from models.shopping import Product
from schemas.shopping_schemas import ProductCreate, ProductUpdate

router = APIRouter(prefix="/inventory", tags=["Inventory Management"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=list[dict[str, Any]])
async def get_inventory_items(
    category: str | None = Query(None, description="Filter by category"),
    status: str | None = Query(
        None, description="Filter by status (in-stock, low-stock, out-of-stock)"
    ),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """
    Get all inventory items with optional filtering
    """
    try:
        # Build query
        query = select(Product).where(Product.is_consumed == 0)

        if category:
            query = query.where(Product.category == category)

        # Execute query
        result = await db.execute(query)
        products = result.scalars().all()

        # Convert to inventory format
        inventory_items = []
        for product in products:
            # Determine status based on quantity and expiry
            status = "in-stock"
            if product.quantity is None or product.quantity <= 0:
                status = "out-of-stock"
            elif product.quantity <= (product.unit_price or 1) * 0.2:  # 20% threshold
                status = "low-stock"

            # Check expiry
            expiry_status = None
            if product.expiration_date:
                days_until_expiry = (product.expiration_date - date.today()).days
                if days_until_expiry < 0:
                    expiry_status = "expired"
                elif days_until_expiry <= 3:
                    expiry_status = "expiring-soon"
                else:
                    expiry_status = "good"

            inventory_item = {
                "id": str(product.id),
                "name": product.name,
                "category": product.category or "Uncategorized",
                "quantity": product.quantity or 0,
                "unit": product.unit or "szt",
                "expiryDate": (
                    product.expiration_date.isoformat()
                    if product.expiration_date
                    else None
                ),
                "minQuantity": 1,  # Default minimum quantity
                "status": status,
                "unitPrice": product.unit_price,
                "notes": product.notes,
                "createdAt": product.created_at.isoformat(),
                "updatedAt": product.updated_at.isoformat(),
                "expiryStatus": expiry_status,
            }
            inventory_items.append(inventory_item)

        return inventory_items

    except Exception as e:
        logger.error(f"Error getting inventory items: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{item_id}", response_model=dict[str, Any])
async def get_inventory_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get specific inventory item by ID
    """
    try:
        result = await db.execute(select(Product).where(Product.id == item_id))
        product = result.scalars().first()

        if not product:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        # Determine status
        status = "in-stock"
        if product.quantity is None or product.quantity <= 0:
            status = "out-of-stock"
        elif product.quantity <= (product.unit_price or 1) * 0.2:
            status = "low-stock"

        return {
            "id": str(product.id),
            "name": product.name,
            "category": product.category or "Uncategorized",
            "quantity": product.quantity or 0,
            "unit": product.unit or "szt",
            "expiryDate": (
                product.expiration_date.isoformat() if product.expiration_date else None
            ),
            "minQuantity": 1,
            "status": status,
            "unitPrice": product.unit_price,
            "notes": product.notes,
            "createdAt": product.created_at.isoformat(),
            "updatedAt": product.updated_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting inventory item {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=dict[str, Any])
async def create_inventory_item(
    item_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Create a new inventory item
    """
    try:
        # Create new product
        product = Product(
            name=item_data.name,
            category=item_data.category,
            quantity=item_data.quantity,
            unit=item_data.unit,
            unit_price=item_data.unit_price,
            expiration_date=item_data.expiration_date,
            notes=item_data.notes,
            trip_id=1,  # Default trip ID - in real app would be user's current trip
        )

        db.add(product)
        await db.commit()
        await db.refresh(product)

        return {
            "id": str(product.id),
            "name": product.name,
            "category": product.category or "Uncategorized",
            "quantity": product.quantity or 0,
            "unit": product.unit or "szt",
            "expiryDate": (
                product.expiration_date.isoformat() if product.expiration_date else None
            ),
            "minQuantity": 1,
            "status": "in-stock",
            "unitPrice": product.unit_price,
            "notes": product.notes,
            "createdAt": product.created_at.isoformat(),
            "updatedAt": product.updated_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error creating inventory item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{item_id}", response_model=dict[str, Any])
async def update_inventory_item(
    item_id: int,
    item_data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Update an existing inventory item
    """
    try:
        result = await db.execute(select(Product).where(Product.id == item_id))
        product = result.scalars().first()

        if not product:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        # Update fields
        if item_data.name is not None:
            product.name = item_data.name
        if item_data.category is not None:
            product.category = item_data.category
        if item_data.quantity is not None:
            product.quantity = item_data.quantity
        if item_data.unit is not None:
            product.unit = item_data.unit
        if item_data.unit_price is not None:
            product.unit_price = item_data.unit_price
        if item_data.expiration_date is not None:
            product.expiration_date = item_data.expiration_date
        if item_data.notes is not None:
            product.notes = item_data.notes

        product.updated_at = datetime.now()

        await db.commit()
        await db.refresh(product)

        # Determine status
        status = "in-stock"
        if product.quantity is None or product.quantity <= 0:
            status = "out-of-stock"
        elif product.quantity <= (product.unit_price or 1) * 0.2:
            status = "low-stock"

        return {
            "id": str(product.id),
            "name": product.name,
            "category": product.category or "Uncategorized",
            "quantity": product.quantity or 0,
            "unit": product.unit or "szt",
            "expiryDate": (
                product.expiration_date.isoformat() if product.expiration_date else None
            ),
            "minQuantity": 1,
            "status": status,
            "unitPrice": product.unit_price,
            "notes": product.notes,
            "createdAt": product.created_at.isoformat(),
            "updatedAt": product.updated_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating inventory item {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{item_id}")
async def delete_inventory_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete an inventory item (mark as consumed)
    """
    try:
        result = await db.execute(select(Product).where(Product.id == item_id))
        product = result.scalars().first()

        if not product:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        # Mark as consumed instead of deleting
        product.is_consumed = 1
        product.updated_at = datetime.now()

        await db.commit()

        return JSONResponse(
            status_code=200,
            content={
                "message": "Inventory item marked as consumed successfully",
                "item_id": item_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting inventory item {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_inventory_stats(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get inventory statistics summary
    """
    try:
        # Get all active inventory items
        result = await db.execute(select(Product).where(Product.is_consumed == 0))
        products = result.scalars().all()

        total_items = len(products)
        in_stock = 0
        low_stock = 0
        out_of_stock = 0
        expiring_soon = 0
        expired = 0

        for product in products:
            # Count by status
            if product.quantity is None or product.quantity <= 0:
                out_of_stock += 1
            elif product.quantity <= (product.unit_price or 1) * 0.2:
                low_stock += 1
            else:
                in_stock += 1

            # Count by expiry
            if product.expiration_date:
                days_until_expiry = (product.expiration_date - date.today()).days
                if days_until_expiry < 0:
                    expired += 1
                elif days_until_expiry <= 3:
                    expiring_soon += 1

        return {
            "totalItems": total_items,
            "inStock": in_stock,
            "lowStock": low_stock,
            "outOfStock": out_of_stock,
            "expiringSoon": expiring_soon,
            "expired": expired,
            "categories": {
                "dairy": len([p for p in products if p.category == "Nabiał"]),
                "bakery": len([p for p in products if p.category == "Pieczywo"]),
                "vegetables": len([p for p in products if p.category == "Warzywa"]),
                "fruits": len([p for p in products if p.category == "Owoce"]),
                "meat": len([p for p in products if p.category == "Mięso"]),
                "other": len(
                    [
                        p
                        for p in products
                        if p.category
                        not in ["Nabiał", "Pieczywo", "Warzywa", "Owoce", "Mięso"]
                    ]
                ),
            },
        }

    except Exception as e:
        logger.error(f"Error getting inventory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
