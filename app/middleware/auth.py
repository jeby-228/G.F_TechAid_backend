"""
身分驗證和權限控制中介軟體
"""
from typing import List, Optional, Callable, Any
from functools import wraps
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import auth_service
from app.utils.constants import UserRole


# HTTP Bearer token 驗證
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """從 JWT token 取得當前用戶 ID"""
    token = credentials.credentials
    user_id = auth_service.verify_user_token(token)
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的身分驗證憑證",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取得當前用戶完整資訊"""
    return auth_service.get_current_user(db, user_id)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """可選的用戶身分驗證（允許匿名訪問）"""
    if credentials is None:
        return None
    
    token = credentials.credentials
    return auth_service.verify_user_token(token)


def require_roles(allowed_roles: List[UserRole]):
    """
    角色權限裝飾器
    
    Args:
        allowed_roles: 允許的用戶角色列表
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 從 kwargs 中取得當前用戶
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要身分驗證"
                )
            
            # 檢查用戶角色
            user_role = UserRole(current_user.role)
            if user_role not in allowed_roles and user_role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="權限不足"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(permission: str):
    """
    權限檢查裝飾器
    
    Args:
        permission: 需要的權限名稱
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 從 kwargs 中取得當前用戶
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要身分驗證"
                )
            
            # 檢查用戶權限
            user_role = UserRole(current_user.role)
            if not auth_service.check_permission(user_role, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少必要權限: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class RoleChecker:
    """角色檢查器類"""
    
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user = Depends(get_current_user)):
        user_role = UserRole(current_user.role)
        if user_role not in self.allowed_roles and user_role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="權限不足"
            )
        return current_user


class PermissionChecker:
    """權限檢查器類"""
    
    def __init__(self, required_permission: str):
        self.required_permission = required_permission
    
    def __call__(self, current_user = Depends(get_current_user)):
        user_role = UserRole(current_user.role)
        if not auth_service.check_permission(user_role, self.required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少必要權限: {self.required_permission}"
            )
        return current_user


# 常用的權限檢查器實例
AdminOnly = RoleChecker([UserRole.ADMIN])
VictimOnly = RoleChecker([UserRole.VICTIM])
OfficialOrgOnly = RoleChecker([UserRole.OFFICIAL_ORG])
SupplyManagerOnly = RoleChecker([UserRole.SUPPLY_MANAGER])
VolunteerAndAbove = RoleChecker([UserRole.VOLUNTEER, UserRole.OFFICIAL_ORG, UserRole.UNOFFICIAL_ORG, UserRole.SUPPLY_MANAGER])

# 常用的功能權限檢查器
CanCreateTask = PermissionChecker("create_task")
CanClaimTask = PermissionChecker("claim_task")
CanManageSupplies = PermissionChecker("manage_supplies")
CanCreateNeed = PermissionChecker("create_need")