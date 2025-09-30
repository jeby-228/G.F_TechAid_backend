"""
身分驗證系統的單元測試
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import get_db
from app.core.security import create_access_token, verify_password, get_password_hash, verify_token
from app.crud.user import user_crud
from app.services.auth_service import auth_service
from app.schemas.auth import UserRegistration, UserLogin
from app.utils.constants import UserRole
from tests.conftest import TestingSessionLocal, override_get_db

# 覆蓋資料庫依賴
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestSecurityFunctions:
    """測試安全相關函數"""
    
    def test_password_hashing(self):
        """測試密碼雜湊和驗證"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        # 驗證雜湊值不等於原密碼
        assert hashed != password
        
        # 驗證密碼驗證功能
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_jwt_token_creation_and_verification(self):
        """測試 JWT token 建立和驗證"""
        user_id = "test-user-id"
        
        # 建立 token
        token = create_access_token(subject=user_id)
        assert token is not None
        
        # 驗證 token
        decoded_user_id = verify_token(token)
        assert decoded_user_id == user_id
    
    def test_jwt_token_expiration(self):
        """測試 JWT token 過期"""
        user_id = "test-user-id"
        
        # 建立已過期的 token（過期時間為 -1 分鐘）
        expired_token = create_access_token(
            subject=user_id,
            expires_delta=timedelta(minutes=-1)
        )
        
        # 驗證過期 token 應該返回 None
        decoded_user_id = verify_token(expired_token)
        assert decoded_user_id is None
    
    def test_invalid_jwt_token(self):
        """測試無效的 JWT token"""
        invalid_token = "invalid.jwt.token"
        decoded_user_id = verify_token(invalid_token)
        assert decoded_user_id is None


class TestUserCRUD:
    """測試用戶 CRUD 操作"""
    
    def setup_method(self):
        """每個測試方法前的設置"""
        self.db = TestingSessionLocal()
    
    def teardown_method(self):
        """每個測試方法後的清理"""
        self.db.close()
    
    def test_create_user_success(self):
        """測試成功建立用戶"""
        user_data = UserRegistration(
            email="test@example.com",
            name="測試用戶",
            password="password123",
            role=UserRole.VOLUNTEER
        )
        
        user = user_crud.create_user(self.db, user_data)
        
        assert user.email == user_data.email
        assert user.name == user_data.name
        assert user.role == user_data.role.value
        assert user.is_approved is True  # 一般志工自動審核通過
        assert verify_password(user_data.password, user.password_hash)
    
    def test_create_user_duplicate_email(self):
        """測試建立重複電子郵件的用戶"""
        user_data = UserRegistration(
            email="duplicate@example.com",
            name="測試用戶1",
            password="password123",
            role=UserRole.VOLUNTEER
        )
        
        # 建立第一個用戶
        user_crud.create_user(self.db, user_data)
        
        # 嘗試建立相同電子郵件的用戶
        user_data.name = "測試用戶2"
        with pytest.raises(ValueError, match="電子郵件已被使用"):
            user_crud.create_user(self.db, user_data)
    
    def test_create_organization_user(self):
        """測試建立組織用戶"""
        user_data = UserRegistration(
            email="org@example.com",
            name="組織負責人",
            password="password123",
            role=UserRole.OFFICIAL_ORG,
            organization_name="測試組織",
            organization_type="official",
            contact_person="聯絡人",
            contact_phone="0912345678"
        )
        
        user = user_crud.create_user(self.db, user_data)
        
        assert user.role == UserRole.OFFICIAL_ORG.value
        assert user.is_approved is True  # 正式組織自動審核通過
        
        # 檢查組織資訊是否建立
        from app.models.user import Organization
        organization = self.db.query(Organization).filter(
            Organization.user_id == user.id
        ).first()
        
        assert organization is not None
        assert organization.organization_name == user_data.organization_name
        assert organization.approval_status == "approved"
    
    def test_authenticate_user_success(self):
        """測試用戶驗證成功"""
        # 先建立用戶
        user_data = UserRegistration(
            email="auth@example.com",
            name="驗證用戶",
            password="password123",
            role=UserRole.VOLUNTEER
        )
        user_crud.create_user(self.db, user_data)
        
        # 驗證用戶
        authenticated_user = user_crud.authenticate_user(
            self.db, user_data.email, user_data.password
        )
        
        assert authenticated_user is not None
        assert authenticated_user.email == user_data.email
    
    def test_authenticate_user_wrong_password(self):
        """測試用戶驗證失敗（錯誤密碼）"""
        # 先建立用戶
        user_data = UserRegistration(
            email="auth2@example.com",
            name="驗證用戶2",
            password="password123",
            role=UserRole.VOLUNTEER
        )
        user_crud.create_user(self.db, user_data)
        
        # 使用錯誤密碼驗證
        authenticated_user = user_crud.authenticate_user(
            self.db, user_data.email, "wrong_password"
        )
        
        assert authenticated_user is None
    
    def test_authenticate_user_not_exist(self):
        """測試驗證不存在的用戶"""
        authenticated_user = user_crud.authenticate_user(
            self.db, "notexist@example.com", "password123"
        )
        
        assert authenticated_user is None


