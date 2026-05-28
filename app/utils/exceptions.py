"""全局异常处理"""
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


async def http_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None},
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=400,
        content={"code": 400, "message": "数据冲突（可能已存在）", "data": None},
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "数据库错误", "data": None},
    )


async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": f"服务器内部错误: {str(exc)}", "data": None},
    )

