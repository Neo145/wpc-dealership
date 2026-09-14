"""
FastAPI application entrypoint.

For now this just sets up the app, CORS, and two health check endpoints
so we can confirm the backend runs and can talk to Postgres, before
building any real features.
"""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User

from app.core.config import settings
from app.core.database import get_db
from app.modules.auth.router import router as auth_router
from app.modules.products.router import router as products_router
from app.modules.orders.router import router as orders_router
from app.modules.dashboard.router import router as dashboard_router

app = FastAPI(title="WPC Dealership API", version="0.1.0")
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(dashboard_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Basic liveness check - does not touch the database."""
    return {"status": "ok", "service": "wpc-dealership-api"}


@app.get("/health/db")
async def health_check_db(db: AsyncSession = Depends(get_db)):
    """Confirms the API can actually reach and query Postgres."""
    result = await db.execute(text("SELECT 1"))
    value = result.scalar_one()
    return {"status": "ok", "database": "connected", "check_value": value}

@app.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Temporary test route - confirms token verification works."""
    return {"id": str(current_user.id), "email": current_user.email, "role": current_user.role}