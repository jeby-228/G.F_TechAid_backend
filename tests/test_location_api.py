"""
地理位置 API 端點的測試
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from app.main import app
from app.models.user import User
from app.models.supply import SupplyStation
from app.models.system import Shelter


class TestLocationAPI:
    """地理位置 API 測試類別"""
    
    def setup_method(self):
        """測試前設置"""
        self.client = TestClient(app)
    
    def test_geocode_address_success(self, auth_headers):
        """測試地址地理編碼成功"""
        with patch('app.services.location_service.location_service.geocode_address') as mock_geocode:
            mock_geocode.return_value = {
                "latitude": 23.6739,
                "longitude": 121.4015,
                "formatted_address": "970花蓮縣光復鄉中正路一段1號",
                "place_id": "ChIJtest123",
                "address_components": []
            }
            
            response = self.client.post(
                "/api/v1/locations/geocode",
                json={"address": "光復鄉公所"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["latitude"] == 23.6739
            assert data["longitude"] == 121.4015
            assert "光復鄉" in data["formatted_address"]
    
    def test_geocode_address_not_found(self, auth_headers):
        """測試地址找不到的情況"""
        with patch('app.services.location_service.location_service.geocode_address') as mock_geocode:
            mock_geocode.return_value = None
            
            response = self.client.post(
                "/api/v1/locations/geocode",
                json={"address": "不存在的地址"},
                headers=auth_headers
            )
            
            assert response.status_code == 404
            assert "無法找到指定地址" in response.json()["detail"]
    
    def test_geocode_address_invalid_input(self, auth_headers):
        """測試無效輸入"""
        response = self.client.post(
            "/api/v1/locations/geocode",
            json={"address": ""},  # 空地址
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_reverse_geocode_success(self, auth_headers):
        """測試反向地理編碼成功"""
        with patch('app.services.location_service.location_service.validate_coordinates') as mock_validate, \
             patch('app.services.location_service.location_service.reverse_geocode') as mock_reverse:
            
            mock_validate.return_value = True
            mock_reverse.return_value = {
                "formatted_address": "970花蓮縣光復鄉中正路一段1號",
                "address_components": [],
                "place_id": "ChIJtest123"
            }
            
            response = self.client.post(
                "/api/v1/locations/reverse-geocode",
                json={"latitude": 23.6739, "longitude": 121.4015},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "光復鄉" in data["formatted_address"]
    
    def test_reverse_geocode_invalid_coordinates(self, auth_headers):
        """測試無效座標的反向地理編碼"""
        with patch('app.services.location_service.location_service.validate_coordinates') as mock_validate:
            mock_validate.return_value = False
            
            response = self.client.post(
                "/api/v1/locations/reverse-geocode",
                json={"latitude": 91.0, "longitude": 121.4015},  # 無效緯度
                headers=auth_headers
            )
            
            assert response.status_code == 400
            assert "無效的座標範圍" in response.json()["detail"]
    
    def test_calculate_distance_success(self, auth_headers):
        """測試距離計算成功"""
        with patch('app.services.location_service.location_service.validate_coordinates') as mock_validate, \
             patch('app.services.location_service.location_service.calculate_distance') as mock_distance:
            
            mock_validate.return_value = True
            mock_distance.return_value = 30.5
            
            response = self.client.post(
                "/api/v1/locations/distance",
                json={
                    "origin": {"lat": 23.6739, "lng": 121.4015},
                    "destination": {"lat": 23.9739, "lng": 121.6015}
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["distance_km"] == 30.5
            assert data["origin"]["lat"] == 23.6739
            assert data["destination"]["lat"] == 23.9739
    
    def test_calculate_distance_invalid_origin(self, auth_headers):
        """測試無效起點座標"""
        with patch('app.services.location_service.location_service.validate_coordinates') as mock_validate:
            # 第一次調用（起點）返回 False，第二次調用（終點）返回 True
            mock_validate.side_effect = [False, True]
            
            response = self.client.post(
                "/api/v1/locations/distance",
                json={
                    "origin": {"lat": 91.0, "lng": 121.4015},  # 無效緯度
                    "destination": {"lat": 23.9739, "lng": 121.6015}
                },
                headers=auth_headers
            )
            
            assert response.status_code == 400
            assert "起點座標無效" in response.json()["detail"]
    
    def test_find_nearby_supply_stations_success(self, auth_headers, db_session):
        """測試查找附近物資站點成功"""
        # 創建測試數據
        user = User(
            email="manager@test.com",
            name="測試管理員",
            role="supply_manager",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.flush()
        
        station = SupplyStation(
            manager_id=user.id,
            name="光復物資站",
            address="光復鄉中正路1號",
            location_data={
                "coordinates": {"lat": 23.6739, "lng": 121.4015}
            },
            contact_info={"phone": "03-1234567"},
            is_active=True
        )
        db_session.add(station)
        db_session.commit()
        
        with patch('app.services.location_service.location_service.validate_coordinates') as mock_validate, \
             patch('app.services.location_service.location_service.find_nearby_supply_stations') as mock_find:
            
            mock_validate.return_value = True
            mock_find.return_value = [{
                "station": station,
                "distance_km": 0.5
            }]
            
            response = self.client.post(
                "/api/v1/locations/nearby/supply-stations",
                json={
                    "latitude": 23.6739,
                    "longitude": 121.4015,
                    "radius_km": 10.0,
                    "limit": 10
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_found"] == 1
            assert len(data["stations"]) == 1
            assert data["stations"][0]["name"] == "光復物資站"
            assert data["stations"][0]["distance_km"] == 0.5
    
    def test_find_nearby_shelters_success(self, auth_headers, db_session):
        """測試查找附近避難所成功"""
        # 創建測試數據
        shelter = Shelter(
            name="光復國小避難所",
            address="光復鄉學校路1號",
            location_data={
                "coordinates": {"lat": 23.6800, "lng": 121.4100}
            },
            capacity=100,
            current_occupancy=50,
            contact_info={"phone": "03-1111111"},
            status="active"
        )
        db_session.add(shelter)
        db_session.commit()
        
        with patch('app.services.location_service.location_service.validate_coordinates') as mock_validate, \
             patch('app.services.location_service.location_service.find_nearby_shelters') as mock_find:
            
            mock_validate.return_value = True
            mock_find.return_value = [{
                "shelter": shelter,
                "distance_km": 1.2
            }]
            
            response = self.client.post(
                "/api/v1/locations/nearby/shelters",
                json={
                    "latitude": 23.6739,
                    "longitude": 121.4015,
                    "radius_km": 15.0,
                    "limit": 10
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_found"] == 1
            assert len(data["shelters"]) == 1
            assert data["shelters"][0]["name"] == "光復國小避難所"
            assert data["shelters"][0]["distance_km"] == 1.2
            assert data["shelters"][0]["capacity"] == 100
    
    def test_get_route_info_success(self, auth_headers):
        """測試路線查詢成功"""
        with patch('app.services.location_service.location_service.validate_coordinates') as mock_validate, \
             patch('app.services.location_service.location_service.get_route_distance_duration') as mock_route:
            
            mock_validate.return_value = True
            mock_route.return_value = {
                "distance": {"text": "30.5 公里", "value": 30500},
                "duration": {"text": "45 分鐘", "value": 2700},
                "status": "OK"
            }
            
            response = self.client.post(
                "/api/v1/locations/route",
                json={
                    "origin": {"lat": 23.6739, "lng": 121.4015},
                    "destination": {"lat": 23.9739, "lng": 121.6015}
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["distance"]["text"] == "30.5 公里"
            assert data["duration"]["text"] == "45 分鐘"
            assert data["status"] == "OK"
    
    def test_get_route_info_not_found(self, auth_headers):
        """測試路線查詢失敗"""
        with patch('app.services.location_service.location_service.validate_coordinates') as mock_validate, \
             patch('app.services.location_service.location_service.get_route_distance_duration') as mock_route:
            
            mock_validate.return_value = True
            mock_route.return_value = None
            
            response = self.client.post(
                "/api/v1/locations/route",
                json={
                    "origin": {"lat": 23.6739, "lng": 121.4015},
                    "destination": {"lat": 23.9739, "lng": 121.6015}
                },
                headers=auth_headers
            )
            
            assert response.status_code == 404
            assert "無法計算路線資訊" in response.json()["detail"]
    
    def test_validate_coordinates_valid(self, auth_headers):
        """測試座標驗證 - 有效座標"""
        with patch('app.services.location_service.location_service.validate_coordinates') as mock_validate:
            mock_validate.return_value = True
            
            response = self.client.post(
                "/api/v1/locations/validate",
                json={"latitude": 23.6739, "longitude": 121.4015},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True
            assert data["latitude"] == 23.6739
            assert data["longitude"] == 121.4015
            assert data["message"] is None
    
    def test_validate_coordinates_invalid(self, auth_headers):
        """測試座標驗證 - 無效座標"""
        with patch('app.services.location_service.location_service.validate_coordinates') as mock_validate:
            mock_validate.return_value = False
            
            response = self.client.post(
                "/api/v1/locations/validate",
                json={"latitude": 91.0, "longitude": 121.4015},  # 無效緯度
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False
            assert data["latitude"] == 91.0
            assert data["longitude"] == 121.4015
            assert "緯度必須在 -90 到 90 之間" in data["message"]
    
    def test_unauthorized_access(self):
        """測試未授權訪問"""
        response = self.client.post(
            "/api/v1/locations/geocode",
            json={"address": "光復鄉公所"}
        )
        
        assert response.status_code == 401
    
    def test_nearby_search_invalid_radius(self, auth_headers):
        """測試無效的搜尋半徑"""
        response = self.client.post(
            "/api/v1/locations/nearby/supply-stations",
            json={
                "latitude": 23.6739,
                "longitude": 121.4015,
                "radius_km": 0,  # 無效半徑
                "limit": 10
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_nearby_search_invalid_limit(self, auth_headers):
        """測試無效的結果限制"""
        response = self.client.post(
            "/api/v1/locations/nearby/supply-stations",
            json={
                "latitude": 23.6739,
                "longitude": 121.4015,
                "radius_km": 10.0,
                "limit": 0  # 無效限制
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error


@pytest.fixture
def auth_headers(db_session):
    """創建認證標頭"""
    from app.services.auth_service import auth_service
    
    # 創建測試用戶
    user = User(
        email="test@example.com",
        name="測試用戶",
        role="volunteer",
        password_hash="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    
    # 生成 JWT token
    token = auth_service.create_access_token(data={"sub": user.email})
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def db_session():
    """創建測試資料庫會話"""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 整合測試
class TestLocationAPIIntegration:
    """地理位置 API 整合測試"""
    
    def setup_method(self):
        """測試前設置"""
        self.client = TestClient(app)
    
    def test_complete_location_workflow(self, auth_headers):
        """測試完整的地理位置工作流程"""
        # 1. 地理編碼
        with patch('app.services.location_service.location_service.geocode_address') as mock_geocode:
            mock_geocode.return_value = {
                "latitude": 23.6739,
                "longitude": 121.4015,
                "formatted_address": "970花蓮縣光復鄉中正路一段1號",
                "place_id": "ChIJtest123",
                "address_components": []
            }
            
            geocode_response = self.client.post(
                "/api/v1/locations/geocode",
                json={"address": "光復鄉公所"},
                headers=auth_headers
            )
            
            assert geocode_response.status_code == 200
            geocode_data = geocode_response.json()
        
        # 2. 座標驗證
        with patch('app.services.location_service.location_service.validate_coordinates') as mock_validate:
            mock_validate.return_value = True
            
            validate_response = self.client.post(
                "/api/v1/locations/validate",
                json={
                    "latitude": geocode_data["latitude"],
                    "longitude": geocode_data["longitude"]
                },
                headers=auth_headers
            )
            
            assert validate_response.status_code == 200
            assert validate_response.json()["is_valid"] is True
        
        # 3. 反向地理編碼
        with patch('app.services.location_service.location_service.validate_coordinates') as mock_validate, \
             patch('app.services.location_service.location_service.reverse_geocode') as mock_reverse:
            
            mock_validate.return_value = True
            mock_reverse.return_value = {
                "formatted_address": "970花蓮縣光復鄉中正路一段1號",
                "address_components": []
            }
            
            reverse_response = self.client.post(
                "/api/v1/locations/reverse-geocode",
                json={
                    "latitude": geocode_data["latitude"],
                    "longitude": geocode_data["longitude"]
                },
                headers=auth_headers
            )
            
            assert reverse_response.status_code == 200
        
        # 4. 距離計算
        with patch('app.services.location_service.location_service.validate_coordinates') as mock_validate, \
             patch('app.services.location_service.location_service.calculate_distance') as mock_distance:
            
            mock_validate.return_value = True
            mock_distance.return_value = 30.5
            
            distance_response = self.client.post(
                "/api/v1/locations/distance",
                json={
                    "origin": {
                        "lat": geocode_data["latitude"],
                        "lng": geocode_data["longitude"]
                    },
                    "destination": {"lat": 23.9739, "lng": 121.6015}
                },
                headers=auth_headers
            )
            
            assert distance_response.status_code == 200
            assert distance_response.json()["distance_km"] == 30.5