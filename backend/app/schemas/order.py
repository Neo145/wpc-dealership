"""
Pydantic schemas for orders.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_phone: str = Field(..., min_length=1, max_length=20)
    notes: str | None = Field(default=None, max_length=1000)
    items: list[OrderItemCreate] = Field(..., min_length=1)


class OrderStatusUpdate(BaseModel):
    status: str  # "PENDING" | "CONFIRMED" | "COMPLETED" | "CANCELLED"


class OrderItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    product_code: str
    quantity: int
    unit_price_snapshot: Decimal | None

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: str
    order_number: str
    customer_name: str
    customer_phone: str
    status: str
    notes: str | None
    total_quantity: int
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}