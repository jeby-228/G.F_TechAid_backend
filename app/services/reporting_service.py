"""
報表生成服務
"""
import io
import csv
import json
from typing import Dict, Any, List, Optional, BinaryIO
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.models.task import Task, TaskClaim
from app.models.need import Need, NeedAssignment
from app.models.supply import SupplyReservation, InventoryItem, SupplyStation, ReservationItem
from app.models.user import User
from app.models.system import SystemLog
from app.services.monitoring_service import monitoring_service
from app.utils.constants import TaskStatus, NeedStatus, UserRole


class ReportingService:
    """報表生成服務類"""

    def __init__(self):
        """初始化報表服務"""
        self.styles = getSampleStyleSheet()
        # 設定中文字體樣式
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # 置中
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=12
        )

    def generate_disaster_relief_report(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        format_type: str = "pdf"
    ) -> bytes:
        """
        生成救災活動報表

        Args:
            db: 資料庫會話
            start_date: 開始日期
            end_date: 結束日期
            format_type: 格式類型 ("pdf", "csv", "excel")

        Returns:
            報表檔案的二進位資料
        """
        # 收集報表資料
        report_data = self._collect_disaster_relief_data(db, start_date, end_date)

        if format_type.lower() == "pdf":
            return self._generate_pdf_report(report_data, "救災活動報表")
        elif format_type.lower() == "csv":
            return self._generate_csv_report(report_data)
        elif format_type.lower() == "excel":
            return self._generate_excel_report(report_data, "救災活動報表")
        else:
            raise ValueError(f"不支援的格式類型: {format_type}")

    def generate_task_completion_report(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        format_type: str = "pdf"
    ) -> bytes:
        """
        生成任務完成報表

        Args:
            db: 資料庫會話
            start_date: 開始日期
            end_date: 結束日期
            format_type: 格式類型

        Returns:
            報表檔案的二進位資料
        """
        # 收集任務完成資料
        report_data = self._collect_task_completion_data(db, start_date, end_date)

        if format_type.lower() == "pdf":
            return self._generate_pdf_report(report_data, "任務完成報表")
        elif format_type.lower() == "csv":
            return self._generate_csv_report(report_data)
        elif format_type.lower() == "excel":
            return self._generate_excel_report(report_data, "任務完成報表")
        else:
            raise ValueError(f"不支援的格式類型: {format_type}")

    def generate_supply_flow_report(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        format_type: str = "pdf"
    ) -> bytes:
        """
        生成物資流向報表

        Args:
            db: 資料庫會話
            start_date: 開始日期
            end_date: 結束日期
            format_type: 格式類型

        Returns:
            報表檔案的二進位資料
        """
        # 收集物資流向資料
        report_data = self._collect_supply_flow_data(db, start_date, end_date)

        if format_type.lower() == "pdf":
            return self._generate_pdf_report(report_data, "物資流向報表")
        elif format_type.lower() == "csv":
            return self._generate_csv_report(report_data)
        elif format_type.lower() == "excel":
            return self._generate_excel_report(report_data, "物資流向報表")
        else:
            raise ValueError(f"不支援的格式類型: {format_type}")

    def generate_system_usage_report(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        format_type: str = "pdf"
    ) -> bytes:
        """
        生成系統使用統計報表

        Args:
            db: 資料庫會話
            start_date: 開始日期
            end_date: 結束日期
            format_type: 格式類型

        Returns:
            報表檔案的二進位資料
        """
        # 收集系統使用資料
        report_data = self._collect_system_usage_data(db, start_date, end_date)

        if format_type.lower() == "pdf":
            return self._generate_pdf_report(report_data, "系統使用統計報表")
        elif format_type.lower() == "csv":
            return self._generate_csv_report(report_data)
        elif format_type.lower() == "excel":
            return self._generate_excel_report(report_data, "系統使用統計報表")
        else:
            raise ValueError(f"不支援的格式類型: {format_type}")

    def generate_comprehensive_analysis_report(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        format_type: str = "pdf"
    ) -> bytes:
        """
        生成綜合分析報表

        Args:
            db: 資料庫會話
            start_date: 開始日期
            end_date: 結束日期
            format_type: 格式類型

        Returns:
            報表檔案的二進位資料
        """
        # 收集綜合分析資料
        report_data = self._collect_comprehensive_analysis_data(db, start_date, end_date)

        if format_type.lower() == "pdf":
            return self._generate_pdf_report(report_data, "綜合分析報表")
        elif format_type.lower() == "csv":
            return self._generate_csv_report(report_data)
        elif format_type.lower() == "excel":
            return self._generate_excel_report(report_data, "綜合分析報表")
        else:
            raise ValueError(f"不支援的格式類型: {format_type}")

    def export_data_by_type(
        self,
        db: Session,
        data_type: str,
        start_date: datetime,
        end_date: datetime,
        format_type: str = "csv",
        filters: dict = None
    ) -> bytes:
        """
        按類型匯出資料

        Args:
            db: 資料庫會話
            data_type: 資料類型 (tasks, needs, supplies, users, logs)
            start_date: 開始日期
            end_date: 結束日期
            format_type: 格式類型
            filters: 額外篩選條件

        Returns:
            匯出檔案的二進位資料
        """
        # 根據資料類型收集資料
        if data_type == "tasks":
            data = self._export_tasks_data(db, start_date, end_date, filters)
        elif data_type == "needs":
            data = self._export_needs_data(db, start_date, end_date, filters)
        elif data_type == "supplies":
            data = self._export_supplies_data(db, start_date, end_date, filters)
        elif data_type == "users":
            data = self._export_users_data(db, start_date, end_date, filters)
        elif data_type == "logs":
            data = self._export_logs_data(db, start_date, end_date, filters)
        else:
            raise ValueError(f"不支援的資料類型: {data_type}")

        # 生成匯出檔案
        if format_type.lower() == "csv":
            return self._generate_csv_export(data)
        elif format_type.lower() == "excel":
            return self._generate_excel_export(data)
        elif format_type.lower() == "json":
            return self._generate_json_export(data)
        else:
            raise ValueError(f"不支援的格式類型: {format_type}")

    def _collect_disaster_relief_data(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """收集救災活動資料"""
        # 使用監控服務獲取統計資料
        days = (end_date - start_date).days
        disaster_progress = monitoring_service.get_disaster_relief_progress(db, days)
        task_completion = monitoring_service.get_task_completion_statistics(db, days)
        supply_flow = monitoring_service.get_supply_flow_monitoring(db, days)

        # 詳細任務資料
        tasks = db.query(Task).filter(
            Task.created_at >= start_date,
            Task.created_at <= end_date
        ).all()

        task_details = []
        for task in tasks:
            task_details.append({
                "任務ID": str(task.id),
                "任務標題": task.title,
                "任務類型": task.task_type,
                "狀態": task.status,
                "優先級": task.priority_level,
                "所需志工數": task.required_volunteers,
                "創建時間": task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "更新時間": task.updated_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        # 詳細需求資料
        needs = db.query(Need).filter(
            Need.created_at >= start_date,
            Need.created_at <= end_date
        ).all()

        need_details = []
        for need in needs:
            need_details.append({
                "需求ID": str(need.id),
                "需求標題": need.title,
                "需求類型": need.need_type,
                "狀態": need.status,
                "緊急程度": need.urgency_level,
                "創建時間": need.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "更新時間": need.updated_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        return {
            "report_title": "救災活動報表",
            "period": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "days": days
            },
            "summary": {
                "disaster_progress": disaster_progress,
                "task_completion": task_completion,
                "supply_flow": supply_flow
            },
            "details": {
                "tasks": task_details,
                "needs": need_details
            },
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _collect_task_completion_data(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """收集任務完成資料"""
        # 獲取任務完成統計
        days = (end_date - start_date).days
        task_stats = monitoring_service.get_task_completion_statistics(db, days)

        # 詳細的任務認領和完成資料
        task_claims = db.query(TaskClaim).join(Task).filter(
            TaskClaim.claimed_at >= start_date,
            TaskClaim.claimed_at <= end_date
        ).all()

        claim_details = []
        for claim in task_claims:
            task = claim.task
            user = db.query(User).filter(User.id == claim.user_id).first()

            completion_time = None
            if claim.completed_at and claim.claimed_at:
                duration = claim.completed_at - claim.claimed_at
                completion_time = round(duration.total_seconds() / 3600, 2)  # 小時

            claim_details.append({
                "任務ID": str(task.id),
                "任務標題": task.title,
                "任務類型": task.task_type,
                "志工姓名": user.name if user else "未知",
                "志工角色": user.role if user else "未知",
                "認領時間": claim.claimed_at.strftime("%Y-%m-%d %H:%M:%S"),
                "開始時間": claim.started_at.strftime("%Y-%m-%d %H:%M:%S") if claim.started_at else "",
                "完成時間": claim.completed_at.strftime("%Y-%m-%d %H:%M:%S") if claim.completed_at else "",
                "完成耗時(小時)": completion_time or "",
                "狀態": claim.status,
                "備註": claim.notes or ""
            })

        return {
            "report_title": "任務完成報表",
            "period": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "days": days
            },
            "summary": task_stats,
            "details": {
                "task_claims": claim_details
            },
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _collect_supply_flow_data(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """收集物資流向資料"""
        # 獲取物資流向統計
        days = (end_date - start_date).days
        supply_stats = monitoring_service.get_supply_flow_monitoring(db, days)

        # 詳細的物資預訂資料
        reservations = db.query(SupplyReservation).filter(
            SupplyReservation.reserved_at >= start_date,
            SupplyReservation.reserved_at <= end_date
        ).all()

        reservation_details = []
        for reservation in reservations:
            station = db.query(SupplyStation).filter(SupplyStation.id == reservation.station_id).first()
            user = db.query(User).filter(User.id == reservation.user_id).first()

            # 獲取預訂物資明細
            items = db.query(ReservationItem).filter(
                ReservationItem.reservation_id == reservation.id
            ).all()

            item_list = []
            for item in items:
                item_list.append(f"{item.supply_type}({item.confirmed_quantity or item.requested_quantity})")

            reservation_details.append({
                "預訂ID": str(reservation.id),
                "物資站點": station.name if station else "未知",
                "預訂者": user.name if user else "未知",
                "預訂物資": ", ".join(item_list),
                "狀態": reservation.status,
                "預訂時間": reservation.reserved_at.strftime("%Y-%m-%d %H:%M:%S"),
                "確認時間": reservation.confirmed_at.strftime("%Y-%m-%d %H:%M:%S") if reservation.confirmed_at else "",
                "領取時間": reservation.picked_up_at.strftime("%Y-%m-%d %H:%M:%S") if reservation.picked_up_at else "",
                "配送時間": reservation.delivered_at.strftime("%Y-%m-%d %H:%M:%S") if reservation.delivered_at else "",
                "備註": reservation.notes or ""
            })

        return {
            "report_title": "物資流向報表",
            "period": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "days": days
            },
            "summary": supply_stats,
            "details": {
                "reservations": reservation_details
            },
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _collect_system_usage_data(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """收集系統使用資料"""
        # 用戶活動統計
        total_users = db.query(User).count()
        new_users = db.query(User).filter(
            User.created_at >= start_date,
            User.created_at <= end_date
        ).count()

        # 用戶角色分布
        user_role_stats = db.query(
            User.role,
            func.count(User.id).label('count')
        ).group_by(User.role).all()

        role_distribution = {role: count for role, count in user_role_stats}

        # 系統活動日誌統計
        hours = int((end_date - start_date).total_seconds() / 3600)
        activity_log = monitoring_service.get_system_activity_log(db, hours, 1000)

        # 詳細的用戶活動資料
        active_users = db.query(
            User.id,
            User.name,
            User.role,
            User.created_at,
            func.count(SystemLog.id).label('activity_count')
        ).outerjoin(
            SystemLog, User.id == SystemLog.user_id
        ).filter(
            or_(
                SystemLog.created_at.between(start_date, end_date),
                SystemLog.created_at.is_(None)
            )
        ).group_by(User.id, User.name, User.role, User.created_at).all()

        user_activity_details = []
        for user_id, name, role, created_at, activity_count in active_users:
            user_activity_details.append({
                "用戶ID": str(user_id),
                "用戶姓名": name,
                "用戶角色": role,
                "註冊時間": created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "活動次數": activity_count or 0
            })

        return {
            "report_title": "系統使用統計報表",
            "period": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "days": (end_date - start_date).days
            },
            "summary": {
                "total_users": total_users,
                "new_users": new_users,
                "role_distribution": role_distribution,
                "activity_summary": activity_log["summary"],
                "activity_counts": activity_log["activity_counts"]
            },
            "details": {
                "user_activities": user_activity_details
            },
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _export_tasks_data(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        filters: dict = None
    ) -> List[Dict[str, Any]]:
        """匯出任務資料"""
        query = db.query(Task).filter(
            Task.created_at >= start_date,
            Task.created_at <= end_date
        )

        # 應用篩選條件
        if filters:
            if 'status' in filters:
                query = query.filter(Task.status == filters['status'])
            if 'task_type' in filters:
                query = query.filter(Task.task_type == filters['task_type'])
            if 'creator_id' in filters:
                query = query.filter(Task.creator_id == filters['creator_id'])

        tasks = query.all()

        task_data = []
        for task in tasks:
            creator = db.query(User).filter(User.id == task.creator_id).first()

            task_data.append({
                "任務ID": str(task.id),
                "任務標題": task.title,
                "任務描述": task.description,
                "任務類型": task.task_type,
                "狀態": task.status,
                "優先級": task.priority_level,
                "所需志工數": task.required_volunteers,
                "創建者": creator.name if creator else "未知",
                "創建者角色": creator.role if creator else "未知",
                "地址": task.location_data.get('address', '') if task.location_data else '',
                "座標": f"{task.location_data.get('coordinates', {}).get('lat', '')},{task.location_data.get('coordinates', {}).get('lng', '')}" if task.location_data and task.location_data.get('coordinates') else '',
                "截止時間": task.deadline.strftime("%Y-%m-%d %H:%M:%S") if task.deadline else "",
                "審核狀態": task.approval_status,
                "創建時間": task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "更新時間": task.updated_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        return task_data

    def _export_needs_data(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        filters: dict = None
    ) -> List[Dict[str, Any]]:
        """匯出需求資料"""
        query = db.query(Need).filter(
            Need.created_at >= start_date,
            Need.created_at <= end_date
        )

        # 應用篩選條件
        if filters:
            if 'status' in filters:
                query = query.filter(Need.status == filters['status'])
            if 'need_type' in filters:
                query = query.filter(Need.need_type == filters['need_type'])
            if 'reporter_id' in filters:
                query = query.filter(Need.reporter_id == filters['reporter_id'])

        needs = query.all()

        need_data = []
        for need in needs:
            reporter = db.query(User).filter(User.id == need.reporter_id).first()
            assigned_user = db.query(User).filter(User.id == need.assigned_to).first() if need.assigned_to else None

            need_data.append({
                "需求ID": str(need.id),
                "需求標題": need.title,
                "需求描述": need.description,
                "需求類型": need.need_type,
                "狀態": need.status,
                "緊急程度": need.urgency_level,
                "報告者": reporter.name if reporter else "未知",
                "報告者角色": reporter.role if reporter else "未知",
                "分配給": assigned_user.name if assigned_user else "",
                "地址": need.location_data.get('address', '') if need.location_data else '',
                "座標": f"{need.location_data.get('coordinates', {}).get('lat', '')},{need.location_data.get('coordinates', {}).get('lng', '')}" if need.location_data and need.location_data.get('coordinates') else '',
                "需求詳情": str(need.requirements) if need.requirements else '',
                "聯絡資訊": str(need.contact_info) if need.contact_info else '',
                "分配時間": need.assigned_at.strftime("%Y-%m-%d %H:%M:%S") if need.assigned_at else "",
                "解決時間": need.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if need.resolved_at else "",
                "創建時間": need.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "更新時間": need.updated_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        return need_data

    def _export_supplies_data(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        filters: dict = None
    ) -> List[Dict[str, Any]]:
        """匯出物資資料"""
        query = db.query(SupplyReservation).filter(
            SupplyReservation.reserved_at >= start_date,
            SupplyReservation.reserved_at <= end_date
        )

        # 應用篩選條件
        if filters:
            if 'status' in filters:
                query = query.filter(SupplyReservation.status == filters['status'])
            if 'station_id' in filters:
                query = query.filter(SupplyReservation.station_id == filters['station_id'])
            if 'user_id' in filters:
                query = query.filter(SupplyReservation.user_id == filters['user_id'])

        reservations = query.all()

        supply_data = []
        for reservation in reservations:
            station = db.query(SupplyStation).filter(SupplyStation.id == reservation.station_id).first()
            user = db.query(User).filter(User.id == reservation.user_id).first()

            # 獲取預訂物資明細
            items = db.query(ReservationItem).filter(
                ReservationItem.reservation_id == reservation.id
            ).all()

            item_details = []
            for item in items:
                item_details.append({
                    "物資類型": item.supply_type,
                    "請求數量": item.requested_quantity,
                    "確認數量": item.confirmed_quantity or 0,
                    "備註": item.notes or ""
                })

            supply_data.append({
                "預訂ID": str(reservation.id),
                "物資站點": station.name if station else "未知",
                "站點地址": station.address if station else "",
                "預訂者": user.name if user else "未知",
                "預訂者角色": user.role if user else "未知",
                "狀態": reservation.status,
                "物資明細": str(item_details),
                "任務ID": str(reservation.task_id) if reservation.task_id else "",
                "需求ID": str(reservation.need_id) if reservation.need_id else "",
                "預訂時間": reservation.reserved_at.strftime("%Y-%m-%d %H:%M:%S"),
                "確認時間": reservation.confirmed_at.strftime("%Y-%m-%d %H:%M:%S") if reservation.confirmed_at else "",
                "領取時間": reservation.picked_up_at.strftime("%Y-%m-%d %H:%M:%S") if reservation.picked_up_at else "",
                "配送時間": reservation.delivered_at.strftime("%Y-%m-%d %H:%M:%S") if reservation.delivered_at else "",
                "備註": reservation.notes or ""
            })

        return supply_data

    def _export_users_data(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        filters: dict = None
    ) -> List[Dict[str, Any]]:
        """匯出用戶資料"""
        query = db.query(User).filter(
            User.created_at >= start_date,
            User.created_at <= end_date
        )

        # 應用篩選條件
        if filters:
            if 'role' in filters:
                query = query.filter(User.role == filters['role'])
            if 'is_approved' in filters:
                query = query.filter(User.is_approved == filters['is_approved'])

        users = query.all()

        user_data = []
        for user in users:
            # 計算用戶活動統計
            task_count = db.query(Task).filter(Task.creator_id == user.id).count()
            need_count = db.query(Need).filter(Need.reporter_id == user.id).count()
            claim_count = db.query(TaskClaim).filter(TaskClaim.user_id == user.id).count()

            user_data.append({
                "用戶ID": str(user.id),
                "用戶姓名": user.name,
                "電子郵件": user.email,
                "電話": user.phone or "",
                "用戶角色": user.role,
                "審核狀態": "已審核" if user.is_approved else "待審核",
                "創建任務數": task_count,
                "報告需求數": need_count,
                "認領任務數": claim_count,
                "個人資料": str(user.profile_data) if user.profile_data else "",
                "註冊時間": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "更新時間": user.updated_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        return user_data

    def _export_logs_data(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        filters: dict = None
    ) -> List[Dict[str, Any]]:
        """匯出系統日誌資料"""
        query = db.query(SystemLog).filter(
            SystemLog.created_at >= start_date,
            SystemLog.created_at <= end_date
        )

        # 應用篩選條件
        if filters:
            if 'action' in filters:
                query = query.filter(SystemLog.action == filters['action'])
            if 'resource_type' in filters:
                query = query.filter(SystemLog.resource_type == filters['resource_type'])
            if 'user_id' in filters:
                query = query.filter(SystemLog.user_id == filters['user_id'])

        # 限制記錄數量以避免過大的匯出檔案
        logs = query.order_by(SystemLog.created_at.desc()).limit(10000).all()

        log_data = []
        for log in logs:
            user = db.query(User).filter(User.id == log.user_id).first() if log.user_id else None

            log_data.append({
                "日誌ID": str(log.id),
                "用戶": user.name if user else "系統",
                "用戶角色": user.role if user else "",
                "操作": log.action,
                "資源類型": log.resource_type or "",
                "資源ID": log.resource_id or "",
                "詳細資訊": str(log.details) if log.details else "",
                "IP地址": log.ip_address or "",
                "用戶代理": log.user_agent or "",
                "創建時間": log.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        return log_data

    def _generate_csv_export(self, data: List[Dict[str, Any]]) -> bytes:
        """生成CSV匯出檔案"""
        if not data:
            return b""

        output = io.StringIO()

        # 取得欄位名稱
        fieldnames = list(data[0].keys())

        # 寫入CSV資料
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

        # 轉換為bytes
        csv_content = output.getvalue()
        return csv_content.encode('utf-8-sig')  # 使用BOM以支援Excel中文顯示

    def _generate_excel_export(self, data: List[Dict[str, Any]]) -> bytes:
        """生成Excel匯出檔案"""
        if not data:
            return b""

        output = io.BytesIO()

        # 建立DataFrame並匯出為Excel
        df = pd.DataFrame(data)
        df.to_excel(output, index=False, engine='openpyxl')

        output.seek(0)
        return output.getvalue()

    def _generate_json_export(self, data: List[Dict[str, Any]]) -> bytes:
        """生成JSON匯出檔案"""
        import json

        json_content = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        return json_content.encode('utf-8')

    def _collect_comprehensive_analysis_data(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """收集綜合分析資料"""
        days = (end_date - start_date).days

        # 獲取各種統計資料
        disaster_progress = monitoring_service.get_disaster_relief_progress(db, days)
        task_completion = monitoring_service.get_task_completion_statistics(db, days)
        supply_flow = monitoring_service.get_supply_flow_monitoring(db, days)

        # 用戶活動分析
        total_users = db.query(User).count()
        active_users = db.query(User.id).join(
            SystemLog, User.id == SystemLog.user_id
        ).filter(
            SystemLog.created_at >= start_date,
            SystemLog.created_at <= end_date
        ).distinct().count()

        # 地理分布分析
        task_locations = db.query(Task.location_data).filter(
            Task.created_at >= start_date,
            Task.created_at <= end_date,
            Task.location_data.isnot(None)
        ).all()

        location_analysis = {
            "total_locations": len(task_locations),
            "unique_addresses": len(set([
                loc.location_data.get('address', '')
                for loc in task_locations
                if loc.location_data and loc.location_data.get('address')
            ]))
        }

        # 時間趨勢分析
        daily_stats = []
        current_date = start_date
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)

            daily_tasks = db.query(Task).filter(
                Task.created_at >= current_date,
                Task.created_at < next_date
            ).count()

            daily_needs = db.query(Need).filter(
                Need.created_at >= current_date,
                Need.created_at < next_date
            ).count()

            daily_stats.append({
                "日期": current_date.strftime("%Y-%m-%d"),
                "新增任務": daily_tasks,
                "新增需求": daily_needs,
                "總活動": daily_tasks + daily_needs
            })

            current_date = next_date

        return {
            "report_title": "綜合分析報表",
            "period": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "days": days
            },
            "summary": {
                "disaster_progress": disaster_progress,
                "task_completion": task_completion,
                "supply_flow": supply_flow,
                "user_activity": {
                    "total_users": total_users,
                    "active_users": active_users,
                    "activity_rate": round((active_users / total_users * 100), 2) if total_users > 0 else 0
                },
                "location_analysis": location_analysis
            },
            "details": {
                "daily_trends": daily_stats
            },
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _generate_pdf_report(self, report_data: Dict[str, Any], title: str) -> bytes:
        """生成PDF報表"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []

        # 標題
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 12))

        # 報表資訊
        period_info = f"報表期間: {report_data['period']['start_date']} 至 {report_data['period']['end_date']}"
        story.append(Paragraph(period_info, self.styles['Normal']))

        generated_info = f"生成時間: {report_data['generated_at']}"
        story.append(Paragraph(generated_info, self.styles['Normal']))
        story.append(Spacer(1, 20))

        # 摘要資訊
        story.append(Paragraph("摘要統計", self.heading_style))

        if 'summary' in report_data:
            summary = report_data['summary']

            # 根據報表類型顯示不同的摘要資訊
            if 'disaster_progress' in summary:
                # 救災活動報表摘要
                dp = summary['disaster_progress']
                summary_data = [
                    ['項目', '數值'],
                    ['總任務數', str(dp['task_progress']['total_tasks'])],
                    ['已完成任務', str(dp['task_progress']['completed_tasks'])],
                    ['任務完成率', f"{dp['task_progress']['completion_rate']}%"],
                    ['總需求數', str(dp['need_progress']['total_needs'])],
                    ['已解決需求', str(dp['need_progress']['resolved_needs'])],
                    ['需求解決率', f"{dp['need_progress']['resolution_rate']}%"],
                    ['整體完成率', f"{dp['overall_completion']['overall_completion_rate']}%"]
                ]
            elif 'overall' in summary:
                # 任務完成報表摘要
                overall = summary['overall']
                summary_data = [
                    ['項目', '數值'],
                    ['總任務數', str(overall['total_tasks'])],
                    ['已完成任務', str(overall['completed_tasks'])],
                    ['完成率', f"{overall['completion_rate']}%"],
                    ['平均完成時間', f"{summary['average_completion_time_hours']}小時"],
                    ['活躍志工數', str(summary['volunteer_efficiency']['active_volunteers'])]
                ]
            else:
                # 其他報表的通用摘要
                summary_data = [['項目', '數值']]
                for key, value in summary.items():
                    if isinstance(value, (int, float, str)):
                        summary_data.append([str(key), str(value)])

            summary_table = Table(summary_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 20))

        # 詳細資料
        if 'details' in report_data:
            story.append(Paragraph("詳細資料", self.heading_style))

            details = report_data['details']
            for section_name, section_data in details.items():
                if section_data and len(section_data) > 0:
                    # 取得第一筆資料的鍵作為表頭
                    headers = list(section_data[0].keys())

                    # 建立表格資料
                    table_data = [headers]
                    for row in section_data[:50]:  # 限制顯示前50筆
                        table_data.append([str(row.get(header, '')) for header in headers])

                    # 建立表格
                    detail_table = Table(table_data)
                    detail_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))

                    story.append(Paragraph(f"{section_name.title()}", self.styles['Heading3']))
                    story.append(detail_table)
                    story.append(Spacer(1, 12))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def _generate_csv_report(self, report_data: Dict[str, Any]) -> bytes:
        """生成CSV報表"""
        output = io.StringIO()

        # 寫入報表標題和基本資訊
        output.write(f"# {report_data['report_title']}\n")
        output.write(f"# 報表期間: {report_data['period']['start_date']} 至 {report_data['period']['end_date']}\n")
        output.write(f"# 生成時間: {report_data['generated_at']}\n")
        output.write("\n")

        # 寫入詳細資料
        if 'details' in report_data:
            details = report_data['details']
            for section_name, section_data in details.items():
                if section_data and len(section_data) > 0:
                    output.write(f"# {section_name.upper()}\n")

                    # 取得欄位名稱
                    fieldnames = list(section_data[0].keys())

                    # 寫入CSV資料
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(section_data)
                    output.write("\n")

        # 轉換為bytes
        csv_content = output.getvalue()
        return csv_content.encode('utf-8-sig')  # 使用BOM以支援Excel中文顯示

    def _generate_excel_report(self, report_data: Dict[str, Any], title: str) -> bytes:
        """生成Excel報表"""
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 摘要工作表
            summary_data = []
            summary_data.append(['報表標題', report_data['report_title']])
            summary_data.append(['報表期間', f"{report_data['period']['start_date']} 至 {report_data['period']['end_date']}"])
            summary_data.append(['生成時間', report_data['generated_at']])
            summary_data.append(['', ''])  # 空行

            # 添加摘要統計
            if 'summary' in report_data:
                summary_data.append(['摘要統計', ''])
                summary = report_data['summary']

                def flatten_dict(d, parent_key='', sep='_'):
                    """扁平化字典"""
                    items = []
                    for k, v in d.items():
                        new_key = f"{parent_key}{sep}{k}" if parent_key else k
                        if isinstance(v, dict):
                            items.extend(flatten_dict(v, new_key, sep=sep).items())
                        else:
                            items.append((new_key, v))
                    return dict(items)

                flat_summary = flatten_dict(summary)
                for key, value in flat_summary.items():
                    if isinstance(value, (int, float, str)):
                        summary_data.append([key, value])

            summary_df = pd.DataFrame(summary_data, columns=['項目', '數值'])
            summary_df.to_excel(writer, sheet_name='摘要', index=False)

            # 詳細資料工作表
            if 'details' in report_data:
                details = report_data['details']
                for section_name, section_data in details.items():
                    if section_data and len(section_data) > 0:
                        df = pd.DataFrame(section_data)
                        sheet_name = section_name[:31]  # Excel工作表名稱限制31字元
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

        output.seek(0)
        return output.getvalue()

    def _generate_csv_export(self, data: List[Dict[str, Any]]) -> bytes:
        """生成CSV匯出檔案"""
        if not data:
            return b""

        output = io.StringIO()

        # 取得欄位名稱
        fieldnames = list(data[0].keys())

        # 寫入CSV資料
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

        # 轉換為bytes
        csv_content = output.getvalue()
        return csv_content.encode('utf-8-sig')  # 使用BOM以支援Excel中文顯示

    def _generate_excel_export(self, data: List[Dict[str, Any]]) -> bytes:
        """生成Excel匯出檔案"""
        if not data:
            return b""

        output = io.BytesIO()

        # 建立DataFrame並匯出為Excel
        df = pd.DataFrame(data)
        df.to_excel(output, index=False, engine='openpyxl')

        output.seek(0)
        return output.getvalue()

    def _generate_json_export(self, data: List[Dict[str, Any]]) -> bytes:
        """生成JSON匯出檔案"""
        json_content = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        return json_content.encode('utf-8')


# 建立全域實例
reporting_service = ReportingService()
