"""
需求管理服務
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.crud.need import need_crud
from app.schemas.need import NeedStatusUpdate, NeedAssignment as NeedAssignmentSchema
from app.models.need import Need
from app.utils.constants import NeedStatus, UserRole
from app.services.notification_service import notification_service
from datetime import datetime


class NeedService:
    """需求管理服務類"""
    
    async def update_need_status(
        self, 
        db: Session, 
        need_id: str, 
        status_data: NeedStatusUpdate,
        current_user_id: str
    ) -> Optional[Need]:
        """更新需求狀態"""
        need = need_crud.update_status(db, need_id, status_data)
        if not need:
            return None
        
        # 發送狀態更新通知
        await notification_service.send_need_status_update_notification(
            db, need_id, status_data.status.value, status_data.notes
        )
        
        return need
    
    async def assign_need_to_volunteer(
        self, 
        db: Session, 
        need_id: str, 
        assignment_data: NeedAssignmentSchema,
        assigner_id: str
    ) -> Optional[Need]:
        """分配需求給志工"""
        need = need_crud.assign_to_user(db, need_id, assignment_data)
        if not need:
            return None
        
        # 發送分配通知給志工
        await notification_service.send_need_assignment_notification(
            db, need_id, assignment_data.assigned_to
        )
        
        # 發送分配確認通知給分配者
        await notification_service.send_notification(
            db,
            user_id=assigner_id,
            title="需求分配成功",
            message=f"需求「{need.title}」已成功分配給志工",
            notification_type="need_assignment"
        )
        
        return need
    
    async def complete_need(
        self, 
        db: Session, 
        need_id: str, 
        completion_notes: Optional[str] = None
    ) -> Optional[Need]:
        """完成需求"""
        status_data = NeedStatusUpdate(
            status=NeedStatus.RESOLVED,
            notes=completion_notes or "需求已完成"
        )
        
        need = need_crud.update_status(db, need_id, status_data)
        if not need:
            return None
        
        # 發送完成通知給報告者
        await notification_service.send_notification(
            db,
            user_id=str(need.reporter_id),
            title="需求已完成",
            message=f"您的需求「{need.title}」已經完成處理",
            notification_type="need_completion"
        )
        
        # 如果有負責人，也發送通知
        if need.assigned_to:
            await notification_service.send_notification(
                db,
                user_id=str(need.assigned_to),
                title="需求處理完成",
                message=f"您負責的需求「{need.title}」已標記為完成",
                notification_type="need_completion"
            )
        
        return need
    
    def can_user_manage_need(self, user_role: UserRole, need: Need, user_id: str) -> bool:
        """檢查用戶是否可以管理需求"""
        # 管理員可以管理所有需求
        if user_role == UserRole.ADMIN:
            return True
        
        # 正式組織可以管理所有需求
        if user_role == UserRole.OFFICIAL_ORG:
            return True
        
        # 物資站點管理者可以管理相關需求
        if user_role == UserRole.SUPPLY_MANAGER:
            return True
        
        # 需求報告者可以管理自己的需求
        if str(need.reporter_id) == user_id:
            return True
        
        # 需求負責人可以管理分配給自己的需求
        if need.assigned_to and str(need.assigned_to) == user_id:
            return True
        
        return False
    
    def can_user_assign_need(self, user_role: UserRole) -> bool:
        """檢查用戶是否可以分配需求"""
        return user_role in [UserRole.ADMIN, UserRole.OFFICIAL_ORG]
    
    def get_available_needs_for_user(
        self, 
        db: Session, 
        user_role: UserRole, 
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Need]:
        """根據用戶角色取得可用的需求列表"""
        if user_role == UserRole.VICTIM:
            # 受災戶只能看到自己的需求
            return need_crud.get_by_reporter(db, user_id, skip=skip, limit=limit)
        elif user_role == UserRole.VOLUNTEER:
            # 一般志工可以看到待處理的需求和分配給自己的需求
            open_needs = need_crud.get_open_needs(db, skip=skip, limit=limit//2)
            assigned_needs = need_crud.get_by_assignee(db, user_id, skip=0, limit=limit//2)
            return open_needs + assigned_needs
        else:
            # 管理員、正式組織、物資管理者可以看到所有需求
            return need_crud.get_multi(db, skip=skip, limit=limit)
    
    async def auto_assign_urgent_needs(self, db: Session) -> List[Need]:
        """自動分配緊急需求（系統定期任務）"""
        urgent_needs = need_crud.get_urgent_needs(db, urgency_threshold=5)
        assigned_needs = []
        
        for need in urgent_needs:
            if need.status == NeedStatus.OPEN.value:
                # 這裡可以實作自動分配邏輯
                # 例如根據地理位置找到最近的志工組織
                # 暫時跳過自動分配，只記錄緊急需求
                await notification_service.send_notification(
                    db,
                    user_id="system",  # 系統通知
                    title="緊急需求待處理",
                    message=f"緊急需求「{need.title}」需要立即處理",
                    notification_type="urgent_need"
                )
        
        return assigned_needs


# 建立全域實例
need_service = NeedService()