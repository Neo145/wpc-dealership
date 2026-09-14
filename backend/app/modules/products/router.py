"""
Product routes.

GET /products      - list all products (any logged-in user)
GET /products/:id  - get one product (any logged-in user)

POST/PUT/DELETE are added in later steps.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(prefix="/products", tags=["products"])


def compute_status(product: Product) -> str:
    """Derives stock status from quantity vs minimum stock level."""
    if product.available_quantity == 0:
        return "OUT_OF_STOCK"
    if product.available_quantity <= product.minimum_stock_level:
        return "LOW_STOCK"
    return "IN_STOCK"


def to_response(product: Product) -> ProductResponse:
    """Converts a Product DB row into a ProductResponse, filling in the
    computed 'status' field that doesn't exist on the model itself."""
    return ProductResponse(
        id=str(product.id),
        product_code=product.product_code,
        name=product.name,
        category=product.category,
        description=product.description,
        unit=product.unit,
        available_quantity=product.available_quantity,
        minimum_stock_level=product.minimum_stock_level,
        price=product.price,
        status=compute_status(product),
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.get("", response_model=list[ProductResponse])
async def list_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Product).order_by(Product.name))
    products = result.scalars().all()
    return [to_response(p) for p in products]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    return to_response(product)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    # Check product_code isn't already taken
    existing = await db.execute(
        select(Product).where(Product.product_code == payload.product_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product code '{payload.product_code}' already exists",
        )

    product = Product(**payload.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)

    return to_response(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # If product_code is being changed, make sure the new one isn't
    # already used by a different product.
    if payload.product_code and payload.product_code != product.product_code:
        existing = await db.execute(
            select(Product).where(Product.product_code == payload.product_code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product code '{payload.product_code}' already exists",
            )

    # Only update fields that were actually provided (exclude_unset=True
    # means fields left out of the request body are left untouched).
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)

    return to_response(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    await db.delete(product)
    await db.commit()