"""
組織審核系統的整合測試
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.crud.user import user_crud
from app.schemas.user import UserCreate, OrganizationCreate
from app.services.organization_service import organization_service
from app.utils.constants import UserRole
from app.core.security import create_access_token


class TestOrganizationApprovalSystem:
    """組織審核系統測試類"""
    
    @pytest.fixture
    def client(self):
        """測試客戶端"""
        return TestClient(app)
    
    @pytest.fixture
    def admin_user(self, db_session: Session):
        """管理員用戶"""
        admin_data = UserCreate(
            email="admin@test.com",
            name="管理員",
            password="password123",
            role=UserRole.ADMIN
        )
        return user_crud.create(db_session, admin_data)
    
    @pytest.fixture
    def unofficial_org_user(self, db_session: Session):
        """非正式組織用戶"""
        user_data = UserCreate(
            email="unofficial@test.com",
            name="非正式組織負責人",
            password="password123",
            role=UserRole.UNOFFICIAL_ORG
        )
        return user_crud.create(db_session, user_data)
    
    @pytest.fixture
    def admin_token(self, admin_user):
        """管理員 token"""
        return create_access_token(data={"sub": str(admin_user.id)})
    
    @pytest.fixture
    def unofficial_org_token(self, unofficial_org_user):
        """非正式組織 token"""
        return create_access_token(data={"sub": str(unofficial_org_user.id)})
    
    def test_submit_organization_application_success(
        self, 
        client: TestClient, 
        unofficial_org_token: str,
        db_session: Session
    ):
        """測試成功提交組織申請"""
        headers = {"Authorization": f"Bearer {unofficial_org_token}"}
        application_data = {
            "organization_name": "測試非正式組織",
            "contact_person": "聯絡人",
            "contact_phone": "0912345678",
            "address": "測試地址",
            "description": "測試描述"
        }
        
        response = client.post(
            "/api/v1/organization-approval/submit",
            json=application_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["organization_name"] == "測試非正式組織"
        assert data["approval_status"] == "pending"
        assert data["organization_type"] == "unofficial"
    
    def test_submit_application_wrong_role(
        self, 
        client: TestClient, 
        db_session: Session
    ):
        """測試錯誤角色提交申請"""
        # 建立一般志工用戶
        volunteer_data = UserCreate(
            email="volunteer@test.com",
            name="一般志工",
            password="password123",
            role=UserRole.VOLUNTEER
        )
        volunteer = user_crud.create(db_session, volunteer_data)
        volunteer_token = create_access_token(data={"sub": str(volunteer.id)})
        
        headers = {"Authorization": f"Bearer {volunteer_token}"}
        application_data = {
            "organization_name": "測試組織"
        }
        
        response = client.post(
            "/api/v1/organization-approval/submit",
            json=application_data,
            headers=headers
        )
        
        assert response.status_code == 403
        assert "只有非正式組織可以提交審核申請" in response.json()["detail"]
    
    def test_submit_duplicate_application(
        self,
        client: TestClient,
        unofficial_org_token: str,
        unofficial_org_user,
        db_session: Session
    ):
        """測試重複提交申請"""
        # 先建立一個組織申請
        org_data = OrganizationCreate(
            user_id=str(unofficial_org_user.id),
            organization_name="已存在的組織",
            organization_type="unofficial"
        )
        user_crud.create_organization(db_session, org_data)
        
        headers = {"Authorization": f"Bearer {unofficial_org_token}"}
        application_data = {
            "organization_name": "新的組織名稱"
        }
        
        response = client.post(
            "/api/v1/organization-approval/submit",
            json=application_data,
            headers=headers
        )
        
        assert response.status_code == 400
        assert "已有待審核的組織申請" in response.json()["detail"]
    
    def test_get_pending_applications_success(
        self,
        client: TestClient,
        admin_token: str,
        unofficial_org_user,
        db_session: Session
    ):
        """測試取得待審核申請列表"""
        # 建立待審核組織
        org_data = OrganizationCreate(
            user_id=str(unofficial_org_user.id),
            organization_name="待審核組織",
            organization_type="unofficial"
        )
        user_crud.create_organization(db_session, org_data)
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/organization-approval/pending", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["approval_status"] == "pending"
    
    def test_get_pending_applications_unauthorized(self, client: TestClient, unofficial_org_token: str):
        """測試非管理員訪問待審核列表"""
        headers = {"Authorization": f"Bearer {unofficial_org_token}"}
        response = client.get("/api/v1/organization-approval/pending", headers=headers)
        
        assert response.status_code == 403
    
    def test_approve_organization_success(
        self,
        client: TestClient,
        admin_token: str,
        unofficial_org_user,
        db_session: Session
    ):
        """測試成功審核組織"""
        # 建立待審核組織
        org_data = OrganizationCreate(
            user_id=str(unofficial_org_user.id),
            organization_name="待審核組織",
            organization_type="unofficial"
        )
        org = user_crud.create_organization(db_session, org_data)
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        approval_data = {
            "approved": True,
            "notes": "審核通過"
        }
        
        response = client.post(
            f"/api/v1/organization-approval/{org.id}/approve",
            json=approval_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "approved"
        assert data["approver_name"] is not None
    
    def test_reject_organization(
        self,
        client: TestClient,
        admin_token: str,
        unofficial_org_user,
        db_session: Session
    ):
        """測試拒絕組織申請"""
        # 建立待審核組織
        org_data = OrganizationCreate(
            user_id=str(unofficial_org_user.id),
            organization_name="待審核組織",
            organization_type="unofficial"
        )
        org = user_crud.create_organization(db_session, org_data)
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        approval_data = {
            "approved": False,
            "notes": "資料不完整"
        }
        
        response = client.post(
            f"/api/v1/organization-approval/{org.id}/approve",
            json=approval_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "rejected"
    
    def test_resubmit_organization_success(
        self,
        client: TestClient,
        unofficial_org_token: str,
        unofficial_org_user,
        admin_user,
        db_session: Session
    ):
        """測試重新提交組織申請"""
        # 建立被拒絕的組織
        org_data = OrganizationCreate(
            user_id=str(unofficial_org_user.id),
            organization_name="被拒絕的組織",
            organization_type="unofficial"
        )
        org = user_crud.create_organization(db_session, org_data)
        
        # 拒絕申請
        user_crud.approve_organization(db_session, str(org.id), str(admin_user.id), False)
        
        headers = {"Authorization": f"Bearer {unofficial_org_token}"}
        updated_data = {
            "organization_name": "更新後的組織名稱",
            "description": "更新後的描述"
        }
        
        response = client.put(
            f"/api/v1/organization-approval/{org.id}/resubmit",
            json=updated_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["organization_name"] == "更新後的組織名稱"
        assert data["approval_status"] == "pending"
    
    def test_resubmit_non_rejected_organization(
        self,
        client: TestClient,
        unofficial_org_token: str,
        unofficial_org_user,
        db_session: Session
    ):
        """測試重新提交非被拒絕的組織"""
        # 建立待審核組織
        org_data = OrganizationCreate(
            user_id=str(unofficial_org_user.id),
            organization_name="待審核組織",
            organization_type="unofficial"
        )
        org = user_crud.create_organization(db_session, org_data)
        
        headers = {"Authorization": f"Bearer {unofficial_org_token}"}
        updated_data = {
            "organization_name": "更新後的組織名稱"
        }
        
        response = client.put(
            f"/api/v1/organization-approval/{org.id}/resubmit",
            json=updated_data,
            headers=headers
        )
        
        assert response.status_code == 400
        assert "只有被拒絕的申請可以重新提交" in response.json()["detail"]
    
    def test_get_organization_statistics(
        self,
        client: TestClient,
        admin_token: str,
        unofficial_org_user,
        db_session: Session
    ):
        """測試取得組織統計資料"""
        # 建立測試組織
        org_data = OrganizationCreate(
            user_id=str(unofficial_org_user.id),
            organization_name="統計測試組織",
            organization_type="unofficial"
        )
        user_crud.create_organization(db_session, org_data)
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/organization-approval/statistics", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_organizations" in data
        assert "by_status" in data
        assert "by_type" in data
        assert "pending_count" in data
    
    def test_get_my_application_success(
        self,
        client: TestClient,
        unofficial_org_token: str,
        unofficial_org_user,
        db_session: Session
    ):
        """測試取得我的組織申請"""
        # 建立組織申請
        org_data = OrganizationCreate(
            user_id=str(unofficial_org_user.id),
            organization_name="我的組織",
            organization_type="unofficial"
        )
        user_crud.create_organization(db_session, org_data)
        
        headers = {"Authorization": f"Bearer {unofficial_org_token}"}
        response = client.get("/api/v1/organization-approval/my-application", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["organization_name"] == "我的組織"
        assert data["user_name"] == unofficial_org_user.name
    
    def test_get_my_application_not_found(
        self,
        client: TestClient,
        unofficial_org_token: str
    ):
        """測試取得不存在的組織申請"""
        headers = {"Authorization": f"Bearer {unofficial_org_token}"}
        response = client.get("/api/v1/organization-approval/my-application", headers=headers)
        
        assert response.status_code == 404
        assert "尚未提交組織申請" in response.json()["detail"]


class TestOrganizationService:
    """組織服務測試類"""
    
    def test_submit_organization_for_approval_success(self, db_session: Session):
        """測試成功提交組織審核申請"""
        # 建立非正式組織用戶
        user_data = UserCreate(
            email="service_test@test.com",
            name="服務測試用戶",
            password="password123",
            role=UserRole.UNOFFICIAL_ORG
        )
        user = user_crud.create(db_session, user_data)
        
        organization_data = {
            "organization_name": "服務測試組織",
            "organization_type": "unofficial",
            "contact_person": "聯絡人",
            "description": "測試描述"
        }
        
        # 使用 asyncio 運行異步方法
        import asyncio
        organization = asyncio.run(
            organization_service.submit_organization_for_approval(
                db_session, str(user.id), organization_data
            )
        )
        
        assert organization.organization_name == "服務測試組織"
        assert organization.approval_status == "pending"
        assert organization.user_id == user.id
    
    def test_submit_wrong_role(self, db_session: Session):
        """測試錯誤角色提交申請"""
        # 建立一般志工用戶
        user_data = UserCreate(
            email="wrong_role@test.com",
            name="錯誤角色用戶",
            password="password123",
            role=UserRole.VOLUNTEER
        )
        user = user_crud.create(db_session, user_data)
        
        organization_data = {
            "organization_name": "測試組織",
            "organization_type": "unofficial"
        }
        
        import asyncio
        with pytest.raises(ValueError, match="只有非正式組織可以提交審核申請"):
            asyncio.run(
                organization_service.submit_organization_for_approval(
                    db_session, str(user.id), organization_data
                )
            )
    
    def test_approve_organization_success(self, db_session: Session):
        """測試成功審核組織"""
        # 建立管理員和非正式組織用戶
        admin_data = UserCreate(
            email="admin_service@test.com",
            name="管理員",
            password="password123",
            role=UserRole.ADMIN
        )
        admin = user_crud.create(db_session, admin_data)
        
        user_data = UserCreate(
            email="org_service@test.com",
            name="組織用戶",
            password="password123",
            role=UserRole.UNOFFICIAL_ORG
        )
        user = user_crud.create(db_session, user_data)
        
        # 建立組織
        org_data = OrganizationCreate(
            user_id=str(user.id),
            organization_name="待審核組織",
            organization_type="unofficial"
        )
        org = user_crud.create_organization(db_session, org_data)
        
        # 審核組織
        from app.schemas.user import OrganizationApprovalRequest
        approval_data = OrganizationApprovalRequest(
            approved=True,
            notes="審核通過"
        )
        
        import asyncio
        approved_org = asyncio.run(
            organization_service.approve_organization(
                db_session, str(org.id), str(admin.id), approval_data
            )
        )
        
        assert approved_org.approval_status == "approved"
        assert approved_org.approved_by == admin.id
        assert approved_org.approved_at is not None
    
    def test_get_organization_statistics(self, db_session: Session):
        """測試取得組織統計資料"""
        # 建立測試組織
        user_data = UserCreate(
            email="stats_test@test.com",
            name="統計測試用戶",
            password="password123",
            role=UserRole.UNOFFICIAL_ORG
        )
        user = user_crud.create(db_session, user_data)
        
        org_data = OrganizationCreate(
            user_id=str(user.id),
            organization_name="統計測試組織",
            organization_type="unofficial"
        )
        user_crud.create_organization(db_session, org_data)
        
        import asyncio
        stats = asyncio.run(organization_service.get_organization_statistics(db_session))
        
        assert "total_organizations" in stats
        assert "by_status" in stats
        assert "by_type" in stats
        assert stats["total_organizations"] >= 1