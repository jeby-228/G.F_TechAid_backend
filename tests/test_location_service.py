"""
地理位置服務的單元測試
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.location_service import LocationService, location_service
from app.models.supply import SupplyStation
from app.models.system import Shelter
from app.models.user import User


class TestLocationService:
    """地理位置服務測試類別"""
    
    def setup_method(self):
        """測試前設置"""
        self.location_service = LocationService()
    
    def test_calculate_distance(self):
        """測試距離計算功能"""
        # 測試光復鄉公所到花蓮市的距離（大約30公里）
        guangfu_lat, guangfu_lng = 23.6739, 121.4015
        hualien_lat, hualien_lng = 23.9739, 121.6015
        
        distance = self.location_service.calculate_distance(
            guangfu_lat, guangfu_lng, hualien_lat, hualien_lng
        )
        
        # 驗證距離在合理範圍內（35-45公里）
        assert 35 <= distance <= 45
        assert isinstance(distance, float)
    
    def test_calculate_distance_same_point(self):
        """測試相同點的距離計算"""
        lat, lng = 23.6739, 121.4015
        
        distance = self.location_service.calculate_distance(lat, lng, lat, lng)
        
        assert distance == 0.0
    
    def test_validate_coordinates_valid(self):
        """測試有效座標驗證"""
        # 光復鄉的座標
        assert self.location_service.validate_coordinates(23.6739, 121.4015) is True
        
        # 台北的座標
        assert self.location_service.validate_coordinates(25.0330, 121.5654) is True
    
    def test_validate_coordinates_invalid_range(self):
        """測試無效範圍的座標"""
        # 緯度超出範圍
        assert self.location_service.validate_coordinates(91.0, 121.4015) is False
        assert self.location_service.validate_coordinates(-91.0, 121.4015) is False
        
        # 經度超出範圍
        assert self.location_service.validate_coordinates(23.6739, 181.0) is False
        assert self.location_service.validate_coordinates(23.6739, -181.0) is False
    
    def test_validate_coordinates_outside_taiwan(self):
        """測試台灣範圍外的座標"""
        # 日本東京的座標
        assert self.location_service.validate_coordinates(35.6762, 139.6503) is False
        
        # 中國北京的座標
        assert self.location_service.validate_coordinates(39.9042, 116.4074) is False
    
    @pytest.mark.asyncio
    async def test_geocode_address_without_api_key(self):
        """測試沒有 API Key 時的地理編碼"""
        # 暫時移除 API Key
        original_key = self.location_service.google_maps_api_key
        self.location_service.google_maps_api_key = None
        
        try:
            result = await self.location_service.geocode_address("光復鄉公所")
            
            assert result is not None
            assert result["latitude"] == 23.6739
            assert result["longitude"] == 121.4015
            assert "光復鄉" in result["formatted_address"]
            
        finally:
            # 恢復原始 API Key
            self.location_service.google_maps_api_key = original_key
    
    @pytest.mark.asyncio
    async def test_reverse_geocode_without_api_key(self):
        """測試沒有 API Key 時的反向地理編碼"""
        # 暫時移除 API Key
        original_key = self.location_service.google_maps_api_key
        self.location_service.google_maps_api_key = None
        
        try:
            result = await self.location_service.reverse_geocode(23.6739, 121.4015)
            
            assert result is not None
            assert "緯度: 23.6739, 經度: 121.4015" in result["formatted_address"]
            assert result["address_components"] == []
            
        finally:
            # 恢復原始 API Key
            self.location_service.google_maps_api_key = original_key
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_geocode_address_with_api_success(self, mock_get):
        """測試使用 API 成功進行地理編碼"""
        # 模擬 Google Maps API 回應
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "results": [{
                "formatted_address": "970花蓮縣光復鄉中正路一段1號",
                "geometry": {
                    "location": {"lat": 23.6739, "lng": 121.4015}
                },
                "place_id": "ChIJtest123",
                "address_components": [
                    {
                        "long_name": "光復鄉",
                        "short_name": "光復鄉",
                        "types": ["locality", "political"]
                    }
                ]
            }]
        }
        mock_get.return_value = mock_response
        
        # 設置 API Key
        self.location_service.google_maps_api_key = "test_api_key"
        
        result = await self.location_service.geocode_address("光復鄉公所")
        
        assert result is not None
        assert result["latitude"] == 23.6739
        assert result["longitude"] == 121.4015
        assert result["formatted_address"] == "970花蓮縣光復鄉中正路一段1號"
        assert result["place_id"] == "ChIJtest123"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_geocode_address_api_failure(self, mock_get):
        """測試 API 調用失敗時的處理"""
        # 模擬 API 調用失敗
        mock_get.side_effect = Exception("Network error")
        
        # 設置 API Key
        self.location_service.google_maps_api_key = "test_api_key"
        
        result = await self.location_service.geocode_address("光復鄉公所")
        
        # 應該返回預設座標
        assert result is not None
        assert result["latitude"] == 23.6739
        assert result["longitude"] == 121.4015
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_get_route_distance_duration_success(self, mock_get):
        """測試路線查詢成功"""
        # 模擬 Distance Matrix API 回應
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "rows": [{
                "elements": [{
                    "status": "OK",
                    "distance": {"text": "30.5 公里", "value": 30500},
                    "duration": {"text": "45 分鐘", "value": 2700}
                }]
            }]
        }
        mock_get.return_value = mock_response
        
        # 設置 API Key
        self.location_service.google_maps_api_key = "test_api_key"
        
        result = await self.location_service.get_route_distance_duration(
            23.6739, 121.4015, 23.9739, 121.6015
        )
        
        assert result is not None
        assert result["distance"]["text"] == "30.5 公里"
        assert result["distance"]["value"] == 30500
        assert result["duration"]["text"] == "45 分鐘"
        assert result["duration"]["value"] == 2700
        assert result["status"] == "OK"
    
    @pytest.mark.asyncio
    async def test_get_route_distance_duration_without_api_key(self):
        """測試沒有 API Key 時的路線查詢"""
        # 暫時移除 API Key
        original_key = self.location_service.google_maps_api_key
        self.location_service.google_maps_api_key = None
        
        try:
            result = await self.location_service.get_route_distance_duration(
                23.6739, 121.4015, 23.9739, 121.6015
            )
            
            assert result is not None
            assert result["status"] == "ESTIMATED"
            assert "公里" in result["distance"]["text"]
            assert "分鐘" in result["duration"]["text"]
            assert result["distance"]["value"] > 0
            assert result["duration"]["value"] > 0
            
        finally:
            # 恢復原始 API Key
            self.location_service.google_maps_api_key = original_key
    
    def test_find_nearby_supply_stations(self, db_session):
        """測試查找附近物資站點"""
        # 創建測試用戶
        user = User(
            email="manager@test.com",
            name="測試管理員",
            role="supply_manager",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.flush()
        
        # 創建測試物資站點
        station1 = SupplyStation(
            manager_id=user.id,
            name="光復物資站",
            address="光復鄉中正路1號",
            location_data={
                "coordinates": {"lat": 23.6739, "lng": 121.4015}
            },
            contact_info={"phone": "03-1234567"},
            is_active=True
        )
        
        station2 = SupplyStation(
            manager_id=user.id,
            name="花蓮物資站",
            address="花蓮市中山路1號",
            location_data={
                "coordinates": {"lat": 23.9739, "lng": 121.6015}
            },
            contact_info={"phone": "03-7654321"},
            is_active=True
        )
        
        # 創建非活躍站點（不應該被找到）
        station3 = SupplyStation(
            manager_id=user.id,
            name="關閉物資站",
            address="關閉地址",
            location_data={
                "coordinates": {"lat": 23.7000, "lng": 121.4200}
            },
            contact_info={"phone": "03-0000000"},
            is_active=False
        )
        
        db_session.add_all([station1, station2, station3])
        db_session.commit()
        
        # 從光復鄉公所附近搜尋（半徑50公里）
        nearby_stations = self.location_service.find_nearby_supply_stations(
            db_session, 23.6739, 121.4015, radius_km=50.0, limit=10
        )
        
        # 驗證結果
        assert len(nearby_stations) == 2  # 只有活躍的站點
        
        # 第一個應該是最近的（光復物資站）
        assert nearby_stations[0]["station"].name == "光復物資站"
        assert nearby_stations[0]["distance_km"] < 1.0  # 很近
        
        # 第二個是花蓮物資站
        assert nearby_stations[1]["station"].name == "花蓮物資站"
        assert nearby_stations[1]["distance_km"] > 20.0  # 較遠
    
    def test_find_nearby_shelters(self, db_session):
        """測試查找附近避難所"""
        # 創建測試避難所
        shelter1 = Shelter(
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
        
        shelter2 = Shelter(
            name="花蓮體育館避難所",
            address="花蓮市體育路1號",
            location_data={
                "coordinates": {"lat": 23.9800, "lng": 121.6100}
            },
            capacity=500,
            current_occupancy=200,
            contact_info={"phone": "03-2222222"},
            status="active"
        )
        
        # 創建關閉的避難所（不應該被找到）
        shelter3 = Shelter(
            name="關閉避難所",
            address="關閉地址",
            location_data={
                "coordinates": {"lat": 23.7000, "lng": 121.4200}
            },
            capacity=200,
            current_occupancy=0,
            contact_info={"phone": "03-0000000"},
            status="closed"
        )
        
        db_session.add_all([shelter1, shelter2, shelter3])
        db_session.commit()
        
        # 從光復鄉公所附近搜尋（半徑50公里）
        nearby_shelters = self.location_service.find_nearby_shelters(
            db_session, 23.6739, 121.4015, radius_km=50.0, limit=10
        )
        
        # 驗證結果
        assert len(nearby_shelters) == 2  # 只有活躍的避難所
        
        # 第一個應該是最近的（光復國小避難所）
        assert nearby_shelters[0]["shelter"].name == "光復國小避難所"
        assert nearby_shelters[0]["distance_km"] < 2.0  # 很近
        
        # 第二個是花蓮體育館避難所
        assert nearby_shelters[1]["shelter"].name == "花蓮體育館避難所"
        assert nearby_shelters[1]["distance_km"] > 20.0  # 較遠
    
    def test_find_nearby_supply_stations_empty_result(self, db_session):
        """測試沒有附近物資站點的情況"""
        nearby_stations = self.location_service.find_nearby_supply_stations(
            db_session, 23.6739, 121.4015, radius_km=1.0, limit=10
        )
        
        assert len(nearby_stations) == 0
    
    def test_find_nearby_supply_stations_with_limit(self, db_session):
        """測試限制返回結果數量"""
        # 創建測試用戶
        user = User(
            email="manager@test.com",
            name="測試管理員",
            role="supply_manager",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.flush()
        
        # 創建多個物資站點
        stations = []
        for i in range(5):
            station = SupplyStation(
                manager_id=user.id,
                name=f"物資站{i+1}",
                address=f"地址{i+1}",
                location_data={
                    "coordinates": {
                        "lat": 23.6739 + (i * 0.001),  # 稍微不同的座標
                        "lng": 121.4015 + (i * 0.001)
                    }
                },
                contact_info={"phone": f"03-123456{i}"},
                is_active=True
            )
            stations.append(station)
        
        db_session.add_all(stations)
        db_session.commit()
        
        # 限制返回3個結果
        nearby_stations = self.location_service.find_nearby_supply_stations(
            db_session, 23.6739, 121.4015, radius_km=10.0, limit=3
        )
        
        assert len(nearby_stations) == 3
    
    def test_get_default_coordinates(self):
        """測試獲取預設座標"""
        result = self.location_service._get_default_coordinates("測試地址")
        
        assert result["latitude"] == 23.6739
        assert result["longitude"] == 121.4015
        assert "光復鄉" in result["formatted_address"]
        assert "測試地址" in result["formatted_address"]
        assert result["place_id"] is None
        assert len(result["address_components"]) > 0


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
class TestLocationServiceIntegration:
    """地理位置服務整合測試"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """測試完整的地理位置處理流程"""
        service = LocationService()
        
        # 1. 地理編碼
        address = "花蓮縣光復鄉"
        geocode_result = await service.geocode_address(address)
        assert geocode_result is not None
        
        lat = geocode_result["latitude"]
        lng = geocode_result["longitude"]
        
        # 2. 驗證座標
        assert service.validate_coordinates(lat, lng) is True
        
        # 3. 反向地理編碼
        reverse_result = await service.reverse_geocode(lat, lng)
        assert reverse_result is not None
        
        # 4. 計算距離（到花蓮市）
        hualien_lat, hualien_lng = 23.9739, 121.6015
        distance = service.calculate_distance(lat, lng, hualien_lat, hualien_lng)
        assert distance > 0
        
        # 5. 路線查詢
        route_result = await service.get_route_distance_duration(
            lat, lng, hualien_lat, hualien_lng
        )
        assert route_result is not None
        assert route_result["distance"]["value"] > 0
        assert route_result["duration"]["value"] > 0