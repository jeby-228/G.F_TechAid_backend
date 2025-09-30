"""
API 依賴項
"""
from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.utils.constants import UserRole


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求管理員權限的依賴項"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理員權限"
        )
    return current_user


def require_roles(*allowed_roles: UserRole):
    """要求特定角色權限的依賴項工廠"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in [role.value for role in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一：{', '.join([role.value for role in allowed_roles])}"
            )
        return current_user
    return role_checker


# 重新匯出常用依賴項
__all__ = ["get_db", "get_current_user", "require_admin", "require_roles"]