"""
Product model.

Represents a single WPC product in inventory (panels, doors, boards, etc).
`available_quantity` is protected by a DB-level check constraint so it
can never go negative, no matter what application code does.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Numeric, DateTime, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("available_quantity >= 0", name="ck_products_quantity_non_negative"),
        CheckConstraint("minimum_stock_level >= 0", name="ck_products_min_stock_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "pcs", "sqft", "meters"

    available_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    minimum_stock_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )