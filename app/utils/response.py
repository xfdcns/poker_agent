"""统一响应格式"""
from typing import Optional, Any


def success(data: Any = None, message: str = "success", code: int = 200) -> dict:
    return {"code": code, "message": message, "data": data}


def fail(message: str = "error", code: int = 400, data: Any = None) -> dict:
    return {"code": code, "message": message, "data": data}
