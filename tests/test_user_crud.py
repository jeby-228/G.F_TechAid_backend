"""
用戶 CRUD 操作的單元測試
"""
import pytest
from sqlalchemy.orm import Session
from app.crud.user import user_crud
from app.schemas.user import UserCreate, UserUpdate, UserSearchQuery, OrganizationCreate, OrganizationUpdate
from app.utils.constants import UserRole
from app.core.security import verify_password


class TestUserCRUD:
    """用戶 CRUD 測試類"""
    
    def test_create_user_success(self, db_session: Session):
        """測試成功建立用戶"""
        user_data = UserCreate(
            email="test@example.com",
            name="測試用戶",
            password="password123",
            role=UserRole.VOLUNTEER,
            phone="0912345678"
        )
        
        user = user_crud.create(db_session, user_data)
        
        assert user.email == "test@example.com"
        assert user.name == "測試用戶"
        assert user.role == UserRole.VOLUNTEER.value
        assert user.phone == "0912345678"
        assert user.is_approved == True  # 一般志工自動通過審核
        assert verify_password("password123", user.password_hash)
    
    def test_create_user_duplicate_email(self, db_session: Session):
        """測試建立重複電子郵件的用戶"""
        user_data = UserCreate(
            email="duplicate@example.com",
            name="用戶1",
            password="password123",
            role=UserRole.VOLUNTEER
        )
        
        # 建立第一個用戶
        user_crud.create(db_session, user_data)
        
        # 嘗試建立相同電子郵件的用戶
        user_data2 = UserCreate(
            email="duplicate@example.com",
            name="用戶2",
            password="password456",
            role=UserRole.VICTIM
        )
        
        with pytest.raises(ValueError, match="電子郵件已被使用"):
            user_crud.create(db_session, user_data2)
    
    def test_create_unofficial_org_user(self, db_session: Session):
        """測試建立非正式組織用戶（需要審核）"""
        user_data = UserCreate(
            email="unofficial@example.com",
            name="非正式組織",
            password="password123",
            role=UserRole.UNOFFICIAL_ORG
        )
        
        user = user_crud.create(db_session, user_data)
        
        assert user.role == UserRole.UNOFFICIAL_ORG.value
        assert user.is_approved == False  # 非正式組織需要審核
    
    def test_get_by_email(self, db_session: Session):
        """測試根據電子郵件取得用戶"""
        user_data = UserCreate(
            email="findme@example.com",
            name="找我",
            password="password123",
            role=UserRole.VOLUNTEER
        )
        
        created_user = user_crud.create(db_session, user_data)
        found_user = user_crud.get_by_email(db_session, "findme@example.com")
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == "findme@example.com"
    
    def test_get_by_id(self, db_session: Session):
        """測試根據 ID 取得用戶"""
        user_data = UserCreate(
            email="findbyid@example.com",
            name="根據ID找我",
            password="password123",
            role=UserRole.VOLUNTEER
        )
        
        created_user = user_crud.create(db_session, user_data)
        found_user = user_crud.get_by_id(db_session, str(created_user.id))
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == "findbyid@example.com"
    
    def test_update_user(self, db_session: Session):
        """測試更新用戶資料"""
        user_data = UserCreate(
            email="update@example.com",
            name="原始名稱",
            password="password123",
            role=UserRole.VOLUNTEER,
            phone="0912345678"
        )
        
        user = user_crud.create(db_session, user_data)
        
        update_data = UserUpdate(
            name="更新後名稱",
            phone="0987654321"
        )
        
        updated_user = user_crud.update(db_session, str(user.id), update_data)
        
        assert updated_user is not None
        assert updated_user.name == "更新後名稱"
        assert updated_user.phone == "0987654321"
        assert updated_user.email == "update@example.com"  # 電子郵件不變
    
    def test_delete_user(self, db_session: Session):
        """測試刪除用戶"""
        user_data = UserCreate(
            email="delete@example.com",
            name="待刪除用戶",
            password="password123",
            role=UserRole.VOLUNTEER
        )
        
        user = user_crud.create(db_session, user_data)
        user_id = str(user.id)
        
        # 刪除用戶
        success = user_crud.delete(db_session, user_id)
        assert success == True
        
        # 確認用戶已被刪除
        deleted_user = user_crud.get_by_id(db_session, user_id)
        assert deleted_user is None
    
    def test_update_role(self, db_session: Session):
        """測試更新用戶角色"""
        user_data = UserCreate(
            email="role@example.com",
            name="角色測試",
            password="password123",
            role=UserRole.VOLUNTEER
        )
        
        user = user_crud.create(db_session, user_data)
        
        # 更新角色為管理員
        updated_user = user_crud.update_role(db_session, str(user.id), UserRole.ADMIN)
        
        assert updated_user is not None
        assert updated_user.role == UserRole.ADMIN.value
        assert updated_user.is_approved == True  # 管理員自動通過審核
    
    def test_update_approval_status(self, db_session: Session):
        """測試更新審核狀態"""
        user_data = UserCreate(
            email="approval@example.com",
            name="審核測試",
            password="password123",
            role=UserRole.UNOFFICIAL_ORG
        )
        
        user = user_crud.create(db_session, user_data)
        assert user.is_approved == False
        
        # 通過審核
        updated_user = user_crud.update_approval_status(db_session, str(user.id), True)
        
        assert updated_user is not None
        assert updated_user.is_approved == True
    
    def test_reset_password(self, db_session: Session):
        """測試重設密碼"""
        user_data = UserCreate(
            email="password@example.com",
            name="密碼測試",
            password="oldpassword",
            role=UserRole.VOLUNTEER
        )
        
        user = user_crud.create(db_session, user_data)
        old_hash = user.password_hash
        
        # 重設密碼
        success = user_crud.reset_password(db_session, str(user.id), "newpassword")
        assert success == True
        
        # 確認密碼已變更
        updated_user = user_crud.get_by_id(db_session, str(user.id))
        assert updated_user.password_hash != old_hash
        assert verify_password("newpassword", updated_user.password_hash)
    
    def test_get_multi_with_search(self, db_session: Session):
        """測試搜尋和篩選用戶列表"""
        # 建立測試用戶
        users_data = [
            UserCreate(email="admin@test.com", name="管理員", password="pass", role=UserRole.ADMIN),
            UserCreate(email="volunteer1@test.com", name="志工一", password="pass", role=UserRole.VOLUNTEER),
            UserCreate(email="volunteer2@test.com", name="志工二", password="pass", role=UserRole.VOLUNTEER),
            UserCreate(email="victim@test.com", name="受災戶", password="pass", role=UserRole.VICTIM),
        ]
        
        for user_data in users_data:
            user_crud.create(db_session, user_data)
        
        # 測試角色篩選
        search_query = UserSearchQuery(role=UserRole.VOLUNTEER)
        volunteers = user_crud.get_multi(db_session, search_query=search_query)
        assert len(volunteers) == 2
        
        # 測試名稱搜尋
        search_query = UserSearchQuery(name="志工")
        volunteers = user_crud.get_multi(db_session, search_query=search_query)
        assert len(volunteers) == 2
        
        # 測試電子郵件搜尋
        search_query = UserSearchQuery(email="admin")
        admins = user_crud.get_multi(db_session, search_query=search_query)
        assert len(admins) == 1
        assert admins[0].role == UserRole.ADMIN.value
    
    def test_count_with_search(self, db_session: Session):
        """測試計算用戶總數（含搜尋）"""
        # 建立測試用戶
        users_data = [
            UserCreate(email="count1@test.com", name="用戶1", password="pass", role=UserRole.VOLUNTEER),
            UserCreate(email="count2@test.com", name="用戶2", password="pass", role=UserRole.VOLUNTEER),
            UserCreate(email="count3@test.com", name="用戶3", password="pass", role=UserRole.VICTIM),
        ]
        
        for user_data in users_data:
            user_crud.create(db_session, user_data)
        
        # 測試總數
        total = user_crud.count(db)
        assert total >= 3
        
        # 測試篩選後的數量
        search_query = UserSearchQuery(role=UserRole.VOLUNTEER)
        volunteer_count = user_crud.count(db_session, search_query=search_query)
        assert volunteer_count == 2


