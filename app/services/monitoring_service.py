"""
系統監控服務
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.task import Task, TaskClaim
from app.models.need import Need, NeedAssignment
from app.models.supply import SupplyReservation, InventoryItem, SupplyStation
from app.models.user import User
from app.models.system import SystemLog
from app.utils.constants import TaskStatus, NeedStatus, UserRole


class MonitoringService:
    """系統監控服務類"""
    
    def get_real_time_statistics(self, db: Session) -> Dict[str, Any]:
        """獲取即時統計資料"""
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 基本統計
        total_users = db.query(User).count()
        total_tasks = db.query(Task).count()
        total_needs = db.query(Need).count()
        total_supply_stations = db.query(SupplyStation).filter(SupplyStation.is_active == True).count()
        
        # 今日新增統計
        today_new_users = db.query(User).filter(User.created_at >= today).count()
        today_new_tasks = db.query(Task).filter(Task.created_at >= today).count()
        today_new_needs = db.query(Need).filter(Need.created_at >= today).count()
        
        # 活躍統計
        active_tasks = db.query(Task).filter(
            Task.status.in_(['available', 'claimed', 'in_progress'])
        ).count()
        
        open_needs = db.query(Need).filter(
            Need.status.in_(['open', 'assigned', 'in_progress'])
        ).count()
        
        # 用戶角色分布
        user_role_distribution = db.query(
            User.role, func.count(User.id).label('count')
        ).group_by(User.role).all()
        
        role_stats = {role: count for role, count in user_role_distribution}
        
        return {
            "overview": {
                "total_users": total_users,
                "total_tasks": total_tasks,
                "total_needs": total_needs,
                "total_supply_stations": total_supply_stations,
                "active_tasks": active_tasks,
                "open_needs": open_needs
            },
            "today_stats": {
                "new_users": today_new_users,
                "new_tasks": today_new_tasks,
                "new_needs": today_new_needs
            },
            "user_distribution": role_stats,
            "last_updated": now.isoformat()
        }
    
    def get_disaster_relief_progress(self, db: Session, days: int = 7) -> Dict[str, Any]:
        """獲取救災進度追蹤統計"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 任務進度統計
        task_progress = self._get_task_progress_stats(db, start_date, end_date)
        
        # 需求處理進度統計
        need_progress = self._get_need_progress_stats(db, start_date, end_date)
        
        # 整體完成率
        overall_completion = self._calculate_overall_completion_rate(db, start_date, end_date)
        
        # 每日進度趨勢
        daily_progress = self._get_daily_progress_trend(db, start_date, end_date)
        
        # 緊急程度分析
        urgency_analysis = self._get_urgency_analysis(db)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "task_progress": task_progress,
            "need_progress": need_progress,
            "overall_completion": overall_completion,
            "daily_progress": daily_progress,
            "urgency_analysis": urgency_analysis
        }
    
    def get_task_completion_statistics(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """獲取任務完成率統計"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 基本完成率統計
        total_tasks = db.query(Task).filter(
            Task.created_at >= start_date,
            Task.created_at <= end_date
        ).count()
        
        completed_tasks = db.query(Task).filter(
            Task.created_at >= start_date,
            Task.created_at <= end_date,
            Task.status == TaskStatus.COMPLETED.value
        ).count()
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # 按任務類型分組的完成率
        from sqlalchemy import case
        task_type_completion = db.query(
            Task.task_type,
            func.count(Task.id).label('total'),
            func.sum(case((Task.status == TaskStatus.COMPLETED.value, 1), else_=0)).label('completed')
        ).filter(
            Task.created_at >= start_date,
            Task.created_at <= end_date
        ).group_by(Task.task_type).all()
        
        type_stats = []
        for task_type, total, completed in task_type_completion:
            completed = completed or 0
            rate = (completed / total * 100) if total > 0 else 0
            type_stats.append({
                "task_type": task_type,
                "total": total,
                "completed": completed,
                "completion_rate": round(rate, 2)
            })
        
        # 平均完成時間
        avg_completion_time = self._calculate_average_completion_time(db, start_date, end_date)
        
        # 志工效率統計
        volunteer_efficiency = self._get_volunteer_efficiency_stats(db, start_date, end_date)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "overall": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": round(completion_rate, 2)
            },
            "by_task_type": type_stats,
            "average_completion_time_hours": avg_completion_time,
            "volunteer_efficiency": volunteer_efficiency
        }
    
    def get_supply_flow_monitoring(self, db: Session, days: int = 7) -> Dict[str, Any]:
        """獲取物資流向監控統計"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 物資預訂統計
        reservation_stats = self._get_supply_reservation_stats(db, start_date, end_date)
        
        # 物資站點活動統計
        station_activity = self._get_station_activity_stats(db, start_date, end_date)
        
        # 物資類型流向統計
        supply_type_flow = self._get_supply_type_flow_stats(db, start_date, end_date)
        
        # 配送效率統計
        delivery_efficiency = self._get_delivery_efficiency_stats(db, start_date, end_date)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "reservation_stats": reservation_stats,
            "station_activity": station_activity,
            "supply_type_flow": supply_type_flow,
            "delivery_efficiency": delivery_efficiency
        }
    
    def get_inventory_statistics(self, db: Session) -> Dict[str, Any]:
        """獲取庫存統計"""
        # 總庫存統計
        total_stations = db.query(SupplyStation).filter(SupplyStation.is_active == True).count()
        total_inventory_items = db.query(InventoryItem).filter(InventoryItem.is_available == True).count()
        
        # 按物資類型統計庫存
        inventory_by_type = db.query(
            InventoryItem.supply_type,
            func.count(InventoryItem.id).label('count')
        ).filter(
            InventoryItem.is_available == True
        ).group_by(InventoryItem.supply_type).all()
        
        type_inventory = {supply_type: count for supply_type, count in inventory_by_type}
        
        # 按站點統計庫存
        inventory_by_station = db.query(
            SupplyStation.name,
            func.count(InventoryItem.id).label('count')
        ).join(
            InventoryItem, SupplyStation.id == InventoryItem.station_id
        ).filter(
            SupplyStation.is_active == True,
            InventoryItem.is_available == True
        ).group_by(SupplyStation.id, SupplyStation.name).all()
        
        station_inventory = [
            {"station_name": name, "inventory_count": count}
            for name, count in inventory_by_station
        ]
        
        # 低庫存警告（假設每個站點應該有多種物資類型）
        low_inventory_stations = []
        for station_name, count in inventory_by_station:
            if count < 5:  # 假設低於5種物資類型為低庫存
                low_inventory_stations.append({
                    "station_name": station_name,
                    "inventory_count": count
                })
        
        return {
            "overview": {
                "total_active_stations": total_stations,
                "total_available_items": total_inventory_items
            },
            "by_supply_type": type_inventory,
            "by_station": station_inventory,
            "low_inventory_alerts": low_inventory_stations,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def get_system_activity_log(
        self, 
        db: Session, 
        hours: int = 24,
        limit: int = 100
    ) -> Dict[str, Any]:
        """獲取系統活動日誌"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # 獲取活動日誌
        logs = db.query(SystemLog).filter(
            SystemLog.created_at >= start_time,
            SystemLog.created_at <= end_time
        ).order_by(SystemLog.created_at.desc()).limit(limit).all()
        
        # 活動類型統計
        activity_stats = db.query(
            SystemLog.action,
            func.count(SystemLog.id).label('count')
        ).filter(
            SystemLog.created_at >= start_time,
            SystemLog.created_at <= end_time
        ).group_by(SystemLog.action).all()
        
        activity_counts = {action: count for action, count in activity_stats}
        
        # 用戶活動統計
        user_activity = db.query(
            func.count(func.distinct(SystemLog.user_id)).label('active_users'),
            func.count(SystemLog.id).label('total_actions')
        ).filter(
            SystemLog.created_at >= start_time,
            SystemLog.created_at <= end_time,
            SystemLog.user_id.isnot(None)
        ).first()
        
        log_entries = []
        for log in logs:
            log_entries.append({
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else None,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat()
            })
        
        return {
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours
            },
            "summary": {
                "active_users": user_activity.active_users if user_activity else 0,
                "total_actions": user_activity.total_actions if user_activity else 0
            },
            "activity_counts": activity_counts,
            "recent_logs": log_entries
        }
    
    def _get_task_progress_stats(self, db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """獲取任務進度統計"""
        # 任務狀態分布
        task_status_stats = db.query(
            Task.status,
            func.count(Task.id).label('count')
        ).filter(
            Task.created_at >= start_date,
            Task.created_at <= end_date
        ).group_by(Task.status).all()
        
        status_distribution = {status: count for status, count in task_status_stats}
        
        # 計算完成率
        total_tasks = sum(status_distribution.values())
        completed_tasks = status_distribution.get(TaskStatus.COMPLETED.value, 0)
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "status_distribution": status_distribution,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": round(completion_rate, 2)
        }
    
    def _get_need_progress_stats(self, db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """獲取需求進度統計"""
        # 需求狀態分布
        need_status_stats = db.query(
            Need.status,
            func.count(Need.id).label('count')
        ).filter(
            Need.created_at >= start_date,
            Need.created_at <= end_date
        ).group_by(Need.status).all()
        
        status_distribution = {status: count for status, count in need_status_stats}
        
        # 計算解決率
        total_needs = sum(status_distribution.values())
        resolved_needs = status_distribution.get(NeedStatus.RESOLVED.value, 0)
        resolution_rate = (resolved_needs / total_needs * 100) if total_needs > 0 else 0
        
        return {
            "status_distribution": status_distribution,
            "total_needs": total_needs,
            "resolved_needs": resolved_needs,
            "resolution_rate": round(resolution_rate, 2)
        }
    
    def _calculate_overall_completion_rate(self, db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """計算整體完成率"""
        # 任務完成率
        total_tasks = db.query(Task).filter(
            Task.created_at >= start_date,
            Task.created_at <= end_date
        ).count()
        
        completed_tasks = db.query(Task).filter(
            Task.created_at >= start_date,
            Task.created_at <= end_date,
            Task.status == TaskStatus.COMPLETED.value
        ).count()
        
        task_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # 需求解決率
        total_needs = db.query(Need).filter(
            Need.created_at >= start_date,
            Need.created_at <= end_date
        ).count()
        
        resolved_needs = db.query(Need).filter(
            Need.created_at >= start_date,
            Need.created_at <= end_date,
            Need.status == NeedStatus.RESOLVED.value
        ).count()
        
        need_resolution_rate = (resolved_needs / total_needs * 100) if total_needs > 0 else 0
        
        # 綜合完成率（加權平均）
        total_items = total_tasks + total_needs
        if total_items > 0:
            overall_rate = ((completed_tasks + resolved_needs) / total_items * 100)
        else:
            overall_rate = 0
        
        return {
            "task_completion_rate": round(task_completion_rate, 2),
            "need_resolution_rate": round(need_resolution_rate, 2),
            "overall_completion_rate": round(overall_rate, 2),
            "total_items": total_items,
            "completed_items": completed_tasks + resolved_needs
        }
    
    def _get_daily_progress_trend(self, db: Session, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """獲取每日進度趨勢"""
        daily_trends = []
        current_date = start_date
        
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            
            # 當日完成的任務數
            daily_completed_tasks = db.query(Task).filter(
                Task.updated_at >= current_date,
                Task.updated_at < next_date,
                Task.status == TaskStatus.COMPLETED.value
            ).count()
            
            # 當日解決的需求數
            daily_resolved_needs = db.query(Need).filter(
                Need.updated_at >= current_date,
                Need.updated_at < next_date,
                Need.status == NeedStatus.RESOLVED.value
            ).count()
            
            # 當日新增的任務和需求數
            daily_new_tasks = db.query(Task).filter(
                Task.created_at >= current_date,
                Task.created_at < next_date
            ).count()
            
            daily_new_needs = db.query(Need).filter(
                Need.created_at >= current_date,
                Need.created_at < next_date
            ).count()
            
            daily_trends.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "completed_tasks": daily_completed_tasks,
                "resolved_needs": daily_resolved_needs,
                "new_tasks": daily_new_tasks,
                "new_needs": daily_new_needs,
                "total_completed": daily_completed_tasks + daily_resolved_needs,
                "total_new": daily_new_tasks + daily_new_needs
            })
            
            current_date = next_date
        
        return daily_trends
    
    def _get_urgency_analysis(self, db: Session) -> Dict[str, Any]:
        """獲取緊急程度分析"""
        # 需求緊急程度分布
        need_urgency_stats = db.query(
            Need.urgency_level,
            func.count(Need.id).label('count')
        ).filter(
            Need.status.in_([NeedStatus.OPEN.value, NeedStatus.ASSIGNED.value, NeedStatus.IN_PROGRESS.value])
        ).group_by(Need.urgency_level).all()
        
        urgency_distribution = {f"level_{level}": count for level, count in need_urgency_stats}
        
        # 高優先級任務統計
        high_priority_tasks = db.query(Task).filter(
            Task.priority_level >= 4,
            Task.status.in_([TaskStatus.AVAILABLE.value, TaskStatus.CLAIMED.value, TaskStatus.IN_PROGRESS.value])
        ).count()
        
        # 高緊急需求統計
        high_urgency_needs = db.query(Need).filter(
            Need.urgency_level >= 4,
            Need.status.in_([NeedStatus.OPEN.value, NeedStatus.ASSIGNED.value, NeedStatus.IN_PROGRESS.value])
        ).count()
        
        return {
            "need_urgency_distribution": urgency_distribution,
            "high_priority_tasks": high_priority_tasks,
            "high_urgency_needs": high_urgency_needs,
            "total_urgent_items": high_priority_tasks + high_urgency_needs
        }
    
    def _calculate_average_completion_time(self, db: Session, start_date: datetime, end_date: datetime) -> float:
        """計算平均完成時間（小時）"""
        completed_claims = db.query(TaskClaim).filter(
            TaskClaim.completed_at >= start_date,
            TaskClaim.completed_at <= end_date,
            TaskClaim.completed_at.isnot(None),
            TaskClaim.claimed_at.isnot(None)
        ).all()
        
        if not completed_claims:
            return 0.0
        
        total_hours = 0
        for claim in completed_claims:
            duration = claim.completed_at - claim.claimed_at
            total_hours += duration.total_seconds() / 3600
        
        return round(total_hours / len(completed_claims), 2)
    
    def _get_volunteer_efficiency_stats(self, db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """獲取志工效率統計"""
        # 活躍志工數量
        active_volunteers = db.query(func.count(func.distinct(TaskClaim.user_id))).filter(
            TaskClaim.claimed_at >= start_date,
            TaskClaim.claimed_at <= end_date
        ).scalar()
        
        # 平均每個志工完成的任務數
        total_completed_claims = db.query(TaskClaim).filter(
            TaskClaim.completed_at >= start_date,
            TaskClaim.completed_at <= end_date,
            TaskClaim.status == "completed"
        ).count()
        
        avg_tasks_per_volunteer = (total_completed_claims / active_volunteers) if active_volunteers > 0 else 0
        
        # 最活躍的志工
        top_volunteers = db.query(
            TaskClaim.user_id,
            func.count(TaskClaim.id).label('completed_count')
        ).filter(
            TaskClaim.completed_at >= start_date,
            TaskClaim.completed_at <= end_date,
            TaskClaim.status == "completed"
        ).group_by(TaskClaim.user_id).order_by(func.count(TaskClaim.id).desc()).limit(5).all()
        
        top_volunteer_stats = []
        for user_id, count in top_volunteers:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                top_volunteer_stats.append({
                    "user_id": str(user_id),
                    "user_name": user.name,
                    "completed_tasks": count
                })
        
        return {
            "active_volunteers": active_volunteers,
            "total_completed_tasks": total_completed_claims,
            "avg_tasks_per_volunteer": round(avg_tasks_per_volunteer, 2),
            "top_volunteers": top_volunteer_stats
        }
    
    def _get_supply_reservation_stats(self, db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """獲取物資預訂統計"""
        # 預訂狀態分布
        reservation_status_stats = db.query(
            SupplyReservation.status,
            func.count(SupplyReservation.id).label('count')
        ).filter(
            SupplyReservation.reserved_at >= start_date,
            SupplyReservation.reserved_at <= end_date
        ).group_by(SupplyReservation.status).all()
        
        status_distribution = {status: count for status, count in reservation_status_stats}
        
        # 總預訂數和完成數
        total_reservations = sum(status_distribution.values())
        delivered_reservations = status_distribution.get("delivered", 0)
        delivery_rate = (delivered_reservations / total_reservations * 100) if total_reservations > 0 else 0
        
        return {
            "status_distribution": status_distribution,
            "total_reservations": total_reservations,
            "delivered_reservations": delivered_reservations,
            "delivery_rate": round(delivery_rate, 2)
        }
    
    def _get_station_activity_stats(self, db: Session, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """獲取物資站點活動統計"""
        station_stats = db.query(
            SupplyStation.name,
            func.count(SupplyReservation.id).label('reservation_count')
        ).join(
            SupplyReservation, SupplyStation.id == SupplyReservation.station_id
        ).filter(
            SupplyReservation.reserved_at >= start_date,
            SupplyReservation.reserved_at <= end_date
        ).group_by(SupplyStation.id, SupplyStation.name).order_by(
            func.count(SupplyReservation.id).desc()
        ).all()
        
        return [
            {
                "station_name": name,
                "reservation_count": count
            }
            for name, count in station_stats
        ]
    
    def _get_supply_type_flow_stats(self, db: Session, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """獲取物資類型流向統計"""
        from app.models.supply import ReservationItem
        
        supply_flow_stats = db.query(
            ReservationItem.supply_type,
            func.sum(ReservationItem.confirmed_quantity).label('total_quantity'),
            func.count(ReservationItem.id).label('reservation_count')
        ).join(
            SupplyReservation, ReservationItem.reservation_id == SupplyReservation.id
        ).filter(
            SupplyReservation.reserved_at >= start_date,
            SupplyReservation.reserved_at <= end_date
        ).group_by(ReservationItem.supply_type).order_by(
            func.sum(ReservationItem.confirmed_quantity).desc()
        ).all()
        
        return [
            {
                "supply_type": supply_type,
                "total_quantity": int(total_quantity) if total_quantity else 0,
                "reservation_count": reservation_count
            }
            for supply_type, total_quantity, reservation_count in supply_flow_stats
        ]
    
    def _get_delivery_efficiency_stats(self, db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """獲取配送效率統計"""
        # 平均配送時間（從確認到配送完成）
        delivered_reservations = db.query(SupplyReservation).filter(
            SupplyReservation.delivered_at >= start_date,
            SupplyReservation.delivered_at <= end_date,
            SupplyReservation.confirmed_at.isnot(None),
            SupplyReservation.delivered_at.isnot(None)
        ).all()
        
        if delivered_reservations:
            total_delivery_time = 0
            for reservation in delivered_reservations:
                delivery_time = reservation.delivered_at - reservation.confirmed_at
                total_delivery_time += delivery_time.total_seconds() / 3600  # 轉換為小時
            
            avg_delivery_time = total_delivery_time / len(delivered_reservations)
        else:
            avg_delivery_time = 0
        
        # 配送成功率
        total_confirmed = db.query(SupplyReservation).filter(
            SupplyReservation.confirmed_at >= start_date,
            SupplyReservation.confirmed_at <= end_date
        ).count()
        
        total_delivered = len(delivered_reservations)
        delivery_success_rate = (total_delivered / total_confirmed * 100) if total_confirmed > 0 else 0
        
        return {
            "avg_delivery_time_hours": round(avg_delivery_time, 2),
            "total_confirmed_reservations": total_confirmed,
            "total_delivered_reservations": total_delivered,
            "delivery_success_rate": round(delivery_success_rate, 2)
        }


# 建立全域實例
monitoring_service = MonitoringService()