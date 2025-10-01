"""
組織審核服務
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.user import user_crud
from app.schemas.user import OrganizationApprovalRequest
from app.services.notification_service import notification_service
from app.utils.constants import UserRole, NotificationType
from app.models.user import Organization
from datetime import datetime


class OrganizationService:
    """組織審核服務類"""
    
    async def submit_organization_for_approval(
        self,
        db: Session,
        user_id: str,
        organization_data: dict
    ) -> Organization:
        """提交組織申請審核"""
        # 檢查用戶是否為非正式組織
        user = user_crud.get_by_id(db, user_id)
        if not user or user.role != UserRole.UNOFFICIAL_ORG.value:
            raise ValueError("只有非正式組織可以提交審核申請")
        
        # 檢查是否已有組織申請
        existing_org = user_crud.get_organization_by_user_id(db, user_id)
        if existing_org:
            if existing_org.approval_status == "pending":
                raise ValueError("已有待審核的組織申請")
            elif existing_org.approval_status == "approved":
                raise ValueError("組織已通過審核")
        
        # 建立組織申請
        from app.schemas.user import OrganizationCreate
        org_create = OrganizationCreate(
            user_id=user_id,
            **organization_data
        )
        
        organization = user_crud.create_organization(db, org_create)
        
        # 發送通知給管理員
        await self._notify_admins_new_application(db, organization)
        
        # 發送確認通知給申請者
        await notification_service.send_notification(
            db=db,
            user_id=user_id,
            title="組織申請已提交",
            message="您的組織申請已成功提交，請等待管理員審核。",
            notification_type=NotificationType.SYSTEM,
            related_id=str(organization.id)
        )
        
        return organization
    
    async def approve_organization(
        self,
        db: Session,
        organization_id: str,
        approver_id: str,
        approval_data: OrganizationApprovalRequest
    ) -> Organization:
        """審核組織申請"""
        # 檢查審核者權限
        approver = user_crud.get_by_id(db, approver_id)
        if not approver or approver.role != UserRole.ADMIN.value:
            raise ValueError("只有管理員可以審核組織申請")
        
        # 審核組織
        organization = user_crud.approve_organization(
            db, organization_id, approver_id, approval_data.approved
        )
        
        if not organization:
            raise ValueError("組織不存在")
        
        # 發送審核結果通知
        await notification_service.send_organization_approval_notification(
            db, str(organization.user_id), approval_data.approved, approval_data.notes
        )
        
        # 如果審核通過，發送歡迎通知
        if approval_data.approved:
            await self._send_welcome_notification(db, organization)
        
        return organization
    
    async def get_pending_applications(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Organization]:
        """取得待審核的組織申請"""
        return user_crud.get_pending_organizations(db, skip, limit)
    
    async def get_organization_statistics(self, db: Session) -> dict:
        """取得組織統計資料"""
        from sqlalchemy import func
        
        # 總組織數
        total_orgs = db.query(func.count(Organization.id)).scalar()
        
        # 各狀態組織數
        status_counts = db.query(
            Organization.approval_status,
            func.count(Organization.id)
        ).group_by(Organization.approval_status).all()
        
        status_dict = {status: count for status, count in status_counts}
        
        # 各類型組織數
        type_counts = db.query(
            Organization.organization_type,
            func.count(Organization.id)
        ).group_by(Organization.organization_type).all()
        
        type_dict = {org_type: count for org_type, count in type_counts}
        
        return {
            "total_organizations": total_orgs,
            "by_status": status_dict,
            "by_type": type_dict,
            "pending_count": status_dict.get("pending", 0),
            "approved_count": status_dict.get("approved", 0),
            "rejected_count": status_dict.get("rejected", 0)
        }
    
    async def resubmit_organization(
        self,
        db: Session,
        organization_id: str,
        user_id: str,
        updated_data: dict
    ) -> Organization:
        """重新提交組織申請（被拒絕後）"""
        organization = user_crud.get_organization_by_id(db, organization_id)
        
        if not organization:
            raise ValueError("組織不存在")
        
        if str(organization.user_id) != user_id:
            raise ValueError("無權限修改此組織")
        
        if organization.approval_status != "rejected":
            raise ValueError("只有被拒絕的申請可以重新提交")
        
        # 更新組織資料並重設審核狀態
        from app.schemas.user import OrganizationUpdate
        update_data = OrganizationUpdate(**updated_data)
        
        updated_org = user_crud.update_organization(db, organization_id, update_data)
        
        # 重設審核狀態
        updated_org.approval_status = "pending"
        updated_org.approved_by = None
        updated_org.approved_at = None
        updated_org.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(updated_org)
        
        # 發送重新提交通知給管理員
        await self._notify_admins_resubmission(db, updated_org)
        
        # 發送確認通知給申請者
        await notification_service.send_notification(
            db=db,
            user_id=user_id,
            title="組織申請已重新提交",
            message="您的組織申請已重新提交，請等待管理員審核。",
            notification_type=NotificationType.SYSTEM,
            related_id=str(updated_org.id)
        )
        
        return updated_org
    
    async def _notify_admins_new_application(self, db: Session, organization: Organization):
        """通知管理員有新的組織申請"""
        # 取得所有管理員
        admins = user_crud.get_users_by_role(db, UserRole.ADMIN)
        
        for admin in admins:
            await notification_service.send_notification(
                db=db,
                user_id=str(admin.id),
                title="新的組織申請",
                message=f"組織「{organization.organization_name}」提交了審核申請，請及時處理。",
                notification_type=NotificationType.SYSTEM,
                related_id=str(organization.id)
            )
    
    async def _notify_admins_resubmission(self, db: Session, organization: Organization):
        """通知管理員有組織重新提交申請"""
        # 取得所有管理員
        admins = user_crud.get_users_by_role(db, UserRole.ADMIN)
        
        for admin in admins:
            await notification_service.send_notification(
                db=db,
                user_id=str(admin.id),
                title="組織申請重新提交",
                message=f"組織「{organization.organization_name}」重新提交了審核申請，請及時處理。",
                notification_type=NotificationType.SYSTEM,
                related_id=str(organization.id)
            )
    
    async def _send_welcome_notification(self, db: Session, organization: Organization):
        """發送歡迎通知給通過審核的組織"""
        await notification_service.send_notification(
            db=db,
            user_id=str(organization.user_id),
            title="歡迎加入光復e互助平台",
            message=f"恭喜！組織「{organization.organization_name}」已通過審核。您現在可以發布任務並參與救災工作。",
            notification_type=NotificationType.SYSTEM,
            related_id=str(organization.id)
        )


# 建立全域實例
organization_service = OrganizationService()