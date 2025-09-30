"""
簡單的任務管理測試
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.utils.constants import UserRole
from tests.conftest import create_test_user


def test_create_task_basic(client: TestClient, db_session: Session):
    """測試基本任務建立功能"""
    # 建立正式組織用戶
    user = create_test_user(db_session, role=UserRole.OFFICIAL_ORG)
    
    # 登入獲取 token
    login_response = client.post("/api/v1/auth/login", json={
        "email": user.email,
        "password": "testpassword123"
    })
    
    # 檢查登入是否成功
    assert login_response.status_code == 200
    token = login_response.json()["token"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 建立任務資料
    task_data = {
        "title": "災後清理工作",
        "description": "清理災區垃圾和雜物",
        "task_type": "cleanup",
        "location_data": {
            "address": "花蓮縣光復鄉中正路123號",
            "coordinates": {"lat": 23.5731, "lng": 121.4208},
            "details": "學校操場"
        },
        "required_volunteers": 10,
        "required_skills": ["體力勞動", "垃圾分類"],
        "priority_level": 3
    }
    
    # 發送建立任務請求
    response = client.post("/api/v1/tasks/", json=task_data, headers=headers)
    
    # 檢查回應
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == task_data["title"]
    assert data["status"] == "available"  # 正式組織任務直接可用
    assert data["approval_status"] == "approved"
    assert data["creator_id"] == str(user.id)