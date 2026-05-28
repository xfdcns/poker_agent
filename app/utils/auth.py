"""认证依赖"""
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.config.db_conf import get_db
from app.crud.user import get_user_by_token

# 用 APIKeyHeader 让 Swagger 显示 🔒 按钮
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


async def get_current_user(
    authorization: Optional[str] = Depends(api_key_header),
    db: AsyncSession = Depends(get_db),
):
    """从 token 获取当前用户，未登录抛 401"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未登录")
    user = await get_user_by_token(db, authorization)
    if not user:
        raise HTTPException(status_code=401, detail="登录已过期")
    return user
