"""
任務管理服務
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.crud.task import task_crud
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse,
    TaskSearchQuery, TaskApprovalRequest, TaskClaimCreate,
    TaskClaimResponse, TaskClaimListResponse, TaskStatistics
)
from app.models.task import Task, TaskClaim
from app.utils.constants import UserRole, TaskStatus
from app.services.notification_service import notification_service


class TaskService:
    """任務管理服務類"""
    
    def create_task(
        self, 
        db: Session, 
        task_data: TaskCreate, 
        creator_id: str,
        creator_role: UserRole
    ) -> TaskResponse:
        """建立新任務"""
        # 權限檢查
        if creator_role == UserRole.VICTIM:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="受災戶無法建立任務，請發布需求"
            )
        
        if creator_role == UserRole.VOLUNTEER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="一般志工無法建立任務"
            )
        
        # 建立任務
        task = task_crud.create_task(db, task_data, creator_id, creator_role)
        
        # 如果是非正式組織，發送審核通知
        if creator_role == UserRole.UNOFFICIAL_ORG:
            # TODO: 實作通知服務
            pass
        
        return self._convert_to_response(task, creator_id, creator_role)
    
    def get_task(
        self, 
        db: Session, 
        task_id: str,
        user_id: str,
        user_role: UserRole
    ) -> Optional[TaskResponse]:
        """獲取單一任務"""
        task = task_crud.get_task(db, task_id)
        if not task:
            return None
        
        # 權限檢查
        if not self._can_view_task(task, user_id, user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限查看此任務"
            )
        
        return self._convert_to_response(task, user_id, user_role)
    
    def get_tasks(
        self, 
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search_query: Optional[TaskSearchQuery] = None,
        user_id: str = None,
        user_role: UserRole = None
    ) -> TaskListResponse:
        """獲取任務列表"""
        tasks, total = task_crud.get_tasks(
            db, skip, limit, search_query, user_role, user_id
        )
        
        task_responses = [
            self._convert_to_response(task, user_id, user_role) 
            for task in tasks
        ]
        
        return TaskListResponse(
            tasks=task_responses,
            total=total,
            skip=skip,
            limit=limit
        )
    
    def update_task(
        self, 
        db: Session, 
        task_id: str, 
        task_update: TaskUpdate,
        user_id: str,
        user_role: UserRole
    ) -> Optional[TaskResponse]:
        """更新任務"""
        task = task_crud.update_task(db, task_id, task_update, user_id, user_role)
        if not task:
            return None
        
        return self._convert_to_response(task, user_id, user_role)
    
    def delete_task(
        self, 
        db: Session, 
        task_id: str,
        user_id: str,
        user_role: UserRole
    ) -> bool:
        """刪除任務"""
        return task_crud.delete_task(db, task_id, user_id, user_role)
    
    def approve_task(
        self, 
        db: Session, 
        task_id: str, 
        approval_request: TaskApprovalRequest,
        approver_id: str
    ) -> Optional[TaskResponse]:
        """審核任務"""
        task = task_crud.approve_task(
            db, task_id, approval_request.approved, approver_id, approval_request.notes
        )
        if not task:
            return None
        
        # 發送審核結果通知
        # TODO: 實作通知服務
        pass
        
        return self._convert_to_response(task, approver_id, UserRole.ADMIN)
    
    def claim_task(
        self, 
        db: Session, 
        claim_data: TaskClaimCreate,
        user_id: str,
        user_role: UserRole
    ) -> TaskClaimResponse:
        """認領任務"""
        # 權限檢查
        if user_role == UserRole.VICTIM:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="受災戶無法認領任務，請發布需求"
            )
        
        claim = task_crud.claim_task(db, claim_data.task_id, user_id, claim_data.notes)
        
        # 發送認領通知給任務建立者
        task = task_crud.get_task(db, claim_data.task_id)
        if task:
            # TODO: 實作通知服務
            pass
        
        return self._convert_claim_to_response(claim)
    
    def update_claim_status(
        self, 
        db: Session, 
        claim_id: str, 
        new_status: str,
        user_id: str,
        notes: Optional[str] = None
    ) -> Optional[TaskClaimResponse]:
        """更新認領狀態"""
        claim = task_crud.update_claim_status(db, claim_id, new_status, user_id, notes)
        if not claim:
            return None
        
        # 發送狀態更新通知
        if new_status == "completed":
            task = task_crud.get_task(db, str(claim.task_id))
            if task:
                # TODO: 實作通知服務
                pass
        
        return self._convert_claim_to_response(claim)
    
    def get_user_claims(
        self, 
        db: Session, 
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> TaskClaimListResponse:
        """獲取用戶的任務認領記錄"""
        claims, total = task_crud.get_user_claims(db, user_id, skip, limit)
        
        claim_responses = [self._convert_claim_to_response(claim) for claim in claims]
        
        return TaskClaimListResponse(
            claims=claim_responses,
            total=total,
            skip=skip,
            limit=limit
        )
    
    def get_task_claims(
        self, 
        db: Session, 
        task_id: str,
        user_id: str,
        user_role: UserRole
    ) -> List[TaskClaimResponse]:
        """獲取任務的所有認領記錄"""
        task = task_crud.get_task(db, task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任務不存在"
            )
        
        # 權限檢查 - 只有任務建立者和管理員可以查看認領記錄
        if user_role != UserRole.ADMIN and str(task.creator_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限查看此任務的認領記錄"
            )
        
        claims = task_crud.get_task_claims(db, task_id)
        return [self._convert_claim_to_response(claim) for claim in claims]
    
    def get_task_history(
        self, 
        db: Session, 
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None
    ) -> TaskClaimListResponse:
        """獲取用戶的任務歷史記錄"""
        claims, total = task_crud.get_task_history(db, user_id, skip, limit, status_filter)
        
        claim_responses = [self._convert_claim_to_response(claim) for claim in claims]
        
        return TaskClaimListResponse(
            claims=claim_responses,
            total=total,
            skip=skip,
            limit=limit
        )
    
    def get_task_activity_log(
        self, 
        db: Session, 
        task_id: str,
        user_id: str,
        user_role: UserRole
    ) -> List[Dict[str, Any]]:
        """獲取任務活動日誌"""
        task = task_crud.get_task(db, task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任務不存在"
            )
        
        # 權限檢查 - 只有任務建立者、認領者和管理員可以查看活動日誌
        if user_role != UserRole.ADMIN and str(task.creator_id) != user_id:
            # 檢查是否為任務認領者
            is_claimer = any(str(claim.user_id) == user_id for claim in task.task_claims)
            if not is_claimer:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="沒有權限查看此任務的活動日誌"
                )
        
        return task_crud.get_task_activity_log(db, task_id)
    
    def check_task_conflicts(
        self, 
        db: Session, 
        task_id: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """檢查任務認領衝突"""
        return task_crud.check_task_conflicts(db, task_id, user_id)

    def get_task_statistics(self, db: Session) -> TaskStatistics:
        """獲取任務統計資料"""
        stats = task_crud.get_task_statistics(db)
        return TaskStatistics(**stats)
    
    def _convert_to_response(
        self, 
        task: Task, 
        user_id: str, 
        user_role: UserRole
    ) -> TaskResponse:
        """轉換任務模型為回應模型"""
        # 計算已認領人數
        claimed_count = len([c for c in task.task_claims if c.status == "claimed"])
        
        # 判斷是否可認領
        can_claim = (
            task.status == TaskStatus.AVAILABLE.value and
            user_role in [UserRole.VOLUNTEER, UserRole.OFFICIAL_ORG, UserRole.UNOFFICIAL_ORG, UserRole.SUPPLY_MANAGER] and
            claimed_count < task.required_volunteers and
            not any(str(c.user_id) == user_id for c in task.task_claims)
        )
        
        # 判斷是否可編輯
        can_edit = (
            user_role == UserRole.ADMIN or 
            (str(task.creator_id) == user_id and task.status == TaskStatus.AVAILABLE.value)
        )
        
        return TaskResponse(
            id=str(task.id),
            creator_id=str(task.creator_id),
            title=task.title,
            description=task.description,
            task_type=task.task_type,
            status=task.status,
            location_data=task.location_data,
            required_volunteers=task.required_volunteers,
            required_skills=task.required_skills,
            deadline=task.deadline,
            priority_level=task.priority_level,
            approval_status=task.approval_status,
            approved_by=str(task.approved_by) if task.approved_by else None,
            approved_at=task.approved_at,
            created_at=task.created_at,
            updated_at=task.updated_at,
            creator_name=task.creator.name if task.creator else None,
            creator_role=task.creator.role if task.creator else None,
            approver_name=task.approver.name if task.approver else None,
            claimed_count=claimed_count,
            can_claim=can_claim,
            can_edit=can_edit
        )
    
    def _convert_claim_to_response(self, claim: TaskClaim) -> TaskClaimResponse:
        """轉換認領模型為回應模型"""
        return TaskClaimResponse(
            id=str(claim.id),
            task_id=str(claim.task_id),
            user_id=str(claim.user_id),
            status=claim.status,
            notes=claim.notes,
            claimed_at=claim.claimed_at,
            started_at=claim.started_at,
            completed_at=claim.completed_at,
            task_title=claim.task.title if claim.task else None,
            task_type=claim.task.task_type if claim.task else None,
            user_name=claim.user.name if claim.user else None,
            user_role=claim.user.role if claim.user else None
        )
    
    def _can_view_task(self, task: Task, user_id: str, user_role: UserRole) -> bool:
        """檢查用戶是否可以查看任務"""
        # 管理員可以查看所有任務
        if user_role == UserRole.ADMIN:
            return True
        
        # 任務建立者可以查看自己的任務
        if str(task.creator_id) == user_id:
            return True
        
        # 已審核通過的任務，所有用戶都可以查看
        if task.approval_status == "approved":
            return True
        
        # 待審核的任務只有建立者和管理員可以查看
        return False


# 建立全域實例
task_service = TaskService()