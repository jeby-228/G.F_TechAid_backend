"""
統一回應格式工具
"""
from typing import Any, Dict, Optional, List
from datetime import datetime
from pydantic import BaseModel
from fastapi import status
from fastapi.responses import JSONResponse

class SuccessResponse(BaseModel):
    """成功回應格式"""
    success: bool = True
    message: str
    data: Optional[Any] = None
    timestamp: datetime = datetime.utcnow()

class ErrorResponse(BaseModel):
    """錯誤回應格式"""
    success: bool = False
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()

class ValidationErrorResponse(BaseModel):
    """驗證錯誤回應格式"""
    success: bool = False
    error_code: str = "VALIDATION_ERROR"
    message: str = "輸入資料驗證失敗"
    field_errors: List[Dict[str, Any]]
    timestamp: datetime = datetime.utcnow()

def create_success_response(
    message: str,
    data: Optional[Any] = None,
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """建立成功回應"""
    response_data = SuccessResponse(message=message, data=data)
    return JSONResponse(
        status_code=status_code,
        content=response_data.model_dump()
    )

def create_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> JSONResponse:
    """建立錯誤回應"""
    response_data = ErrorResponse(
        error_code=error_code,
        message=message,
        details=details
    )
    return JSONResponse(
        status_code=status_code,
        content=response_data.model_dump()
    )

def create_validation_error_response(
    field_errors: List[Dict[str, Any]],
    status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY
) -> JSONResponse:
    """建立驗證錯誤回應"""
    response_data = ValidationErrorResponse(field_errors=field_errors)
    return JSONResponse(
        status_code=status_code,
        content=response_data.model_dump()
    )