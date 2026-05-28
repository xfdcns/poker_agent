"""POKER Agent 系统入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.routers import user, table, game, profile
from app.utils.exceptions import (
    http_exception_handler,
    integrity_error_handler,
    sqlalchemy_error_handler,
    general_exception_handler,
)

app = FastAPI(
    title="POKER Agent",
    description="德州扑克AI分析Agent系统",
    version="3.0",
    swagger_ui_parameters={"persistAuthorization": True},
)

# 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 注册路由
app.include_router(user.router)
app.include_router(table.router)
app.include_router(game.router)
app.include_router(profile.router)


@app.get("/")
async def root():
    return {"message": "POKER Agent v3", "status": "running"}
