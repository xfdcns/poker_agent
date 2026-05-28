"""用户路由 /api/user"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.db_conf import get_db
from app.crud.user import create_user, get_user_by_username, verify_password, update_user, change_password, create_token
from app.utils.auth import get_current_user
from app.utils.response import success, fail
from app.schemas.user import RegisterRequest, LoginRequest, UpdateUserRequest, ChangePasswordRequest
from app.models.user import User

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_username(db, req.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = await create_user(db, req.username, req.password)
    token = await create_token(db, user.id)
    return success({
        "token": token,
        "userInfo": {
            "id": user.id, "username": user.username,
            "nickname": user.nickname, "avatar": user.avatar, "bio": user.bio,
        }
    }, message="注册成功")


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_username(db, req.username)
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    token = await create_token(db, user.id)
    return success({
        "token": token,
        "userInfo": {
            "id": user.id, "username": user.username,
            "nickname": user.nickname, "avatar": user.avatar, "bio": user.bio,
        }
    }, message="登录成功")


@router.get("/info")
async def get_info(user: User = Depends(get_current_user)):
    return success({
        "id": user.id, "username": user.username, "nickname": user.nickname,
        "avatar": user.avatar, "gender": user.gender, "bio": user.bio, "phone": user.phone,
    })


@router.put("/update")
async def update_info(req: UpdateUserRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = await update_user(db, user, **req.model_dump(exclude_unset=True))
    return success({
        "id": user.id, "username": user.username, "nickname": user.nickname,
        "avatar": user.avatar, "gender": user.gender, "bio": user.bio, "phone": user.phone,
    }, message="更新成功")


@router.put("/password")
async def update_password(req: ChangePasswordRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not verify_password(req.oldPassword, user.password):
        raise HTTPException(status_code=400, detail="原密码错误")
    await change_password(db, user, req.newPassword)
    return success(message="密码修改成功")
