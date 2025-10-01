"""
需求相關的 CRUD 操作
"""
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, text
from app.models.need import Need, NeedAssignment, NeedType as NeedTypeModel, NeedStatus as NeedStatusModel
from app.models.user import User
from app.models.task import Task
from app.schemas.need import (
    NeedCreate, NeedUpdate, NeedSearchQuery, NeedStatistics,
    NeedStatusUpdate, NeedAssignment as NeedAssignmentSchema
)
from app.utils.constants import NeedStatus, NeedType
from datetime import datetime, timedelta
import math


class NeedCRUD:
    """需求 CRUD 操作類"""
    
    def get_by_id(self, db: Session, need_id: str) -> Optional[Need]:
        """根據 ID 取得需求"""
        return db.query(Need).options(
            joinedload(Need.reporter),
            joinedload(Need.assignee),
            joinedload(Need.need_type_obj),
            joinedload(Need.need_status_obj)
        ).filter(Need.id == need_id).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search_query: Optional[NeedSearchQuery] = None
    ) -> List[Need]:
        """取得需求列表（支援搜尋和篩選）"""
        query = db.query(Need).options(
            joinedload(Need.reporter),
            joinedload(Need.assignee),
            joinedload(Need.need_type_obj),
            joinedload(Need.need_status_obj)
        )
        
        if search_query:
            query = self._apply_search_filters(query, search_query)
        
        return query.order_by(
            desc(Need.urgency_level),  # 緊急程度優先
            desc(Need.created_at)      # 然後按建立時間
        ).offset(skip).limit(limit).all()
    
    def count(self, db: Session, search_query: Optional[NeedSearchQuery] = None) -> int:
        """計算需求總數（支援搜尋和篩選）"""
        query = db.query(func.count(Need.id))
        
        if search_query:
            query = self._apply_search_filters(query, search_query)
        
        return query.scalar()
    
    def create(self, db: Session, need_data: NeedCreate, reporter_id) -> Need:
        """建立新需求"""
        # 建立需求
        db_need = Need(
            reporter_id=reporter_id,
            title=need_data.title,
            description=need_data.description,
            need_type=need_data.need_type.value,
            status=NeedStatus.OPEN.value,
            location_data=need_data.location_data.dict(),
            requirements=need_data.requirements.dict(),
            urgency_level=need_data.urgency_level,
            contact_info=need_data.contact_info.dict() if need_data.contact_info else None
        )
        
        db.add(db_need)
        db.commit()
        db.refresh(db_need)
        return db_need
    
    def update(self, db: Session, need_id: str, need_data: NeedUpdate) -> Optional[Need]:
        """更新需求資料"""
        need = self.get_by_id(db, need_id)
        if not need:
            return None
        
        update_data = need_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field in ['location_data', 'requirements', 'contact_info'] and value:
                # 對於 JSON 欄位，需要轉換為字典
                setattr(need, field, value.dict() if hasattr(value, 'dict') else value)
            else:
                setattr(need, field, value.value if hasattr(value, 'value') else value)
        
        need.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(need)
        return need
    
    def update_status(self, db: Session, need_id: str, status_data: NeedStatusUpdate) -> Optional[Need]:
        """更新需求狀態"""
        need = self.get_by_id(db, need_id)
        if not need:
            return None
        
        old_status = need.status
        need.status = status_data.status.value
        need.updated_at = datetime.utcnow()
        
        # 如果狀態變為已解決，記錄解決時間
        if status_data.status == NeedStatus.RESOLVED and old_status != NeedStatus.RESOLVED.value:
            need.resolved_at = datetime.utcnow()
        
        db.commit()
        db.refresh(need)
        return need
    
    def assign_to_user(self, db: Session, need_id: str, assignment_data: NeedAssignmentSchema) -> Optional[Need]:
        """分配需求給用戶"""
        need = self.get_by_id(db, need_id)
        if not need:
            return None
        
        # 檢查用戶是否存在
        user = db.query(User).filter(User.id == assignment_data.assigned_to).first()
        if not user:
            raise ValueError("指定的用戶不存在")
        
        # 更新需求分配資訊
        need.assigned_to = assignment_data.assigned_to
        need.assigned_at = datetime.utcnow()
        need.status = NeedStatus.ASSIGNED.value
        need.updated_at = datetime.utcnow()
        
        # 建立分配記錄
        assignment = NeedAssignment(
            need_id=need_id,
            task_id=assignment_data.task_id,
            user_id=assignment_data.assigned_to,
            notes=assignment_data.notes,
            status="assigned"
        )
        db.add(assignment)
        
        db.commit()
        db.refresh(need)
        return need
    
    def unassign(self, db: Session, need_id: str) -> Optional[Need]:
        """取消需求分配"""
        need = self.get_by_id(db, need_id)
        if not need:
            return None
        
        need.assigned_to = None
        need.assigned_at = None
        need.status = NeedStatus.OPEN.value
        need.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(need)
        return need
    
    def delete(self, db: Session, need_id: str) -> bool:
        """刪除需求"""
        need = self.get_by_id(db, need_id)
        if not need:
            return False
        
        db.delete(need)
        db.commit()
        return True
    
    def get_by_reporter(self, db: Session, reporter_id: str, skip: int = 0, limit: int = 100) -> List[Need]:
        """取得特定報告者的需求列表"""
        return db.query(Need).options(
            joinedload(Need.assignee),
            joinedload(Need.need_type_obj),
            joinedload(Need.need_status_obj)
        ).filter(Need.reporter_id == reporter_id).order_by(
            desc(Need.created_at)
        ).offset(skip).limit(limit).all()
    
    def get_by_assignee(self, db: Session, assignee_id: str, skip: int = 0, limit: int = 100) -> List[Need]:
        """取得特定負責人的需求列表"""
        return db.query(Need).options(
            joinedload(Need.reporter),
            joinedload(Need.need_type_obj),
            joinedload(Need.need_status_obj)
        ).filter(Need.assigned_to == assignee_id).order_by(
            desc(Need.urgency_level),
            desc(Need.assigned_at)
        ).offset(skip).limit(limit).all()
    
    def get_open_needs(self, db: Session, skip: int = 0, limit: int = 100) -> List[Need]:
        """取得待處理的需求列表"""
        return db.query(Need).options(
            joinedload(Need.reporter),
            joinedload(Need.need_type_obj)
        ).filter(Need.status == NeedStatus.OPEN.value).order_by(
            desc(Need.urgency_level),
            desc(Need.created_at)
        ).offset(skip).limit(limit).all()
    
    def get_urgent_needs(self, db: Session, urgency_threshold: int = 4) -> List[Need]:
        """取得緊急需求列表"""
        return db.query(Need).options(
            joinedload(Need.reporter),
            joinedload(Need.need_type_obj)
        ).filter(
            and_(
                Need.urgency_level >= urgency_threshold,
                Need.status.in_([NeedStatus.OPEN.value, NeedStatus.ASSIGNED.value])
            )
        ).order_by(
            desc(Need.urgency_level),
            desc(Need.created_at)
        ).all()
    
    def get_nearby_needs(
        self, 
        db: Session, 
        center_lat: float, 
        center_lng: float, 
        radius_km: float = 5.0,
        skip: int = 0,
        limit: int = 100
    ) -> List[Need]:
        """取得附近的需求列表"""
        # 使用 Haversine 公式計算距離
        distance_query = text("""
            (6371 * acos(cos(radians(:lat)) * cos(radians(CAST(location_data->>'coordinates'->>'lat' AS FLOAT))) 
            * cos(radians(CAST(location_data->>'coordinates'->>'lng' AS FLOAT)) - radians(:lng)) 
            + sin(radians(:lat)) * sin(radians(CAST(location_data->>'coordinates'->>'lat' AS FLOAT)))))
        """)
        
        return db.query(Need).options(
            joinedload(Need.reporter),
            joinedload(Need.need_type_obj),
            joinedload(Need.need_status_obj)
        ).filter(
            and_(
                Need.location_data['coordinates'].isnot(None),
                distance_query <= radius_km
            )
        ).params(lat=center_lat, lng=center_lng).order_by(
            desc(Need.urgency_level),
            desc(Need.created_at)
        ).offset(skip).limit(limit).all()
    
    def get_statistics(self, db: Session) -> NeedStatistics:
        """取得需求統計資料"""
        # 總需求數
        total_needs = db.query(func.count(Need.id)).scalar()
        
        # 各類型需求數
        type_counts = db.query(
            Need.need_type, 
            func.count(Need.id)
        ).group_by(Need.need_type).all()
        needs_by_type = {need_type: count for need_type, count in type_counts}
        
        # 各狀態需求數
        status_counts = db.query(
            Need.status, 
            func.count(Need.id)
        ).group_by(Need.status).all()
        needs_by_status = {status: count for status, count in status_counts}
        
        # 各緊急程度需求數
        urgency_counts = db.query(
            Need.urgency_level, 
            func.count(Need.id)
        ).group_by(Need.urgency_level).all()
        needs_by_urgency = {str(level): count for level, count in urgency_counts}
        
        # 特定狀態統計
        open_needs = db.query(func.count(Need.id)).filter(Need.status == NeedStatus.OPEN.value).scalar()
        assigned_needs = db.query(func.count(Need.id)).filter(Need.status == NeedStatus.ASSIGNED.value).scalar()
        resolved_needs = db.query(func.count(Need.id)).filter(Need.status == NeedStatus.RESOLVED.value).scalar()
        
        # 平均解決時間（小時）
        avg_resolution_time = None
        resolved_with_times = db.query(
            func.avg(
                func.extract('epoch', Need.resolved_at - Need.created_at) / 3600
            )
        ).filter(
            and_(Need.resolved_at.isnot(None), Need.created_at.isnot(None))
        ).scalar()
        
        if resolved_with_times:
            avg_resolution_time = float(resolved_with_times)
        
        return NeedStatistics(
            total_needs=total_needs,
            needs_by_type=needs_by_type,
            needs_by_status=needs_by_status,
            needs_by_urgency=needs_by_urgency,
            open_needs=open_needs,
            assigned_needs=assigned_needs,
            resolved_needs=resolved_needs,
            average_resolution_time=avg_resolution_time
        )
    
    # 需求分配記錄相關方法
    def get_assignment_by_id(self, db: Session, assignment_id: str) -> Optional[NeedAssignment]:
        """根據 ID 取得分配記錄"""
        return db.query(NeedAssignment).options(
            joinedload(NeedAssignment.need),
            joinedload(NeedAssignment.task),
            joinedload(NeedAssignment.user)
        ).filter(NeedAssignment.id == assignment_id).first()
    
    def get_assignments_by_need(self, db: Session, need_id: str) -> List[NeedAssignment]:
        """取得需求的所有分配記錄"""
        return db.query(NeedAssignment).options(
            joinedload(NeedAssignment.task),
            joinedload(NeedAssignment.user)
        ).filter(NeedAssignment.need_id == need_id).order_by(
            desc(NeedAssignment.assigned_at)
        ).all()
    
    def get_assignments_by_user(self, db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[NeedAssignment]:
        """取得用戶的所有分配記錄"""
        return db.query(NeedAssignment).options(
            joinedload(NeedAssignment.need),
            joinedload(NeedAssignment.task)
        ).filter(NeedAssignment.user_id == user_id).order_by(
            desc(NeedAssignment.assigned_at)
        ).offset(skip).limit(limit).all()
    
    def update_assignment_status(self, db: Session, assignment_id: str, status: str, notes: Optional[str] = None) -> Optional[NeedAssignment]:
        """更新分配記錄狀態"""
        assignment = self.get_assignment_by_id(db, assignment_id)
        if not assignment:
            return None
        
        assignment.status = status
        if notes:
            assignment.notes = notes
        
        if status == "completed":
            assignment.completed_at = datetime.utcnow()
            # 同時更新需求狀態為處理中
            if assignment.need:
                assignment.need.status = NeedStatus.IN_PROGRESS.value
                assignment.need.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(assignment)
        return assignment
    
    def _apply_search_filters(self, query, search_query: NeedSearchQuery):
        """應用搜尋篩選條件"""
        if search_query.title:
            query = query.filter(Need.title.ilike(f"%{search_query.title}%"))
        
        if search_query.need_type:
            query = query.filter(Need.need_type == search_query.need_type.value)
        
        if search_query.status:
            query = query.filter(Need.status == search_query.status.value)
        
        if search_query.urgency_level:
            query = query.filter(Need.urgency_level == search_query.urgency_level)
        
        if search_query.reporter_id:
            query = query.filter(Need.reporter_id == search_query.reporter_id)
        
        if search_query.assigned_to:
            query = query.filter(Need.assigned_to == search_query.assigned_to)
        
        # 地理位置搜尋
        if all([search_query.center_lat, search_query.center_lng, search_query.location_radius]):
            distance_query = text("""
                (6371 * acos(cos(radians(:lat)) * cos(radians(CAST(location_data->>'coordinates'->>'lat' AS FLOAT))) 
                * cos(radians(CAST(location_data->>'coordinates'->>'lng' AS FLOAT)) - radians(:lng)) 
                + sin(radians(:lat)) * sin(radians(CAST(location_data->>'coordinates'->>'lat' AS FLOAT)))))
            """)
            query = query.filter(
                and_(
                    Need.location_data['coordinates'].isnot(None),
                    distance_query <= search_query.location_radius
                )
            ).params(lat=search_query.center_lat, lng=search_query.center_lng)
        
        return query


# 建立全域實例
need_crud = NeedCRUD()