class TestOrganizationCRUD:
    """組織 CRUD 測試類"""
    
    def test_create_organization_success(self, db_session: Session):
        """測試成功建立組織"""
        # 先建立用戶
        user_data = UserCreate(
            email="org@example.com",
            name="組織負責人",
            password="password123",
            role=UserRole.OFFICIAL_ORG
        )
        user = user_crud.create(db_session, user_data)
        
        # 建立組織
        org_data = OrganizationCreate(
            user_id=str(user.id),
            organization_name="測試組織",
            organization_type="official",
            contact_person="聯絡人",
            contact_phone="0912345678",
            address="測試地址",
            description="測試描述"
        )
        
        org = user_crud.create_organization(db_session, org_data)
        
        assert org.organization_name == "測試組織"
        assert org.organization_type == "official"
        assert org.contact_person == "聯絡人"
        assert org.approval_status == "approved"  # 正式組織自動通過
    
    def test_create_organization_user_not_exists(self, db_session: Session):
        """測試建立組織時用戶不存在"""
        org_data = OrganizationCreate(
            user_id="non-existent-id",
            organization_name="測試組織",
            organization_type="official"
        )
        
        with pytest.raises(ValueError, match="用戶不存在"):
            user_crud.create_organization(db_session, org_data)
    
    def test_create_organization_duplicate_user(self, db_session: Session):
        """測試用戶已有組織時建立組織"""
        # 建立用戶
        user_data = UserCreate(
            email="duplicate_org@example.com",
            name="組織負責人",
            password="password123",
            role=UserRole.OFFICIAL_ORG
        )
        user = user_crud.create(db_session, user_data)
        
        # 建立第一個組織
        org_data1 = OrganizationCreate(
            user_id=str(user.id),
            organization_name="第一個組織",
            organization_type="official"
        )
        user_crud.create_organization(db_session, org_data1)
        
        # 嘗試建立第二個組織
        org_data2 = OrganizationCreate(
            user_id=str(user.id),
            organization_name="第二個組織",
            organization_type="official"
        )
        
        with pytest.raises(ValueError, match="用戶已有組織資訊"):
            user_crud.create_organization(db_session, org_data2)
    
    def test_get_organization_by_user_id(self, db_session: Session):
        """測試根據用戶 ID 取得組織"""
        # 建立用戶和組織
        user_data = UserCreate(
            email="find_org@example.com",
            name="組織負責人",
            password="password123",
            role=UserRole.OFFICIAL_ORG
        )
        user = user_crud.create(db_session, user_data)
        
        org_data = OrganizationCreate(
            user_id=str(user.id),
            organization_name="可找到的組織",
            organization_type="official"
        )
        created_org = user_crud.create_organization(db_session, org_data)
        
        # 根據用戶 ID 查找組織
        found_org = user_crud.get_organization_by_user_id(db_session, str(user.id))
        
        assert found_org is not None
        assert found_org.id == created_org.id
        assert found_org.organization_name == "可找到的組織"
    
    def test_update_organization(self, db_session: Session):
        """測試更新組織資料"""
        # 建立用戶和組織
        user_data = UserCreate(
            email="update_org@example.com",
            name="組織負責人",
            password="password123",
            role=UserRole.OFFICIAL_ORG
        )
        user = user_crud.create(db_session, user_data)
        
        org_data = OrganizationCreate(
            user_id=str(user.id),
            organization_name="原始組織名稱",
            organization_type="official",
            contact_person="原始聯絡人"
        )
        org = user_crud.create_organization(db_session, org_data)
        
        # 更新組織資料
        update_data = OrganizationUpdate(
            organization_name="更新後組織名稱",
            contact_person="更新後聯絡人"
        )
        
        updated_org = user_crud.update_organization(db_session, str(org.id), update_data)
        
        assert updated_org is not None
        assert updated_org.organization_name == "更新後組織名稱"
        assert updated_org.contact_person == "更新後聯絡人"
        assert updated_org.organization_type == "official"  # 未更新的欄位保持不變
    
    def test_approve_organization(self, db_session: Session):
        """測試審核組織"""
        # 建立用戶和非正式組織
        user_data = UserCreate(
            email="approve_org@example.com",
            name="非正式組織負責人",
            password="password123",
            role=UserRole.UNOFFICIAL_ORG
        )
        user = user_crud.create(db_session, user_data)
        
        org_data = OrganizationCreate(
            user_id=str(user.id),
            organization_name="待審核組織",
            organization_type="unofficial"
        )
        org = user_crud.create_organization(db_session, org_data)
        
        # 建立管理員
        admin_data = UserCreate(
            email="admin@example.com",
            name="管理員",
            password="password123",
            role=UserRole.ADMIN
        )
        admin = user_crud.create(db_session, admin_data)
        
        # 審核通過
        approved_org = user_crud.approve_organization(db_session, str(org.id), str(admin.id), True)
        
        assert approved_org is not None
        assert approved_org.approval_status == "approved"
        assert approved_org.approved_by == admin.id
        assert approved_org.approved_at is not None
        
        # 檢查用戶的審核狀態也被更新
        updated_user = user_crud.get_by_id(db_session, str(user.id))
        assert updated_user.is_approved == True
    
    def test_get_pending_organizations(self, db_session: Session):
        """測試取得待審核組織列表"""
        # 建立多個組織
        orgs_data = []
        for i in range(3):
            user_data = UserCreate(
                email=f"pending{i}@example.com",
                name=f"用戶{i}",
                password="password123",
                role=UserRole.UNOFFICIAL_ORG
            )
            user = user_crud.create(db_session, user_data)
            
            org_data = OrganizationCreate(
                user_id=str(user.id),
                organization_name=f"待審核組織{i}",
                organization_type="unofficial"
            )
            user_crud.create_organization(db_session, org_data)
        
        # 取得待審核組織
        pending_orgs = user_crud.get_pending_organizations(db)
        
        assert len(pending_orgs) == 3
        for org in pending_orgs:
            assert org.approval_status == "pending"
    
    def test_delete_organization(self, db_session: Session):
        """測試刪除組織"""
        # 建立用戶和組織
        user_data = UserCreate(
            email="delete_org@example.com",
            name="組織負責人",
            password="password123",
            role=UserRole.OFFICIAL_ORG
        )
        user = user_crud.create(db_session, user_data)
        
        org_data = OrganizationCreate(
            user_id=str(user.id),
            organization_name="待刪除組織",
            organization_type="official"
        )
        org = user_crud.create_organization(db_session, org_data)
        org_id = str(org.id)
        
        # 刪除組織
        success = user_crud.delete_organization(db_session, org_id)
        assert success == True
        
        # 確認組織已被刪除
        deleted_org = user_crud.get_organization_by_id(db_session, org_id)
        assert deleted_org is None