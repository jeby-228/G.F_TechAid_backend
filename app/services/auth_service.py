"""
身分驗證服務
"""
from typing import Optional, Dict, Any
from datetime import timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.crud.user import user_crud
from app.schemas.auth import UserRegistration, UserLogin, Token, UserProfile
from app.core.security import create_access_token, verify_token
from app.core.config import settings
from app.utils.constants import UserRole, ROLE_PERMISSIONS


class AuthService:
    """身分驗證服務類"""
    
    def register_user(self, db: Session, user_data: UserRegistration) -> Dict[str, Any]:
        """用戶註冊"""
        try:
            # 建立用戶
            user = user_crud.create_user(db, user_data)
            
            # 生成 JWT token
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                subject=str(user.id),
                expires_delta=access_token_expires
            )
            
            return {
                "user": self._user_to_profile(user),
                "token": Token(
                    access_token=access_token,
                    token_type="bearer",
                    expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
                ),
                "message": self._get_registration_message(user_data.role)
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="註冊過程中發生錯誤"
            )
    
    def login_user(self, db: Session, login_data: UserLogin) -> Dict[str, Any]:
        """用戶登入"""
        # 驗證用戶憑證
        user = user_crud.authenticate_user(db, login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="電子郵件或密碼錯誤",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 檢查用戶是否已審核通過
        if not user.is_approved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="帳號尚未通過審核，請等待管理員審核"
            )
        
        # 生成 JWT token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=str(user.id),
            expires_delta=access_token_expires
        )
        
        return {
            "user": self._user_to_profile(user),
            "token": Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
        }
    
    def get_current_user(self, db: Session, user_id: str) -> UserProfile:
        """取得當前用戶資訊"""
        user = user_crud.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )
        
        if not user.is_approved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="帳號尚未通過審核"
            )
        
        return self._user_to_profile(user)
    
    def verify_user_token(self, token: str) -> Optional[str]:
        """驗證用戶 token"""
        return verify_token(token)
    
    def check_permission(self, user_role: UserRole, permission: str) -> bool:
        """檢查用戶權限"""
        role_permissions = ROLE_PERMISSIONS.get(user_role, {})
        
        # 管理員擁有所有權限
        if role_permissions.get("all"):
            return True
        
        return role_permissions.get(permission, False)
    
    def get_user_permissions(self, user_role: UserRole) -> Dict[str, Any]:
        """取得用戶權限列表"""
        return ROLE_PERMISSIONS.get(user_role, {})
    
    def _user_to_profile(self, user) -> UserProfile:
        """將用戶模型轉換為用戶資料模型"""
        return UserProfile(
            id=str(user.id),
            email=user.email,
            phone=user.phone,
            name=user.name,
            role=UserRole(user.role),
            is_approved=user.is_approved,
            created_at=user.created_at.isoformat() if user.created_at else ""
        )
    
    def _get_registration_message(self, role: UserRole) -> str:
        """取得註冊成功訊息"""
        if role == UserRole.UNOFFICIAL_ORG:
            return "註冊成功！您的組織資訊已提交審核，請等待管理員審核通過後即可發布任務。"
        elif role in [UserRole.OFFICIAL_ORG, UserRole.SUPPLY_MANAGER]:
            return "註冊成功！您已可以開始使用平台功能。"
        else:
            return "註冊成功！歡迎使用光復e互助平台。"


# 建立全域實例
auth_service = AuthService()