from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    user_id: str
    username: str
    full_name: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str

class RoleCreate(BaseModel):
    role_name: str
    description: Optional[str] = None
