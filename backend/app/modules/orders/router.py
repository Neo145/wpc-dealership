"""
Order routes.

POST /orders                 - create an order; auto-confirms and deducts
                                stock immediately if enough is available,
                                otherwise stays PENDING for manual review
GET  /orders                 - list all orders
GET  /orders/:id             - get one order with full item details
PUT  /orders/:id/status      - manually change status; CONFIRM deducts
                                stock safely, CANCEL restores it
GET  /orders/:id/invoice     - download a PDF invoice for a confirmed
                                or completed order

Race condition protection: whenever stock is deducted (auto-confirm on
create, or manual confirm), we lock each product row with
SELECT ... FOR UPDATE inside a transaction. This means if two people try
to confirm/create orders touching the same product at the same moment,
the second one waits until the first transaction finishes and sees the
updated (already-reduced) stock - so it always makes its decision based
on the true current stock, instead of both succeeding and pushing stock
negative.
"""

import random
import string
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse, OrderItemResponse, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["orders"])

VALID_STATUSES = {s.value for s in OrderStatus}

# Which status transitions are allowed via the manual PUT endpoint.
# Prevents nonsense like moving a CANCELLED order back to PENDING, or
# CONFIRMED straight to PENDING.
ALLOWED_TRANSITIONS = {
    OrderStatus.PENDING.value: {OrderStatus.CONFIRMED.value, OrderStatus.CANCELLED.value},
    OrderStatus.CONFIRMED.value: {OrderStatus.COMPLETED.value, OrderStatus.CANCELLED.value},
    OrderStatus.COMPLETED.value: set(),
    OrderStatus.CANCELLED.value: set(),
}


def generate_order_number() -> str:
    suffix = "".join(random.choices(string.digits, k=6))
    return f"ORD-{suffix}"


async def to_response(db: AsyncSession, order: Order) -> OrderResponse:
    result = await db.execute(
        select(OrderItem, Product)
        .join(Product, OrderItem.product_id == Product.id)
        .where(OrderItem.order_id == order.id)
    )
    rows = result.all()

    items = [
        OrderItemResponse(
            id=str(item.id),
            product_id=str(item.product_id),
            product_name=product.name,
            product_code=product.product_code,
            quantity=item.quantity,
            unit_price_snapshot=item.unit_price_snapshot,
        )
        for item, product in rows
    ]

    return OrderResponse(
        id=str(order.id),
        order_number=order.order_number,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        status=order.status,
        notes=order.notes,
        total_quantity=sum(i.quantity for i in items),
        items=items,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate every product exists before creating anything.
    product_ids = [item.product_id for item in payload.items]
    result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
    products = {str(p.id): p for p in result.scalars().all()}

    for item in payload.items:
        if item.product_id not in products:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {item.product_id} does not exist",
            )

    order = Order(
        order_number=generate_order_number(),
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        notes=payload.notes,
        status=OrderStatus.PENDING.value,
        created_by=current_user.id,
    )
    db.add(order)
    await db.flush()  # assigns order.id without committing yet

    for item in payload.items:
        product = products[item.product_id]
        db.add(OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item.quantity,
            unit_price_snapshot=product.price,
        ))

    await db.flush()

    # --- Auto-confirm attempt ---
    # If every ordered item has enough stock right now, confirm the order
    # immediately and deduct stock - no manual admin step needed. If any
    # item is short, leave the order as PENDING so an admin can review it.
    # Uses the same row-locking pattern as the manual confirm endpoint to
    # stay safe under concurrent orders.
    items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    order_items = items_result.scalars().all()

    can_auto_confirm = True
    locked_products = {}
    for item in order_items:
        product_result = await db.execute(
            select(Product).where(Product.id == item.product_id).with_for_update()
        )
        product = product_result.scalar_one()
        locked_products[str(product.id)] = product
        if product.available_quantity < item.quantity:
            can_auto_confirm = False

    if can_auto_confirm:
        for item in order_items:
            product = locked_products[str(item.product_id)]
            product.available_quantity -= item.quantity
        order.status = OrderStatus.CONFIRMED.value

    await db.commit()
    await db.refresh(order)

    return await to_response(db, order)


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Order).order_by(Order.created_at.desc()))
    orders = result.scalars().all()
    return [await to_response(db, o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    return await to_response(db, order)


@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    payload: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_status = payload.status

    if new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}",
        )

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if new_status not in ALLOWED_TRANSITIONS.get(order.status, set()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot change order from {order.status} to {new_status}",
        )

    # Load this order's items.
    items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    order_items = items_result.scalars().all()

    if new_status == OrderStatus.CONFIRMED.value:
        # --- Critical section: deduct stock safely ---
        for item in order_items:
            product_result = await db.execute(
                select(Product).where(Product.id == item.product_id).with_for_update()
            )
            product = product_result.scalar_one()

            if product.available_quantity < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Insufficient stock for '{product.name}': "
                        f"requested {item.quantity}, available {product.available_quantity}"
                    ),
                )

        for item in order_items:
            product_result = await db.execute(
                select(Product).where(Product.id == item.product_id).with_for_update()
            )
            product = product_result.scalar_one()
            product.available_quantity -= item.quantity

    elif new_status == OrderStatus.CANCELLED.value and order.status == OrderStatus.CONFIRMED.value:
        # Stock was deducted when this was confirmed - restore it.
        for item in order_items:
            product_result = await db.execute(
                select(Product).where(Product.id == item.product_id).with_for_update()
            )
            product = product_result.scalar_one()
            product.available_quantity += item.quantity

    order.status = new_status
    await db.commit()
    await db.refresh(order)

    return await to_response(db, order)


@router.get("/{order_id}/invoice")
async def get_order_invoice(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates a simple PDF invoice for a CONFIRMED or COMPLETED order.
    """
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.status not in (OrderStatus.CONFIRMED.value, OrderStatus.COMPLETED.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice is only available for confirmed or completed orders",
        )

    order_response = await to_response(db, order)

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 25 * mm
    p.setFont("Helvetica-Bold", 18)
    p.drawString(20 * mm, y, "WPC Dealership")
    p.setFont("Helvetica", 10)
    y -= 7 * mm
    p.drawString(20 * mm, y, "Invoice")

    y -= 12 * mm
    p.setFont("Helvetica-Bold", 11)
    p.drawString(20 * mm, y, f"Order #: {order_response.order_number}")
    y -= 6 * mm
    p.setFont("Helvetica", 10)
    p.drawString(20 * mm, y, f"Status: {order_response.status}")
    y -= 6 * mm
    p.drawString(20 * mm, y, f"Date: {order_response.created_at.strftime('%d %b %Y, %I:%M %p')}")

    y -= 10 * mm
    p.setFont("Helvetica-Bold", 11)
    p.drawString(20 * mm, y, "Bill To")
    y -= 6 * mm
    p.setFont("Helvetica", 10)
    p.drawString(20 * mm, y, f"{order_response.customer_name}")
    y -= 5 * mm
    p.drawString(20 * mm, y, f"{order_response.customer_phone}")

    y -= 12 * mm
    p.setFont("Helvetica-Bold", 10)
    p.drawString(20 * mm, y, "Product")
    p.drawString(110 * mm, y, "Code")
    p.drawString(150 * mm, y, "Qty")
    y -= 2 * mm
    p.line(20 * mm, y, 190 * mm, y)
    y -= 6 * mm

    p.setFont("Helvetica", 9)
    for item in order_response.items:
        p.drawString(20 * mm, y, item.product_name[:45])
        p.drawString(110 * mm, y, item.product_code)
        p.drawString(150 * mm, y, str(item.quantity))
        y -= 6 * mm
        if y < 30 * mm:
            p.showPage()
            y = height - 25 * mm

    y -= 4 * mm
    p.line(20 * mm, y, 190 * mm, y)
    y -= 8 * mm
    p.setFont("Helvetica-Bold", 10)
    p.drawString(20 * mm, y, f"Total Quantity: {order_response.total_quantity}")

    if order_response.notes:
        y -= 10 * mm
        p.setFont("Helvetica", 9)
        p.drawString(20 * mm, y, f"Notes: {order_response.notes}")

    p.showPage()
    p.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{order_response.order_number}.pdf"'},
    )