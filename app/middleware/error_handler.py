"""
全域錯誤處理中介軟體
"""
import logging
from typing import Union
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.exceptions import DisasterReliefException
from app.utils.response import create_error_response

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """全域錯誤處理中介軟體"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except DisasterReliefException as exc:
            # 處理自定義例外
            logger.warning(f"Business exception: {exc.error_code} - {exc.message}")
            return create_error_response(
                error_code=exc.error_code,
                message=exc.message,
                details=exc.details,
                status_code=self._get_status_code_for_error(exc.error_code)
            )
        except HTTPException as exc:
            # 處理 FastAPI HTTP 例外
            logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "success": False,
                    "error_code": "HTTP_ERROR",
                    "message": exc.detail,
                    "timestamp": "2024-01-01T00:00:00"
                }
            )
        except Exception as exc:
            # 處理未預期的例外
            logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
            return create_error_response(
                error_code="INTERNAL_SERVER_ERROR",
                message="伺服器內部錯誤",
                status_code=500
            )
    
    def _get_status_code_for_error(self, error_code: str) -> int:
        """根據錯誤代碼取得對應的 HTTP 狀態碼"""
        status_map = {
            "VALIDATION_ERROR": 400,
            "AUTHENTICATION_ERROR": 401,
            "PERMISSION_ERROR": 403,
            "RESOURCE_NOT_FOUND": 404,
            "CONFLICT_ERROR": 409,
            "GENERAL_ERROR": 400,
        }
        return status_map.get(error_code, 500)