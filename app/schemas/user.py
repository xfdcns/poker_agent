from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


# ============ 请求 ============

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class UpdateUserRequest(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    oldPassword: str
    newPassword: str


# ============ 响应 ============

class UserInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None

class LoginResponse(BaseModel):
    token: str
    userInfo: UserInfoResponse
