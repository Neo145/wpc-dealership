"""
Pydantic schemas for authentication.

LoginRequest: what the client must send to /auth/login.
TokenResponse: what we send back - the JWT plus basic user info so the
frontend can immediately show "Welcome, {name}" without a second call.
"""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserInfo(BaseModel):
    id: str
    email: str
    name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo