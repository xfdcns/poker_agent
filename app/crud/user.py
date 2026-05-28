"""用户 CRUD"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from app.models.user import User, UserToken
from datetime import datetime, timedelta
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


async def create_user(db: AsyncSession, username: str, password: str) -> User:
    user = User(username=username, password=hash_password(password))
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_token(db: AsyncSession, token: str):
    result = await db.execute(
        select(UserToken).where(UserToken.token == token)
    )
    token_obj = result.scalar_one_or_none()
    if not token_obj:
        return None
    # 检查过期
    if token_obj.expired_at and token_obj.expired_at < datetime.now():
        return None
    # 通过 token 找到用户
    result2 = await db.execute(select(User).where(User.id == token_obj.user_id))
    return result2.scalar_one_or_none()


async def create_token(db: AsyncSession, user_id: int) -> str:
    token = str(uuid.uuid4())
    expired_at = datetime.now() + timedelta(days=7)
    token_obj = UserToken(user_id=user_id, token=token, expired_at=expired_at)
    db.add(token_obj)
    await db.flush()
    return token


async def update_user(db: AsyncSession, user: User, **kwargs) -> User:
    for key, value in kwargs.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)
    await db.flush()
    await db.refresh(user)
    return user


async def change_password(db: AsyncSession, user: User, new_password: str):
    user.password = hash_password(new_password)
    await db.flush()
