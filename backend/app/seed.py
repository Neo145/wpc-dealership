"""
Seed script.

Populates the database with:
  - One ADMIN user and one STAFF user, so you can log in once the
    frontend exists.
  - 20 realistic sample WPC products, so the app has real data to show.

Run this once after migrations are applied. Safe to re-run - it checks
for existing records first and skips them instead of creating duplicates.
"""

import asyncio

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.product import Product

from sqlalchemy import select


SAMPLE_USERS = [
    {
        "email": "admin@wpcdealer.com",
        "password": "Admin@123",
        "name": "Store Owner",
        "role": UserRole.ADMIN,
    },
    {
        "email": "staff@wpcdealer.com",
        "password": "Staff@123",
        "name": "Sales Staff",
        "role": UserRole.STAFF,
    },
]

SAMPLE_PRODUCTS = [
    {"product_code": "WPC-PNL-001", "name": "WPC Panel A - White", "category": "Panels", "unit": "sqft", "available_quantity": 500, "minimum_stock_level": 50},
    {"product_code": "WPC-PNL-002", "name": "WPC Panel B - Oak Wood", "category": "Panels", "unit": "sqft", "available_quantity": 350, "minimum_stock_level": 50},
    {"product_code": "WPC-PNL-003", "name": "WPC Panel C - Walnut", "category": "Panels", "unit": "sqft", "available_quantity": 120, "minimum_stock_level": 50},
    {"product_code": "WPC-PNL-004", "name": "WPC Panel D - Grey Matte", "category": "Panels", "unit": "sqft", "available_quantity": 40, "minimum_stock_level": 50},
    {"product_code": "WPC-DR-001", "name": "WPC Door - Classic White", "category": "Doors", "unit": "pcs", "available_quantity": 45, "minimum_stock_level": 10},
    {"product_code": "WPC-DR-002", "name": "WPC Door - Teak Finish", "category": "Doors", "unit": "pcs", "available_quantity": 28, "minimum_stock_level": 10},
    {"product_code": "WPC-DR-003", "name": "WPC Door - Rosewood", "category": "Doors", "unit": "pcs", "available_quantity": 8, "minimum_stock_level": 10},
    {"product_code": "WPC-DR-004", "name": "WPC Bathroom Door - Waterproof", "category": "Doors", "unit": "pcs", "available_quantity": 60, "minimum_stock_level": 15},
    {"product_code": "WPC-BRD-001", "name": "WPC Board 8x4 - 12mm", "category": "Boards", "unit": "pcs", "available_quantity": 200, "minimum_stock_level": 30},
    {"product_code": "WPC-BRD-002", "name": "WPC Board 8x4 - 18mm", "category": "Boards", "unit": "pcs", "available_quantity": 150, "minimum_stock_level": 30},
    {"product_code": "WPC-BRD-003", "name": "WPC Board 8x4 - 25mm", "category": "Boards", "unit": "pcs", "available_quantity": 15, "minimum_stock_level": 20},
    {"product_code": "WPC-PRF-001", "name": "WPC Profile - Skirting 3inch", "category": "Profiles", "unit": "meters", "available_quantity": 800, "minimum_stock_level": 100},
    {"product_code": "WPC-PRF-002", "name": "WPC Profile - Skirting 4inch", "category": "Profiles", "unit": "meters", "available_quantity": 600, "minimum_stock_level": 100},
    {"product_code": "WPC-PRF-003", "name": "WPC Profile - Louvers", "category": "Profiles", "unit": "meters", "available_quantity": 90, "minimum_stock_level": 100},
    {"product_code": "WPC-PRF-004", "name": "WPC Profile - Fluted Panel Strip", "category": "Profiles", "unit": "meters", "available_quantity": 0, "minimum_stock_level": 50},
    {"product_code": "WPC-FRM-001", "name": "WPC Door Frame - Standard", "category": "Frames", "unit": "pcs", "available_quantity": 35, "minimum_stock_level": 10},
    {"product_code": "WPC-FRM-002", "name": "WPC Window Frame", "category": "Frames", "unit": "pcs", "available_quantity": 22, "minimum_stock_level": 10},
    {"product_code": "WPC-FLR-001", "name": "WPC Flooring Plank - Light Oak", "category": "Flooring", "unit": "sqft", "available_quantity": 1000, "minimum_stock_level": 150},
    {"product_code": "WPC-FLR-002", "name": "WPC Flooring Plank - Dark Walnut", "category": "Flooring", "unit": "sqft", "available_quantity": 250, "minimum_stock_level": 150},
    {"product_code": "WPC-CLD-001", "name": "WPC Wall Cladding - Textured", "category": "Cladding", "unit": "sqft", "available_quantity": 5, "minimum_stock_level": 40},
]


async def seed_users(session):
    for user_data in SAMPLE_USERS:
        existing = await session.execute(select(User).where(User.email == user_data["email"]))
        if existing.scalar_one_or_none():
            print(f"  User already exists, skipping: {user_data['email']}")
            continue

        user = User(
            email=user_data["email"],
            password_hash=hash_password(user_data["password"]),
            name=user_data["name"],
            role=user_data["role"],
        )
        session.add(user)
        print(f"  Created user: {user_data['email']} ({user_data['role'].value}) - password: {user_data['password']}")

    await session.commit()


async def seed_products(session):
    for product_data in SAMPLE_PRODUCTS:
        existing = await session.execute(
            select(Product).where(Product.product_code == product_data["product_code"])
        )
        if existing.scalar_one_or_none():
            print(f"  Product already exists, skipping: {product_data['product_code']}")
            continue

        product = Product(**product_data)
        session.add(product)
        print(f"  Created product: {product_data['product_code']} - {product_data['name']}")

    await session.commit()


async def main():
    async with AsyncSessionLocal() as session:
        print("Seeding users...")
        await seed_users(session)
        print("\nSeeding products...")
        await seed_products(session)
        print("\nSeed complete!")


if __name__ == "__main__":
    asyncio.run(main())