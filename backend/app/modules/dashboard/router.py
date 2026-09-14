"""
Dashboard routes.

GET /dashboard/summary - aggregated stats for the dashboard page.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.schemas.dashboard import DashboardSummary, RecentOrderSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Total products + total stock across all products
    result = await db.execute(
        select(func.count(Product.id), func.coalesce(func.sum(Product.available_quantity), 0))
    )
    total_products, total_available_stock = result.one()

    # Low stock: quantity > 0 but at or below minimum
    low_stock_result = await db.execute(
        select(func.count(Product.id)).where(
            Product.available_quantity > 0,
            Product.available_quantity <= Product.minimum_stock_level,
        )
    )
    low_stock_products = low_stock_result.scalar_one()

    # Out of stock: quantity is exactly 0
    out_of_stock_result = await db.execute(
        select(func.count(Product.id)).where(Product.available_quantity == 0)
    )
    out_of_stock_products = out_of_stock_result.scalar_one()

    # Order counts by status
    total_orders_result = await db.execute(select(func.count(Order.id)))
    total_orders = total_orders_result.scalar_one()

    pending_orders_result = await db.execute(
        select(func.count(Order.id)).where(Order.status == OrderStatus.PENDING.value)
    )
    pending_orders = pending_orders_result.scalar_one()

    completed_orders_result = await db.execute(
        select(func.count(Order.id)).where(Order.status == OrderStatus.COMPLETED.value)
    )
    completed_orders = completed_orders_result.scalar_one()

    # Recent orders - last 5, most recent first, with total quantity per order
    recent_result = await db.execute(
        select(
            Order.id,
            Order.order_number,
            Order.customer_name,
            Order.status,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("total_quantity"),
        )
        .outerjoin(OrderItem, OrderItem.order_id == Order.id)
        .group_by(Order.id)
        .order_by(Order.created_at.desc())
        .limit(5)
    )
    recent_orders = [
        RecentOrderSummary(
            id=str(row.id),
            order_number=row.order_number,
            customer_name=row.customer_name,
            status=row.status,
            total_quantity=row.total_quantity,
        )
        for row in recent_result.all()
    ]

    return DashboardSummary(
        total_products=total_products,
        total_available_stock=total_available_stock,
        low_stock_products=low_stock_products,
        out_of_stock_products=out_of_stock_products,
        total_orders=total_orders,
        pending_orders=pending_orders,
        completed_orders=completed_orders,
        recent_orders=recent_orders,
    )