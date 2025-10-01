"""
用戶相關的 CRUD 操作
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from app.models.user import User, UserRole as UserRoleModel, Organization
from app.schemas.auth import UserRegistration, UserProfileUpdate
from app.schemas.user import (
    UserCreate, UserUpdate, UserSearchQuery, UserStatistics,
    OrganizationCreate, OrganizationUpdate, OrganizationSearchQuery
)
from app.core.security import get_password_hash, verify_password
from app.utils.constants import UserRole
from datetime import datetime


class UserCRUD:
    """用戶 CRUD 操作類"""
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """根據電子郵件取得用戶"""
        return db.query(User).filter(User.email == email).first()
    
    def get_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """根據 ID 取得用戶"""
        import uuid
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            return db.query(User).filter(User.id == user_uuid).first()
        except (ValueError, TypeError):
            return None
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search_query: Optional[UserSearchQuery] = None
    ) -> List[User]:
        """取得用戶列表（支援搜尋和篩選）"""
        query = db.query(User)
        
        if search_query:
            if search_query.email:
                query = query.filter(User.email.ilike(f"%{search_query.email}%"))
            if search_query.name:
                query = query.filter(User.name.ilike(f"%{search_query.name}%"))
            if search_query.role:
                query = query.filter(User.role == search_query.role.value)
            if search_query.is_approved is not None:
                query = query.filter(User.is_approved == search_query.is_approved)
        
        return query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
    
    def count(self, db: Session, search_query: Optional[UserSearchQuery] = None) -> int:
        """計算用戶總數（支援搜尋和篩選）"""
        query = db.query(func.count(User.id))
        
        if search_query:
            if search_query.email:
                query = query.filter(User.email.ilike(f"%{search_query.email}%"))
            if search_query.name:
                query = query.filter(User.name.ilike(f"%{search_query.name}%"))
            if search_query.role:
                query = query.filter(User.role == search_query.role.value)
            if search_query.is_approved is not None:
                query = query.filter(User.is_approved == search_query.is_approved)
        
        return query.scalar()
    
    def create(self, db: Session, user_data: UserCreate) -> User:
        """建立新用戶（通用方法）"""
        # 檢查電子郵件是否已存在
        if self.get_by_email(db, user_data.email):
            raise ValueError("電子郵件已被使用")
        
        # 建立用戶
        db_user = User(
            email=user_data.email,
            phone=user_data.phone,
            name=user_data.name,
            password_hash=get_password_hash(user_data.password),
            role=user_data.role.value,
            is_approved=self._should_auto_approve(user_data.role),
            profile_data=user_data.profile_data
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def create_user(self, db: Session, user_data: UserRegistration) -> User:
        """建立新用戶"""
        # 檢查電子郵件是否已存在
        if self.get_by_email(db, user_data.email):
            raise ValueError("電子郵件已被使用")
        
        # 建立用戶
        db_user = User(
            email=user_data.email,
            phone=user_data.phone,
            name=user_data.name,
            password_hash=get_password_hash(user_data.password),
            role=user_data.role.value,
            is_approved=self._should_auto_approve(user_data.role)
        )
        
        db.add(db_user)
        db.flush()  # 取得用戶 ID
        
        # 如果是組織負責人，建立組織資訊
        if user_data.role in [UserRole.OFFICIAL_ORG, UserRole.UNOFFICIAL_ORG]:
            organization = Organization(
                user_id=db_user.id,
                organization_name=user_data.organization_name,
                organization_type=user_data.organization_type or user_data.role.value.replace('_org', ''),
                contact_person=user_data.contact_person,
                contact_phone=user_data.contact_phone,
                address=user_data.address,
                description=user_data.description,
                approval_status="approved" if user_data.role == UserRole.OFFICIAL_ORG else "pending"
            )
            db.add(organization)
        
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """驗證用戶登入"""
        user = self.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
    
    def update(self, db: Session, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """更新用戶資料（通用方法）"""
        user = self.get_by_id(db, user_id)
        if not user:
            return None
        
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user
    
    def update_profile(self, db: Session, user_id: str, profile_data: UserProfileUpdate) -> Optional[User]:
        """更新用戶個人資料"""
        user = self.get_by_id(db, user_id)
        if not user:
            return None
        
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user
    
    def delete(self, db: Session, user_id: str) -> bool:
        """刪除用戶"""
        user = self.get_by_id(db, user_id)
        if not user:
            return False
        
        db.delete(user)
        db.commit()
        return True
    
    def update_role(self, db: Session, user_id: str, new_role: UserRole) -> Optional[User]:
        """更新用戶角色（管理員專用）"""
        user = self.get_by_id(db, user_id)
        if not user:
            return None
        
        user.role = new_role.value
        user.is_approved = self._should_auto_approve(new_role)
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        return user
    
    def update_approval_status(self, db: Session, user_id: str, is_approved: bool) -> Optional[User]:
        """更新用戶審核狀態（管理員專用）"""
        user = self.get_by_id(db, user_id)
        if not user:
            return None
        
        user.is_approved = is_approved
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        return user
    
    def reset_password(self, db: Session, user_id: str, new_password: str) -> bool:
        """重設用戶密碼（管理員專用）"""
        user = self.get_by_id(db, user_id)
        if not user:
            return False
        
        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        
        db.commit()
        return True
    
    def change_password(self, db: Session, user_id: str, current_password: str, new_password: str) -> bool:
        """變更用戶密碼"""
        user = self.get_by_id(db, user_id)
        if not user:
            return False
        
        if not verify_password(current_password, user.password_hash):
            return False
        
        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        db.commit()
        return True
    
    def get_users_by_role(self, db: Session, role: UserRole, skip: int = 0, limit: int = 100) -> List[User]:
        """根據角色取得用戶列表"""
        return db.query(User).filter(User.role == role.value).offset(skip).limit(limit).all()
    
    def get_statistics(self, db: Session) -> UserStatistics:
        """取得用戶統計資料"""
        # 總用戶數
        total_users = db.query(func.count(User.id)).scalar()
        
        # 各角色用戶數
        role_counts = db.query(
            User.role, 
            func.count(User.id)
        ).group_by(User.role).all()
        users_by_role = {role: count for role, count in role_counts}
        
        # 已審核用戶數
        approved_users = db.query(func.count(User.id)).filter(User.is_approved == True).scalar()
        
        # 待審核用戶數
        pending_approvals = db.query(func.count(User.id)).filter(User.is_approved == False).scalar()
        
        # 活躍組織數
        active_organizations = db.query(func.count(Organization.id)).filter(
            Organization.approval_status == "approved"
        ).scalar()
        
        # 待審核組織數
        pending_organizations = db.query(func.count(Organization.id)).filter(
            Organization.approval_status == "pending"
        ).scalar()
        
        return UserStatistics(
            total_users=total_users,
            users_by_role=users_by_role,
            approved_users=approved_users,
            pending_approvals=pending_approvals,
            active_organizations=active_organizations,
            pending_organizations=pending_organizations
        )
    
    # 組織相關方法
    def create_organization(self, db: Session, org_data: OrganizationCreate) -> Organization:
        """建立組織"""
        # 檢查用戶是否存在
        user = self.get_by_id(db, org_data.user_id)
        if not user:
            raise ValueError("用戶不存在")
        
        # 檢查用戶是否已有組織
        existing_org = db.query(Organization).filter(Organization.user_id == org_data.user_id).first()
        if existing_org:
            raise ValueError("用戶已有組織資訊")
        
        # 建立組織
        db_org = Organization(
            user_id=org_data.user_id,
            organization_name=org_data.organization_name,
            organization_type=org_data.organization_type,
            contact_person=org_data.contact_person,
            contact_phone=org_data.contact_phone,
            address=org_data.address,
            description=org_data.description,
            approval_status="approved" if org_data.organization_type == "official" else "pending"
        )
        
        db.add(db_org)
        db.commit()
        db.refresh(db_org)
        return db_org
    
    def get_organization_by_id(self, db: Session, org_id: str) -> Optional[Organization]:
        """根據 ID 取得組織"""
        return db.query(Organization).filter(Organization.id == org_id).first()
    
    def get_organization_by_user_id(self, db: Session, user_id: str) -> Optional[Organization]:
        """根據用戶 ID 取得組織"""
        return db.query(Organization).filter(Organization.user_id == user_id).first()
    
    def get_organizations(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search_query: Optional[OrganizationSearchQuery] = None
    ) -> List[Organization]:
        """取得組織列表（支援搜尋和篩選）"""
        query = db.query(Organization).options(
            joinedload(Organization.user),
            joinedload(Organization.approver)
        )
        
        if search_query:
            if search_query.organization_name:
                query = query.filter(
                    Organization.organization_name.ilike(f"%{search_query.organization_name}%")
                )
            if search_query.organization_type:
                query = query.filter(Organization.organization_type == search_query.organization_type)
            if search_query.approval_status:
                query = query.filter(Organization.approval_status == search_query.approval_status)
        
        return query.order_by(desc(Organization.created_at)).offset(skip).limit(limit).all()
    
    def count_organizations(
        self, 
        db: Session, 
        search_query: Optional[OrganizationSearchQuery] = None
    ) -> int:
        """計算組織總數（支援搜尋和篩選）"""
        query = db.query(func.count(Organization.id))
        
        if search_query:
            if search_query.organization_name:
                query = query.filter(
                    Organization.organization_name.ilike(f"%{search_query.organization_name}%")
                )
            if search_query.organization_type:
                query = query.filter(Organization.organization_type == search_query.organization_type)
            if search_query.approval_status:
                query = query.filter(Organization.approval_status == search_query.approval_status)
        
        return query.scalar()
    
    def get_pending_organizations(self, db: Session, skip: int = 0, limit: int = 100) -> List[Organization]:
        """取得待審核的組織列表"""
        return db.query(Organization).options(
            joinedload(Organization.user)
        ).filter(
            Organization.approval_status == "pending"
        ).order_by(desc(Organization.created_at)).offset(skip).limit(limit).all()
    
    def update_organization(self, db: Session, org_id: str, org_data: OrganizationUpdate) -> Optional[Organization]:
        """更新組織資料"""
        organization = self.get_organization_by_id(db, org_id)
        if not organization:
            return None
        
        update_data = org_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(organization, field, value)
        
        organization.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(organization)
        return organization
    
    def approve_organization(self, db: Session, organization_id: str, approved_by: str, approved: bool = True) -> Optional[Organization]:
        """審核組織"""
        organization = db.query(Organization).filter(Organization.id == organization_id).first()
        if not organization:
            return None
        
        organization.approval_status = "approved" if approved else "rejected"
        organization.approved_by = approved_by
        organization.approved_at = datetime.utcnow()
        
        # 如果通過審核，更新用戶的 is_approved 狀態
        if approved:
            user = self.get_by_id(db, str(organization.user_id))
            if user:
                user.is_approved = True
                user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(organization)
        return organization
    
    def delete_organization(self, db: Session, org_id: str) -> bool:
        """刪除組織"""
        organization = self.get_organization_by_id(db, org_id)
        if not organization:
            return False
        
        db.delete(organization)
        db.commit()
        return True
    
    def _should_auto_approve(self, role: UserRole) -> bool:
        """判斷是否應該自動審核通過"""
        # 非正式組織需要管理員審核，其他角色自動通過
        return role != UserRole.UNOFFICIAL_ORG


# 建立全域實例
user_crud = UserCRUD()