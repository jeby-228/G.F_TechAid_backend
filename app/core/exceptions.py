"""
自定義例外類別
"""
from typing import Any, Dict, Optional

class DisasterReliefException(Exception):
    """基礎例外類別"""
    def __init__(
        self,
        message: str,
        error_code: str = "GENERAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(DisasterReliefException):
    """資料驗證錯誤"""
    def __init__(self, field: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"驗證錯誤: {field} - {message}",
            error_code="VALIDATION_ERROR",
            details={"field": field, **(details or {})}
        )

class AuthenticationError(DisasterReliefException):
    """身分驗證錯誤"""
    def __init__(self, message: str = "身分驗證失敗"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR"
        )

class PermissionError(DisasterReliefException):
    """權限不足錯誤"""
    def __init__(self, message: str = "權限不足"):
        super().__init__(
            message=message,
            error_code="PERMISSION_ERROR"
        )

class ResourceNotFoundError(DisasterReliefException):
    """資源不存在錯誤"""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} 不存在: {resource_id}",
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )

class ConflictError(DisasterReliefException):
    """資源衝突錯誤"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFLICT_ERROR",
            details=details
        )