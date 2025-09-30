"""
用戶管理 API 的測試
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.crud.user import user_crud
from app.schemas.user import UserCreate, OrganizationCreate
from app.utils.constants import UserRole
from app.core.security import create_access_token


class TestUserAPI:
    """用戶管理 API 測試類"""
    
    @pytest.fixture
    def client(self):
        """測試客戶端"""
        return TestClient(app)
    
    @pytest.fixture
    def admin_token(self, db: Session):
        """管理員 token"""
        admin_data = UserCreate(
            email="admin@test.com",
            name="管理員",
            password="password123",
            role=UserRole.ADMIN
        )
        admin = user_crud.create(db, admin_data)
        return create_access_token(data={"sub": str(admin.id)})
    
    @pytest.fixture
    def test_user(self, db: Session):
        """測試用戶"""
        user_data = UserCreate(
            email="testuser@test.com",
            name="測試用戶",
            password="password123",
            role=UserRole.VOLUNTEER,
            phone="0912345678"
        )
        return user_crud.create(db, user_data)
    
    def test_get_users_unauthorized(self, client: TestClient):
        """測試未授權訪問用戶列表"""
        response = client.get("/api/v1/users/")
        assert response.status_code == 401
    
    def test_get_users_success(self, client: TestClient, admin_token: str, test_user, db: Session):
        """測試成功取得用戶列表"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/users/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert data["total"] >= 1
        assert len(data["users"]) >= 1
    
    def test_get_users_with_filters(self, client: TestClient, admin_token: str, test_user, db: Session):
        """測試使用篩選條件取得用戶列表"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 測試角色篩選
        response = client.get(
            "/api/v1/users/?role=volunteer",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        for user in data["users"]:
            assert user["role"] == "volunteer"
        
        # 測試名稱搜尋
        response = client.get(
            "/api/v1/users/?name=測試",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) >= 1
    
    def test_get_user_by_id_success(self, client: TestClient, admin_token: str, test_user, db: Session):
        """測試成功取得特定用戶"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(f"/api/v1/users/{test_user.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
    
    def test_get_user_by_id_not_found(self, client: TestClient, admin_token: str):
        """測試取得不存在的用戶"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/users/non-existent-id", headers=headers)
        
        assert response.status_code == 404
        assert "用戶不存在" in response.json()["detail"]
    
    def test_create_user_success(self, client: TestClient, admin_token: str):
        """測試成功建立用戶"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        user_data = {
            "email": "newuser@test.com",
            "name": "新用戶",
            "password": "password123",
            "role": "volunteer",
            "phone": "0987654321"
        }
        
        response = client.post("/api/v1/users/", json=user_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["name"] == "新用戶"
        assert data["role"] == "volunteer"
        assert data["phone"] == "0987654321"
    
    def test_create_user_duplicate_email(self, client: TestClient, admin_token: str, test_user):
        """測試建立重複電子郵件的用戶"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        user_data = {
            "email": test_user.email,  # 使用已存在的電子郵件
            "name": "重複用戶",
            "password": "password123",
            "role": "volunteer"
        }
        
        response = client.post("/api/v1/users/", json=user_data, headers=headers)
        
        assert response.status_code == 400
        assert "電子郵件已被使用" in response.json()["detail"]
    
    def test_update_user_success(self, client: TestClient, admin_token: str, test_user):
        """測試成功更新用戶"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {
            "name": "更新後名稱",
            "phone": "0999888777"
        }
        
        response = client.put(f"/api/v1/users/{test_user.id}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新後名稱"
        assert data["phone"] == "0999888777"
        assert data["email"] == test_user.email  # 電子郵件不變
    
    def test_delete_user_success(self, client: TestClient, admin_token: str, test_user):
        """測試成功刪除用戶"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.delete(f"/api/v1/users/{test_user.id}", headers=headers)
        
        assert response.status_code == 200
        assert "用戶刪除成功" in response.json()["message"]
        
        # 確認用戶已被刪除
        response = client.get(f"/api/v1/users/{test_user.id}", headers=headers)
        assert response.status_code == 404
    
    def test_update_user_role_success(self, client: TestClient, admin_token: str, test_user):
        """測試成功更新用戶角色"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        role_data = {"role": "admin"}
        
        response = client.put(f"/api/v1/users/{test_user.id}/role", json=role_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
    
    def test_update_user_approval_success(self, client: TestClient, admin_token: str, db: Session):
        """測試成功更新用戶審核狀態"""
        # 建立需要審核的用戶
        user_data = UserCreate(
            email="approval@test.com",
            name="待審核用戶",
            password="password123",
            role=UserRole.UNOFFICIAL_ORG
        )
        user = user_crud.create(db, user_data)
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        approval_data = {
            "is_approved": True,
            "notes": "審核通過"
        }
        
        response = client.put(f"/api/v1/users/{user.id}/approval", json=approval_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_approved"] == True
    
    def test_reset_user_password_success(self, client: TestClient, admin_token: str, test_user):
        """測試成功重設用戶密碼"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        password_data = {"new_password": "newpassword123"}
        
        response = client.post(f"/api/v1/users/{test_user.id}/reset-password", json=password_data, headers=headers)
        
        assert response.status_code == 200
        assert "密碼重設成功" in response.json()["message"]
    
    def test_get_user_statistics_success(self, client: TestClient, admin_token: str, test_user):
        """測試成功取得用戶統計資料"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/users/statistics", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "users_by_role" in data
        assert "approved_users" in data
        assert "pending_approvals" in data
        assert data["total_users"] >= 1


class TestOrganizationAPI:
    """組織管理 API 測試類"""
    
    @pytest.fixture
    def client(self):
        """測試客戶端"""
        return TestClient(app)
    
    @pytest.fixture
    def admin_token(self, db: Session):
        """管理員 token"""
        admin_data = UserCreate(
            email="admin@test.com",
            name="管理員",
            password="password123",
            role=UserRole.ADMIN
        )
        admin = user_crud.create(db, admin_data)
        return create_access_token(data={"sub": str(admin.id)})
    
    @pytest.fixture
    def test_organization(self, db: Session):
        """測試組織"""
        # 建立用戶
        user_data = UserCreate(
            email="org@test.com",
            name="組織負責人",
            password="password123",
            role=UserRole.OFFICIAL_ORG
        )
        user = user_crud.create(db, user_data)
        
        # 建立組織
        org_data = OrganizationCreate(
            user_id=str(user.id),
            organization_name="測試組織",
            organization_type="official",
            contact_person="聯絡人",
            contact_phone="0912345678"
        )
        return user_crud.create_organization(db, org_data)
    
    def test_get_organizations_success(self, client: TestClient, admin_token: str, test_organization):
        """測試成功取得組織列表"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/users/organizations/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "organizations" in data
        assert "total" in data
        assert data["total"] >= 1
    
    def test_get_organization_by_id_success(self, client: TestClient, admin_token: str, test_organization):
        """測試成功取得特定組織"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(f"/api/v1/users/organizations/{test_organization.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_organization.id)
        assert data["organization_name"] == test_organization.organization_name
    
    def test_create_organization_success(self, client: TestClient, admin_token: str, db: Session):
        """測試成功建立組織"""
        # 先建立用戶
        user_data = UserCreate(
            email="neworg@test.com",
            name="新組織負責人",
            password="password123",
            role=UserRole.OFFICIAL_ORG
        )
        user = user_crud.create(db, user_data)
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        org_data = {
            "user_id": str(user.id),
            "organization_name": "新組織",
            "organization_type": "official",
            "contact_person": "新聯絡人",
            "contact_phone": "0987654321"
        }
        
        response = client.post("/api/v1/users/organizations/", json=org_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["organization_name"] == "新組織"
        assert data["contact_person"] == "新聯絡人"
    
    def test_update_organization_success(self, client: TestClient, admin_token: str, test_organization):
        """測試成功更新組織"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {
            "organization_name": "更新後組織名稱",
            "contact_person": "更新後聯絡人"
        }
        
        response = client.put(f"/api/v1/users/organizations/{test_organization.id}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["organization_name"] == "更新後組織名稱"
        assert data["contact_person"] == "更新後聯絡人"
    
    def test_approve_organization_success(self, client: TestClient, admin_token: str, db: Session):
        """測試成功審核組織"""
        # 建立待審核組織
        user_data = UserCreate(
            email="pending@test.com",
            name="待審核組織負責人",
            password="password123",
            role=UserRole.UNOFFICIAL_ORG
        )
        user = user_crud.create(db, user_data)
        
        org_data = OrganizationCreate(
            user_id=str(user.id),
            organization_name="待審核組織",
            organization_type="unofficial"
        )
        org = user_crud.create_organization(db, org_data)
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        approval_data = {
            "approved": True,
            "notes": "審核通過"
        }
        
        response = client.post(f"/api/v1/users/organizations/{org.id}/approve", json=approval_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "approved"
    
    def test_get_pending_organizations_success(self, client: TestClient, admin_token: str, db: Session):
        """測試成功取得待審核組織列表"""
        # 建立待審核組織
        user_data = UserCreate(
            email="pending2@test.com",
            name="待審核組織負責人2",
            password="password123",
            role=UserRole.UNOFFICIAL_ORG
        )
        user = user_crud.create(db, user_data)
        
        org_data = OrganizationCreate(
            user_id=str(user.id),
            organization_name="待審核組織2",
            organization_type="unofficial"
        )
        user_crud.create_organization(db, org_data)
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/users/organizations/pending", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        for org in data:
            assert org["approval_status"] == "pending"
    
    def test_delete_organization_success(self, client: TestClient, admin_token: str, test_organization):
        """測試成功刪除組織"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.delete(f"/api/v1/users/organizations/{test_organization.id}", headers=headers)
        
        assert response.status_code == 200
        assert "組織刪除成功" in response.json()["message"]
        
        # 確認組織已被刪除
        response = client.get(f"/api/v1/users/organizations/{test_organization.id}", headers=headers)
        assert response.status_code == 404