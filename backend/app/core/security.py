"""
Password hashing utilities.

We use bcrypt (via passlib) to hash passwords. Bcrypt automatically
handles salting, so two users with the same password get different
hashes - this protects against rainbow table attacks.
"""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ---- JWT token handling ----

from datetime import datetime, timedelta, timezone
from jose import jwt

from app.core.config import settings


def create_access_token(subject: str, role: str) -> str:
    """
    Creates a signed JWT containing the user's id (as 'sub') and role.
    The frontend will send this back in the Authorization header on
    every request; we verify and decode it to know who's making the call.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decodes and verifies a JWT. Raises jose.JWTError if the token is
    invalid, tampered with, or expired.
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])