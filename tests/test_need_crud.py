"""
需求 CRUD 操作測試
"""
import pytest
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.need import Need, NeedType as NeedTypeModel, NeedStatus as NeedStatusModel, NeedAssignment
from app.crud.need import need_crud
from app.schemas.need import (
    NeedCreate, NeedUpdate, NeedSearchQuery, NeedStatusUpdate,
    NeedAssignment as NeedAssignmentSchema, LocationData, ContactInfo, NeedRequirements
)
from app.utils.constants import UserRole, NeedType, NeedStatus
from datetime import datetime


class TestNeedCRUD:
    """需求 CRUD 測試類"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self, db_session: Session):
        """每個測試方法前的設置"""
        self.db = db_session
        
        # 建立測試用戶
        self.victim_user = User(
            email="victim@test.com",
            name="測試受災戶",
            password_hash="hashed_password",
            role=UserRole.VICTIM.value,
            is_approved=True
        )
        self.volunteer_user = User(
            email="volunteer@test.com",
            name="測試志工",
            password_hash="hashed_password",
            role=UserRole.VOLUNTEER.value,
            is_approved=True
        )
        
        self.db.add_all([self.victim_user, self.volunteer_user])
        self.db.commit()
        
        # 建立需求類型和狀態
        need_types = [
            NeedTypeModel(type="food", display_name="食物需求"),
            NeedTypeModel(type="medical", display_name="醫療需求"),
            NeedTypeModel(type="shelter", display_name="住宿需求")
        ]
        need_statuses = [
            NeedStatusModel(status="open", display_name="待處理"),
            NeedStatusModel(status="assigned", display_name="已分配"),
            NeedStatusModel(status="resolved", display_name="已解決")
        ]
        
        self.db.add_all(need_types + need_statuses)
        self.db.commit()
    
    def test_create_need_success(self):
        """測試成功建立需求"""
        need_data = NeedCreate(
            title="緊急食物需求",
            description="家中食物短缺，需要緊急補給",
            need_type=NeedType.FOOD,
            location_data=LocationData(
                address="花蓮縣光復鄉中正路123號",
                coordinates={"lat": 23.5731, "lng": 121.4208},
                details="靠近光復國小"
            ),
            requirements=NeedRequirements(
                items=[
                    {"name": "白米", "quantity": 5, "unit": "公斤"},
                    {"name": "罐頭", "quantity": 10, "unit": "罐"}
                ],
                people_count=4,
                special_needs="家中有老人和小孩"
            ),
            urgency_level=4,
            contact_info=ContactInfo(
                phone="0912345678",
                notes="請於上午聯絡"
            )
        )
        
        need = need_crud.create(self.db, need_data, self.victim_user.id)
        
        assert need.id is not None
        assert need.title == need_data.title
        assert need.need_type == need_data.need_type.value
        assert need.status == NeedStatus.OPEN.value
        assert need.reporter_id == self.victim_user.id
        assert need.urgency_level == 4
        assert need.location_data["address"] == "花蓮縣光復鄉中正路123號"
        assert need.requirements["people_count"] == 4
        assert need.contact_info["phone"] == "0912345678"
    
    def test_get_need_by_id(self):
        """測試根據 ID 取得需求"""
        # 先建立需求
        need_data = NeedCreate(
            title="測試需求",
            description="測試描述",
            need_type=NeedType.MEDICAL,
            location_data=LocationData(address="測試地址"),
            requirements=NeedRequirements(people_count=1),
            urgency_level=2
        )
        
        created_need = need_crud.create(self.db, need_data, str(self.victim_user.id))
        
        # 取得需求
        retrieved_need = need_crud.get_by_id(self.db, str(created_need.id))
        
        assert retrieved_need is not None
        assert retrieved_need.id == created_need.id
        assert retrieved_need.title == need_data.title
        assert retrieved_need.reporter is not None
        assert retrieved_need.reporter.name == self.victim_user.name
    
    def test_get_need_by_id_not_found(self):
        """測試取得不存在的需求"""
        need = need_crud.get_by_id(self.db, "non-existent-id")
        assert need is None
    
    def test_update_need_success(self):
        """測試成功更新需求"""
        # 先建立需求
        need_data = NeedCreate(
            title="原始標題",
            description="原始描述",
            need_type=NeedType.FOOD,
            location_data=LocationData(address="原始地址"),
            requirements=NeedRequirements(people_count=1),
            urgency_level=1
        )
        
        need = need_crud.create(self.db, need_data, str(self.victim_user.id))
        
        # 更新需求
        update_data = NeedUpdate(
            title="更新後標題",
            urgency_level=5
        )
        
        updated_need = need_crud.update(self.db, str(need.id), update_data)
        
        assert updated_need is not None
        assert updated_need.title == "更新後標題"
        assert updated_need.urgency_level == 5
        assert updated_need.description == "原始描述"  # 未更新的欄位保持不變
    
    def test_update_need_status(self):
        """測試更新需求狀態"""
        # 先建立需求
        need_data = NeedCreate(
            title="測試需求",
            description="測試描述",
            need_type=NeedType.FOOD,
            location_data=LocationData(address="測試地址"),
            requirements=NeedRequirements(people_count=1),
            urgency_level=1
        )
        
        need = need_crud.create(self.db, need_data, str(self.victim_user.id))
        assert need.status == NeedStatus.OPEN.value
        
        # 更新狀態為已解決
        status_data = NeedStatusUpdate(
            status=NeedStatus.RESOLVED,
            notes="問題已解決"
        )
        
        updated_need = need_crud.update_status(self.db, str(need.id), status_data)
        
        assert updated_need is not None
        assert updated_need.status == NeedStatus.RESOLVED.value
        assert updated_need.resolved_at is not None
    
    def test_assign_need_to_user(self):
        """測試分配需求給用戶"""
        # 先建立需求
        need_data = NeedCreate(
            title="測試需求",
            description="測試描述",
            need_type=NeedType.FOOD,
            location_data=LocationData(address="測試地址"),
            requirements=NeedRequirements(people_count=1),
            urgency_level=1
        )
        
        need = need_crud.create(self.db, need_data, str(self.victim_user.id))
        
        # 分配給志工
        assignment_data = NeedAssignmentSchema(
            assigned_to=str(self.volunteer_user.id),
            notes="分配給經驗豐富的志工"
        )
        
        assigned_need = need_crud.assign_to_user(self.db, str(need.id), assignment_data)
        
        assert assigned_need is not None
        assert assigned_need.assigned_to == self.volunteer_user.id
        assert assigned_need.status == NeedStatus.ASSIGNED.value
        assert assigned_need.assigned_at is not None
        
        # 檢查分配記錄是否建立
        assignments = need_crud.get_assignments_by_need(self.db, str(need.id))
        assert len(assignments) == 1
        assert assignments[0].user_id == self.volunteer_user.id
        assert assignments[0].notes == "分配給經驗豐富的志工"
    
    def test_assign_need_invalid_user(self):
        """測試分配需求給不存在的用戶"""
        # 先建立需求
        need_data = NeedCreate(
            title="測試需求",
            description="測試描述",
            need_type=NeedType.FOOD,
            location_data=LocationData(address="測試地址"),
            requirements=NeedRequirements(people_count=1),
            urgency_level=1
        )
        
        need = need_crud.create(self.db, need_data, str(self.victim_user.id))
        
        # 嘗試分配給不存在的用戶
        assignment_data = NeedAssignmentSchema(
            assigned_to="non-existent-user-id"
        )
        
        with pytest.raises(ValueError, match="指定的用戶不存在"):
            need_crud.assign_to_user(self.db, str(need.id), assignment_data)
    
    def test_unassign_need(self):
        """測試取消需求分配"""
        # 先建立並分配需求
        need_data = NeedCreate(
            title="測試需求",
            description="測試描述",
            need_type=NeedType.FOOD,
            location_data=LocationData(address="測試地址"),
            requirements=NeedRequirements(people_count=1),
            urgency_level=1
        )
        
        need = need_crud.create(self.db, need_data, str(self.victim_user.id))
        
        assignment_data = NeedAssignmentSchema(
            assigned_to=str(self.volunteer_user.id)
        )
        need_crud.assign_to_user(self.db, str(need.id), assignment_data)
        
        # 取消分配
        unassigned_need = need_crud.unassign(self.db, str(need.id))
        
        assert unassigned_need is not None
        assert unassigned_need.assigned_to is None
        assert unassigned_need.assigned_at is None
        assert unassigned_need.status == NeedStatus.OPEN.value
    
    def test_delete_need(self):
        """測試刪除需求"""
        # 先建立需求
        need_data = NeedCreate(
            title="測試需求",
            description="測試描述",
            need_type=NeedType.FOOD,
            location_data=LocationData(address="測試地址"),
            requirements=NeedRequirements(people_count=1),
            urgency_level=1
        )
        
        need = need_crud.create(self.db, need_data, str(self.victim_user.id))
        need_id = str(need.id)
        
        # 刪除需求
        success = need_crud.delete(self.db, need_id)
        assert success is True
        
        # 確認需求已被刪除
        deleted_need = need_crud.get_by_id(self.db, need_id)
        assert deleted_need is None
    
    def test_get_multi_with_search(self):
        """測試搜尋和篩選需求列表"""
        # 建立多個測試需求
        needs_data = [
            NeedCreate(
                title="食物需求A",
                description="需要白米",
                need_type=NeedType.FOOD,
                location_data=LocationData(address="地址A"),
                requirements=NeedRequirements(people_count=2),
                urgency_level=3
            ),
            NeedCreate(
                title="醫療需求B",
                description="需要醫療協助",
                need_type=NeedType.MEDICAL,
                location_data=LocationData(address="地址B"),
                requirements=NeedRequirements(people_count=1),
                urgency_level=5
            ),
            NeedCreate(
                title="食物需求C",
                description="需要罐頭",
                need_type=NeedType.FOOD,
                location_data=LocationData(address="地址C"),
                requirements=NeedRequirements(people_count=3),
                urgency_level=2
            )
        ]
        
        for need_data in needs_data:
            need_crud.create(self.db, need_data, str(self.victim_user.id))
        
        # 測試按類型搜尋
        search_query = NeedSearchQuery(need_type=NeedType.FOOD)
        food_needs = need_crud.get_multi(self.db, search_query=search_query)
        assert len(food_needs) == 2
        assert all(need.need_type == NeedType.FOOD.value for need in food_needs)
        
        # 測試按標題搜尋
        search_query = NeedSearchQuery(title="醫療")
        medical_needs = need_crud.get_multi(self.db, search_query=search_query)
        assert len(medical_needs) == 1
        assert "醫療" in medical_needs[0].title
        
        # 測試按緊急程度搜尋
        search_query = NeedSearchQuery(urgency_level=5)
        urgent_needs = need_crud.get_multi(self.db, search_query=search_query)
        assert len(urgent_needs) == 1
        assert urgent_needs[0].urgency_level == 5
    
    def test_get_by_reporter(self):
        """測試取得特定報告者的需求"""
        # 建立需求
        need_data = NeedCreate(
            title="測試需求",
            description="測試描述",
            need_type=NeedType.FOOD,
            location_data=LocationData(address="測試地址"),
            requirements=NeedRequirements(people_count=1),
            urgency_level=1
        )
        
        need_crud.create(self.db, need_data, str(self.victim_user.id))
        
        # 取得報告者的需求
        reporter_needs = need_crud.get_by_reporter(self.db, str(self.victim_user.id))
        
        assert len(reporter_needs) == 1
        assert reporter_needs[0].reporter_id == self.victim_user.id
    
    def test_get_by_assignee(self):
        """測試取得特定負責人的需求"""
        # 建立並分配需求
        need_data = NeedCreate(
            title="測試需求",
            description="測試描述",
            need_type=NeedType.FOOD,
            location_data=LocationData(address="測試地址"),
            requirements=NeedRequirements(people_count=1),
            urgency_level=1
        )
        
        need = need_crud.create(self.db, need_data, str(self.victim_user.id))
        
        assignment_data = NeedAssignmentSchema(
            assigned_to=str(self.volunteer_user.id)
        )
        need_crud.assign_to_user(self.db, str(need.id), assignment_data)
        
        # 取得負責人的需求
        assignee_needs = need_crud.get_by_assignee(self.db, str(self.volunteer_user.id))
        
        assert len(assignee_needs) == 1
        assert assignee_needs[0].assigned_to == self.volunteer_user.id
    
    def test_get_open_needs(self):
        """測試取得待處理需求"""
        # 建立不同狀態的需求
        need_data = NeedCreate(
            title="待處理需求",
            description="測試描述",
            need_type=NeedType.FOOD,
            location_data=LocationData(address="測試地址"),
            requirements=NeedRequirements(people_count=1),
            urgency_level=1
        )
        
        open_need = need_crud.create(self.db, need_data, str(self.victim_user.id))
        
        # 建立已分配的需求
        assigned_need = need_crud.create(self.db, need_data, str(self.victim_user.id))
        assignment_data = NeedAssignmentSchema(
            assigned_to=str(self.volunteer_user.id)
        )
        need_crud.assign_to_user(self.db, str(assigned_need.id), assignment_data)
        
        # 取得待處理需求
        open_needs = need_crud.get_open_needs(self.db)
        
        assert len(open_needs) == 1
        assert open_needs[0].status == NeedStatus.OPEN.value
        assert open_needs[0].id == open_need.id
    
    def test_get_urgent_needs(self):
        """測試取得緊急需求"""
        # 建立不同緊急程度的需求
        urgent_data = NeedCreate(
            title="緊急需求",
            description="測試描述",
            need_type=NeedType.MEDICAL,
            location_data=LocationData(address="測試地址"),
            requirements=NeedRequirements(people_count=1),
            urgency_level=5
        )
        
        normal_data = NeedCreate(
            title="一般需求",
            description="測試描述",
            need_type=NeedType.FOOD,
            location_data=LocationData(address="測試地址"),
            requirements=NeedRequirements(people_count=1),
            urgency_level=2
        )
        
        urgent_need = need_crud.create(self.db, urgent_data, str(self.victim_user.id))
        need_crud.create(self.db, normal_data, str(self.victim_user.id))
        
        # 取得緊急需求（緊急程度 >= 4）
        urgent_needs = need_crud.get_urgent_needs(self.db, urgency_threshold=4)
        
        assert len(urgent_needs) == 1
        assert urgent_needs[0].urgency_level >= 4
        assert urgent_needs[0].id == urgent_need.id
    
    def test_get_statistics(self):
        """測試取得需求統計"""
        # 建立不同類型和狀態的需求
        needs_data = [
            (NeedType.FOOD, NeedStatus.OPEN, 3),
            (NeedType.MEDICAL, NeedStatus.OPEN, 5),
            (NeedType.FOOD, NeedStatus.ASSIGNED, 2)
        ]
        
        for need_type, status, urgency in needs_data:
            need_data = NeedCreate(
                title=f"{need_type.value}需求",
                description="測試描述",
                need_type=need_type,
                location_data=LocationData(address="測試地址"),
                requirements=NeedRequirements(people_count=1),
                urgency_level=urgency
            )
            
            need = need_crud.create(self.db, need_data, str(self.victim_user.id))
            
            if status == NeedStatus.ASSIGNED:
                assignment_data = NeedAssignmentSchema(
                    assigned_to=str(self.volunteer_user.id)
                )
                need_crud.assign_to_user(self.db, str(need.id), assignment_data)
        
        # 取得統計資料
        stats = need_crud.get_statistics(self.db)
        
        assert stats.total_needs == 3
        assert stats.needs_by_type["food"] == 2
        assert stats.needs_by_type["medical"] == 1
        assert stats.open_needs == 2
        assert stats.assigned_needs == 1
        assert stats.needs_by_urgency["3"] == 1
        assert stats.needs_by_urgency["5"] == 1
        assert stats.needs_by_urgency["2"] == 1
    
    def test_count_with_search(self):
        """測試搜尋條件下的計數"""
        # 建立多個需求
        for i in range(5):
            need_data = NeedCreate(
                title=f"需求{i}",
                description="測試描述",
                need_type=NeedType.FOOD if i % 2 == 0 else NeedType.MEDICAL,
                location_data=LocationData(address="測試地址"),
                requirements=NeedRequirements(people_count=1),
                urgency_level=i + 1
            )
            need_crud.create(self.db, need_data, str(self.victim_user.id))
        
        # 測試總計數
        total_count = need_crud.count(self.db)
        assert total_count == 5
        
        # 測試按類型計數
        search_query = NeedSearchQuery(need_type=NeedType.FOOD)
        food_count = need_crud.count(self.db, search_query=search_query)
        assert food_count == 3  # 索引 0, 2, 4
        
        # 測試按緊急程度計數
        search_query = NeedSearchQuery(urgency_level=3)
        urgent_count = need_crud.count(self.db, search_query=search_query)
        assert urgent_count == 1