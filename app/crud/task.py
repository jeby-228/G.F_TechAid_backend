"""
任務管理 CRUD 操作
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, text
from fastapi import HTTPException, status

from app.models.task import Task, TaskClaim, TaskType, TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskSearchQuery
from app.utils.constants import UserRole, TaskStatus as TaskStatusEnum
import uuid


class TaskCRUD:
    """任務 CRUD 操作類"""
    
    def create_task(
        self, 
        db: Session, 
        task_data: TaskCreate, 
        creator_id: str,
        creator_role: UserRole
    ) -> Task:
        """建立新任務"""
        # 根據建立者角色決定審核狀態
        if creator_role == UserRole.UNOFFICIAL_ORG:
            approval_status = "pending"
            status = TaskStatusEnum.PENDING
        else:
            approval_status = "approved"
            status = TaskStatusEnum.AVAILABLE
        
        # 建立任務物件
        db_task = Task(
            id=uuid.uuid4(),
            creator_id=uuid.UUID(creator_id),
            title=task_data.title,
            description=task_data.description,
            task_type=task_data.task_type.value,
            status=status.value,
            location_data=task_data.location_data.dict(),
            required_volunteers=task_data.required_volunteers,
            required_skills=task_data.required_skills,
            deadline=task_data.deadline,
            priority_level=task_data.priority_level,
            approval_status=approval_status
        )
        
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        return db_task
    
    def get_task(self, db: Session, task_id: str) -> Optional[Task]:
        """根據 ID 獲取任務"""
        return db.query(Task).options(
            joinedload(Task.creator),
            joinedload(Task.approver),
            joinedload(Task.task_claims)
        ).filter(Task.id == uuid.UUID(task_id)).first()
    
    def get_tasks(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search_query: Optional[TaskSearchQuery] = None,
        user_role: Optional[UserRole] = None,
        user_id: Optional[str] = None
    ) -> Tuple[List[Task], int]:
        """獲取任務列表"""
        query = db.query(Task).options(
            joinedload(Task.creator),
            joinedload(Task.approver),
            joinedload(Task.task_claims).joinedload(TaskClaim.user)
        )
        
        # 基於用戶角色的權限篩選
        if user_role and user_role != UserRole.ADMIN:
            if user_role == UserRole.VICTIM:
                # 受災戶只能看到可認領的任務和自己相關的任務
                query = query.filter(
                    or_(
                        Task.status == TaskStatusEnum.AVAILABLE.value,
                        Task.task_claims.any(TaskClaim.user_id == uuid.UUID(user_id))
                    )
                )
            elif user_role == UserRole.UNOFFICIAL_ORG:
                # 非正式組織可以看到自己建立的任務和可認領的任務
                query = query.filter(
                    or_(
                        Task.creator_id == uuid.UUID(user_id),
                        and_(
                            Task.status == TaskStatusEnum.AVAILABLE.value,
                            Task.approval_status == "approved"
                        )
                    )
                )
            elif user_role in [UserRole.OFFICIAL_ORG, UserRole.SUPPLY_MANAGER]:
                # 正式組織和物資管理者可以看到所有已審核的任務和自己建立的任務
                query = query.filter(
                    or_(
                        Task.creator_id == uuid.UUID(user_id),
                        Task.approval_status == "approved"
                    )
                )
            elif user_role == UserRole.VOLUNTEER:
                # 一般志工可以看到可認領的任務和自己認領的任務
                query = query.filter(
                    or_(
                        Task.status == TaskStatusEnum.AVAILABLE.value,
                        Task.task_claims.any(TaskClaim.user_id == uuid.UUID(user_id))
                    )
                )
        
        # 搜尋條件
        if search_query:
            if search_query.title:
                query = query.filter(Task.title.ilike(f"%{search_query.title}%"))
            if search_query.task_type:
                query = query.filter(Task.task_type == search_query.task_type.value)
            if search_query.status:
                query = query.filter(Task.status == search_query.status.value)
            if search_query.creator_id:
                query = query.filter(Task.creator_id == uuid.UUID(search_query.creator_id))
            if search_query.priority_level:
                query = query.filter(Task.priority_level == search_query.priority_level)
            
            # 地理位置篩選
            if (search_query.location_radius and 
                search_query.center_lat is not None and 
                search_query.center_lng is not None):
                # 使用 Haversine 公式計算距離（簡化版本，適用於 SQLite）
                try:
                    # PostgreSQL 版本
                    distance_query = text("""
                        (6371 * acos(cos(radians(:lat)) * cos(radians(CAST(location_data->>'coordinates'->>'lat' AS FLOAT))) 
                        * cos(radians(CAST(location_data->>'coordinates'->>'lng' AS FLOAT)) - radians(:lng)) 
                        + sin(radians(:lat)) * sin(radians(CAST(location_data->>'coordinates'->>'lat' AS FLOAT))))) <= :radius
                    """)
                    query = query.filter(distance_query.params(
                        lat=search_query.center_lat,
                        lng=search_query.center_lng,
                        radius=search_query.location_radius
                    ))
                except Exception:
                    # SQLite 簡化版本 - 基於經緯度範圍篩選
                    lat_range = search_query.location_radius / 111.0  # 大約 1 度 = 111 公里
                    lng_range = search_query.location_radius / (111.0 * func.cos(func.radians(search_query.center_lat)))
                    
                    # 使用 JSON 提取函數（SQLite 支援）
                    query = query.filter(
                        and_(
                            func.json_extract(Task.location_data, '$.coordinates.lat').between(
                                search_query.center_lat - lat_range,
                                search_query.center_lat + lat_range
                            ),
                            func.json_extract(Task.location_data, '$.coordinates.lng').between(
                                search_query.center_lng - lng_range,
                                search_query.center_lng + lng_range
                            )
                        )
                    )
        
        # 獲取總數
        total = query.count()
        
        # 排序和分頁
        tasks = query.order_by(
            Task.priority_level.desc(),
            Task.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return tasks, total
    
    def update_task(
        self, 
        db: Session, 
        task_id: str, 
        task_update: TaskUpdate,
        user_id: str,
        user_role: UserRole
    ) -> Optional[Task]:
        """更新任務"""
        task = self.get_task(db, task_id)
        if not task:
            return None
        
        # 權限檢查
        if user_role != UserRole.ADMIN and str(task.creator_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限編輯此任務"
            )
        
        # 狀態檢查 - 已認領或完成的任務不能編輯基本資訊
        if task.status in [TaskStatusEnum.CLAIMED.value, TaskStatusEnum.IN_PROGRESS.value, TaskStatusEnum.COMPLETED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="任務已被認領或完成，無法編輯"
            )
        
        # 更新欄位
        update_data = task_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "location_data" and value:
                setattr(task, field, value.dict())
            else:
                setattr(task, field, value)
        
        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
        return task
    
    def delete_task(
        self, 
        db: Session, 
        task_id: str,
        user_id: str,
        user_role: UserRole
    ) -> bool:
        """刪除任務"""
        task = self.get_task(db, task_id)
        if not task:
            return False
        
        # 權限檢查
        if user_role != UserRole.ADMIN and str(task.creator_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限刪除此任務"
            )
        
        # 狀態檢查 - 已認領的任務不能刪除
        if task.status in [TaskStatusEnum.CLAIMED.value, TaskStatusEnum.IN_PROGRESS.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="任務已被認領，無法刪除"
            )
        
        db.delete(task)
        db.commit()
        return True
    
    def approve_task(
        self, 
        db: Session, 
        task_id: str, 
        approved: bool,
        approver_id: str,
        notes: Optional[str] = None
    ) -> Optional[Task]:
        """審核任務"""
        task = self.get_task(db, task_id)
        if not task:
            return None
        
        if task.approval_status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="任務不在待審核狀態"
            )
        
        if approved:
            task.approval_status = "approved"
            task.status = TaskStatusEnum.AVAILABLE.value
        else:
            task.approval_status = "rejected"
            task.status = TaskStatusEnum.CANCELLED.value
        
        task.approved_by = uuid.UUID(approver_id)
        task.approved_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(task)
        return task
    
    def claim_task(
        self, 
        db: Session, 
        task_id: str, 
        user_id: str,
        notes: Optional[str] = None
    ) -> TaskClaim:
        """認領任務（包含衝突檢查）"""
        # 使用衝突檢查方法
        conflicts = self.check_task_conflicts(db, task_id, user_id)
        if conflicts["has_conflicts"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="; ".join(conflicts["conflicts"])
            )
        
        task = self.get_task(db, task_id)
        
        # 使用資料庫鎖定防止併發問題（PostgreSQL 支援，SQLite 測試環境跳過）
        try:
            db.execute(text("SELECT * FROM tasks WHERE id = :task_id FOR UPDATE"), {"task_id": task_id})
        except Exception:
            # SQLite 不支援 FOR UPDATE，在測試環境中跳過
            pass
        
        # 再次檢查認領人數（防止併發認領）
        current_claims = db.query(TaskClaim).filter(
            and_(
                TaskClaim.task_id == uuid.UUID(task_id),
                TaskClaim.status.in_(["claimed", "started"])
            )
        ).count()
        
        if current_claims >= task.required_volunteers:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="任務認領人數已滿（併發衝突）"
            )
        
        # 建立認領記錄
        claim = TaskClaim(
            id=uuid.uuid4(),
            task_id=uuid.UUID(task_id),
            user_id=uuid.UUID(user_id),
            notes=notes,
            status="claimed"
        )
        
        db.add(claim)
        
        # 更新任務狀態
        if current_claims + 1 >= task.required_volunteers:
            task.status = TaskStatusEnum.CLAIMED.value
        
        task.updated_at = datetime.utcnow()
        
        try:
            db.commit()
            db.refresh(claim)
            return claim
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="認領失敗，請重試"
            )
    
    def update_claim_status(
        self, 
        db: Session, 
        claim_id: str, 
        new_status: str,
        user_id: str,
        notes: Optional[str] = None
    ) -> Optional[TaskClaim]:
        """更新認領狀態"""
        claim = db.query(TaskClaim).filter(TaskClaim.id == uuid.UUID(claim_id)).first()
        if not claim:
            return None
        
        # 權限檢查
        if str(claim.user_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限更新此認領"
            )
        
        claim.status = new_status
        if notes:
            claim.notes = notes
        
        # 根據狀態更新時間戳
        now = datetime.utcnow()
        if new_status == "started":
            claim.started_at = now
        elif new_status == "completed":
            claim.completed_at = now
        
        # 檢查是否所有認領都已完成，更新任務狀態
        task = claim.task
        if new_status == "completed":
            all_claims = db.query(TaskClaim).filter(TaskClaim.task_id == claim.task_id).all()
            completed_claims = [c for c in all_claims if c.status == "completed"]
            
            if len(completed_claims) == len(all_claims):
                task.status = TaskStatusEnum.COMPLETED.value
                task.updated_at = now
        
        db.commit()
        db.refresh(claim)
        return claim
    
    def get_user_claims(
        self, 
        db: Session, 
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[TaskClaim], int]:
        """獲取用戶的任務認領記錄"""
        query = db.query(TaskClaim).options(
            joinedload(TaskClaim.task),
            joinedload(TaskClaim.user)
        ).filter(TaskClaim.user_id == uuid.UUID(user_id))
        
        total = query.count()
        claims = query.order_by(TaskClaim.claimed_at.desc()).offset(skip).limit(limit).all()
        
        return claims, total
    
    def get_task_claims(
        self, 
        db: Session, 
        task_id: str
    ) -> List[TaskClaim]:
        """獲取任務的所有認領記錄"""
        return db.query(TaskClaim).options(
            joinedload(TaskClaim.user)
        ).filter(TaskClaim.task_id == uuid.UUID(task_id)).all()
    
    def get_task_history(
        self, 
        db: Session, 
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None
    ) -> Tuple[List[TaskClaim], int]:
        """獲取用戶的任務歷史記錄（包含已完成和已取消的任務）"""
        query = db.query(TaskClaim).options(
            joinedload(TaskClaim.task).joinedload(Task.creator),
            joinedload(TaskClaim.user)
        ).filter(TaskClaim.user_id == uuid.UUID(user_id))
        
        # 狀態篩選
        if status_filter:
            query = query.filter(TaskClaim.status == status_filter)
        
        # 按時間倒序排列
        query = query.order_by(TaskClaim.claimed_at.desc())
        
        total = query.count()
        claims = query.offset(skip).limit(limit).all()
        
        return claims, total
    
    def get_task_activity_log(
        self, 
        db: Session, 
        task_id: str
    ) -> List[Dict[str, Any]]:
        """獲取任務活動日誌"""
        task = self.get_task(db, task_id)
        if not task:
            return []
        
        activities = []
        
        # 任務建立
        activities.append({
            "timestamp": task.created_at,
            "action": "task_created",
            "description": f"任務「{task.title}」已建立",
            "user_id": str(task.creator_id),
            "user_name": task.creator.name if task.creator else None
        })
        
        # 審核記錄
        if task.approved_at:
            action = "task_approved" if task.approval_status == "approved" else "task_rejected"
            description = f"任務已{'通過' if task.approval_status == 'approved' else '拒絕'}審核"
            activities.append({
                "timestamp": task.approved_at,
                "action": action,
                "description": description,
                "user_id": str(task.approved_by) if task.approved_by else None,
                "user_name": task.approver.name if task.approver else None
            })
        
        # 認領記錄
        for claim in task.task_claims:
            activities.append({
                "timestamp": claim.claimed_at,
                "action": "task_claimed",
                "description": f"{claim.user.name if claim.user else '志工'}認領了任務",
                "user_id": str(claim.user_id),
                "user_name": claim.user.name if claim.user else None,
                "notes": claim.notes
            })
            
            if claim.started_at:
                activities.append({
                    "timestamp": claim.started_at,
                    "action": "task_started",
                    "description": f"{claim.user.name if claim.user else '志工'}開始執行任務",
                    "user_id": str(claim.user_id),
                    "user_name": claim.user.name if claim.user else None
                })
            
            if claim.completed_at:
                activities.append({
                    "timestamp": claim.completed_at,
                    "action": "task_completed",
                    "description": f"{claim.user.name if claim.user else '志工'}完成了任務",
                    "user_id": str(claim.user_id),
                    "user_name": claim.user.name if claim.user else None,
                    "notes": claim.notes
                })
        
        # 按時間排序
        activities.sort(key=lambda x: x["timestamp"])
        
        return activities
    
    def check_task_conflicts(
        self, 
        db: Session, 
        task_id: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """檢查任務認領衝突"""
        conflicts = {
            "has_conflicts": False,
            "conflicts": []
        }
        
        # 驗證 UUID 格式
        try:
            uuid.UUID(task_id)
            uuid.UUID(user_id)
        except ValueError:
            conflicts["conflicts"].append("無效的 ID 格式")
            conflicts["has_conflicts"] = True
            return conflicts
        
        task = self.get_task(db, task_id)
        if not task:
            conflicts["conflicts"].append("任務不存在")
            conflicts["has_conflicts"] = True
            return conflicts
        
        # 檢查任務狀態
        if task.status != TaskStatusEnum.AVAILABLE.value:
            conflicts["conflicts"].append(f"任務狀態為「{task.status}」，無法認領")
            conflicts["has_conflicts"] = True
        
        # 檢查是否已認領
        existing_claim = db.query(TaskClaim).filter(
            and_(
                TaskClaim.task_id == uuid.UUID(task_id),
                TaskClaim.user_id == uuid.UUID(user_id),
                TaskClaim.status.in_(["claimed", "started"])
            )
        ).first()
        
        if existing_claim:
            conflicts["conflicts"].append("您已認領此任務")
            conflicts["has_conflicts"] = True
        
        # 檢查認領人數限制
        current_claims = db.query(TaskClaim).filter(
            and_(
                TaskClaim.task_id == uuid.UUID(task_id),
                TaskClaim.status.in_(["claimed", "started"])
            )
        ).count()
        
        if current_claims >= task.required_volunteers:
            conflicts["conflicts"].append("任務認領人數已滿")
            conflicts["has_conflicts"] = True
        
        # 檢查用戶是否有其他進行中的任務（可選的衝突檢查）
        user_active_claims = db.query(TaskClaim).filter(
            and_(
                TaskClaim.user_id == uuid.UUID(user_id),
                TaskClaim.status.in_(["claimed", "started"])
            )
        ).count()
        
        if user_active_claims >= 3:  # 限制同時認領的任務數量
            conflicts["conflicts"].append("您已認領過多任務，請先完成現有任務")
            conflicts["has_conflicts"] = True
        
        return conflicts

    def get_task_statistics(self, db: Session) -> Dict[str, Any]:
        """獲取任務統計資料"""
        # 總任務數
        total_tasks = db.query(Task).count()
        
        # 各狀態任務數
        status_stats = db.query(
            Task.status, 
            func.count(Task.id)
        ).group_by(Task.status).all()
        tasks_by_status = {status: count for status, count in status_stats}
        
        # 各類型任務數
        type_stats = db.query(
            Task.task_type, 
            func.count(Task.id)
        ).group_by(Task.task_type).all()
        tasks_by_type = {task_type: count for task_type, count in type_stats}
        
        # 待審核任務數
        pending_approval = db.query(Task).filter(Task.approval_status == "pending").count()
        
        # 可認領任務數
        available_tasks = db.query(Task).filter(Task.status == TaskStatusEnum.AVAILABLE.value).count()
        
        # 已完成任務數
        completed_tasks = db.query(Task).filter(Task.status == TaskStatusEnum.COMPLETED.value).count()
        
        # 活躍志工數（有認領任務的志工）
        active_volunteers = db.query(TaskClaim.user_id).distinct().count()
        
        return {
            "total_tasks": total_tasks,
            "tasks_by_status": tasks_by_status,
            "tasks_by_type": tasks_by_type,
            "pending_approval": pending_approval,
            "available_tasks": available_tasks,
            "completed_tasks": completed_tasks,
            "active_volunteers": active_volunteers
        }


# 建立全域實例
task_crud = TaskCRUD()