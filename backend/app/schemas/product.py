"""
Pydantic schemas for products.

ProductCreate: what's required to create a new product.
ProductUpdate: same fields, but all optional (partial updates via PUT).
ProductResponse: what we send back to the client - includes id and
timestamps that only exist once a product is in the database.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    product_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    unit: str = Field(..., min_length=1, max_length=20)
    available_quantity: int = Field(..., ge=0)
    minimum_stock_level: int = Field(..., ge=0)
    price: Decimal | None = Field(default=None, ge=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    product_code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    available_quantity: int | None = Field(default=None, ge=0)
    minimum_stock_level: int | None = Field(default=None, ge=0)
    price: Decimal | None = Field(default=None, ge=0)


class ProductResponse(ProductBase):
    id: str
    status: str  # computed: "IN_STOCK" / "LOW_STOCK" / "OUT_OF_STOCK"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}