class TestAuthService:
    """測試身分驗證服務"""
    
    def setup_method(self):
        """每個測試方法前的設置"""
        self.db = TestingSessionLocal()
    
    def teardown_method(self):
        """每個測試方法後的清理"""
        self.db.close()
    
    def test_register_user_success(self):
        """測試用戶註冊成功"""
        user_data = UserRegistration(
            email="register@example.com",
            name="註冊用戶",
            password="password123",
            role=UserRole.VOLUNTEER
        )
        
        result = auth_service.register_user(self.db, user_data)
        
        assert "user" in result
        assert "token" in result
        assert "message" in result
        
        assert result["user"].email == user_data.email
        assert result["token"].access_token is not None
        assert result["token"].token_type == "bearer"
    
    def test_login_user_success(self):
        """測試用戶登入成功"""
        # 先註冊用戶
        user_data = UserRegistration(
            email="login@example.com",
            name="登入用戶",
            password="password123",
            role=UserRole.VOLUNTEER
        )
        auth_service.register_user(self.db, user_data)
        
        # 登入
        login_data = UserLogin(
            email=user_data.email,
            password=user_data.password
        )
        result = auth_service.login_user(self.db, login_data)
        
        assert "user" in result
        assert "token" in result
        
        assert result["user"].email == user_data.email
        assert result["token"].access_token is not None
    
    def test_check_permission(self):
        """測試權限檢查"""
        # 測試管理員權限
        assert auth_service.check_permission(UserRole.ADMIN, "any_permission") is True
        
        # 測試一般志工權限
        assert auth_service.check_permission(UserRole.VOLUNTEER, "claim_task") is True
        assert auth_service.check_permission(UserRole.VOLUNTEER, "create_task") is False
        
        # 測試受災戶權限
        assert auth_service.check_permission(UserRole.VICTIM, "create_need") is True
        assert auth_service.check_permission(UserRole.VICTIM, "claim_task") is False


class TestAuthAPI:
    """測試身分驗證 API 端點"""
    
    def test_register_api_success(self):
        """測試註冊 API 成功"""
        user_data = {
            "email": "api_register@example.com",
            "name": "API註冊用戶",
            "password": "password123",
            "role": "volunteer"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user" in data
        assert "token" in data
        assert data["user"]["email"] == user_data["email"]
        assert data["token"]["access_token"] is not None
    
    def test_register_api_duplicate_email(self):
        """測試註冊 API 重複電子郵件"""
        user_data = {
            "email": "duplicate_api@example.com",
            "name": "重複用戶",
            "password": "password123",
            "role": "volunteer"
        }
        
        # 第一次註冊
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # 第二次註冊相同電子郵件
        response2 = client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
    
    def test_login_api_success(self):
        """測試登入 API 成功"""
        # 先註冊用戶
        register_data = {
            "email": "api_login@example.com",
            "name": "API登入用戶",
            "password": "password123",
            "role": "volunteer"
        }
        client.post("/api/v1/auth/register", json=register_data)
        
        # 登入
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user" in data
        assert "token" in data
        assert data["user"]["email"] == register_data["email"]
    
    def test_login_api_wrong_credentials(self):
        """測試登入 API 錯誤憑證"""
        login_data = {
            "email": "wrong@example.com",
            "password": "wrong_password"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
    
    def test_get_current_user_api(self):
        """測試取得當前用戶 API"""
        # 先註冊並登入
        register_data = {
            "email": "current_user@example.com",
            "name": "當前用戶",
            "password": "password123",
            "role": "volunteer"
        }
        register_response = client.post("/api/v1/auth/register", json=register_data)
        token = register_response.json()["token"]["access_token"]
        
        # 取得當前用戶資訊
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == register_data["email"]
        assert data["name"] == register_data["name"]
        assert data["role"] == register_data["role"]
    
    def test_get_current_user_api_unauthorized(self):
        """測試未授權存取當前用戶 API"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403  # FastAPI HTTPBearer 預設回傳 403
    
    def test_get_permissions_api(self):
        """測試取得權限 API"""
        # 先註冊並登入
        register_data = {
            "email": "permissions@example.com",
            "name": "權限用戶",
            "password": "password123",
            "role": "volunteer"
        }
        register_response = client.post("/api/v1/auth/register", json=register_data)
        token = register_response.json()["token"]["access_token"]
        
        # 取得權限
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/permissions", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["role"] == "volunteer"
        assert "permissions" in data
        assert data["permissions"]["claim_task"] is True