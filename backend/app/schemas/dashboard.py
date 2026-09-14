"""
Pydantic schema for the dashboard summary.
"""

from pydantic import BaseModel


class RecentOrderSummary(BaseModel):
    id: str
    order_number: str
    customer_name: str
    status: str
    total_quantity: int


class DashboardSummary(BaseModel):
    total_products: int
    total_available_stock: int
    low_stock_products: int
    out_of_stock_products: int
    total_orders: int
    pending_orders: int
    completed_orders: int
    recent_orders: list[RecentOrderSummary]