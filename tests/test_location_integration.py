"""
地理位置功能整合測試
"""

import pytest
import asyncio
from unittest.mock import patch

from app.services.location_service import location_service
from app.utils.location_helpers import (
    process_location_data,
    extract_coordinates_from_location_data,
    calculate_distance_between_locations,
    validate_location_data,
    format_location_for_display,
    create_location_data_from_coordinates,
    create_location_data_from_address
)


class TestLocationIntegration:
    """地理位置功能整合測試"""
    
    @pytest.mark.asyncio
    async def test_process_location_data_with_address_only(self):
        """測試僅使用地址處理位置資料"""
        with patch.object(location_service, 'geocode_address') as mock_geocode:
            mock_geocode.return_value = {
                "latitude": 23.6739,
                "longitude": 121.4015,
                "formatted_address": "970花蓮縣光復鄉中正路一段1號",
                "place_id": "ChIJtest123"
            }
            
            result = await process_location_data("光復鄉公所")
            
            assert result["address"] == "光復鄉公所"
            assert result["coordinates"]["lat"] == 23.6739
            assert result["coordinates"]["lng"] == 121.4015
            assert "光復鄉" in result["formatted_address"]
    
    @pytest.mark.asyncio
    async def test_process_location_data_with_coordinates(self):
        """測試使用座標處理位置資料"""
        with patch.object(location_service, 'validate_coordinates') as mock_validate, \
             patch.object(location_service, 'reverse_geocode') as mock_reverse:
            
            mock_validate.return_value = True
            mock_reverse.return_value = {
                "formatted_address": "970花蓮縣光復鄉中正路一段1號",
                "place_id": "ChIJtest123"
            }
            
            coordinates = {"lat": 23.6739, "lng": 121.4015}
            result = await process_location_data("光復鄉公所", coordinates)
            
            assert result["address"] == "光復鄉公所"
            assert result["coordinates"]["lat"] == 23.6739
            assert result["coordinates"]["lng"] == 121.4015
            assert "光復鄉" in result["formatted_address"]
    
    def test_extract_coordinates_from_location_data(self):
        """測試從位置資料提取座標"""
        location_data = {
            "address": "光復鄉公所",
            "coordinates": {"lat": 23.6739, "lng": 121.4015}
        }
        
        coords = extract_coordinates_from_location_data(location_data)
        
        assert coords is not None
        assert coords[0] == 23.6739
        assert coords[1] == 121.4015
    
    def test_extract_coordinates_invalid_data(self):
        """測試提取無效座標資料"""
        # 空資料
        assert extract_coordinates_from_location_data(None) is None
        assert extract_coordinates_from_location_data({}) is None
        
        # 缺少座標
        location_data = {"address": "光復鄉公所"}
        assert extract_coordinates_from_location_data(location_data) is None
        
        # 無效座標格式
        location_data = {"coordinates": {"lat": "invalid", "lng": 121.4015}}
        assert extract_coordinates_from_location_data(location_data) is None
    
    def test_calculate_distance_between_locations(self):
        """測試計算兩個位置間的距離"""
        location1 = {
            "address": "光復鄉公所",
            "coordinates": {"lat": 23.6739, "lng": 121.4015}
        }
        
        location2 = {
            "address": "花蓮市公所",
            "coordinates": {"lat": 23.9739, "lng": 121.6015}
        }
        
        distance = calculate_distance_between_locations(location1, location2)
        
        assert distance is not None
        assert distance > 30  # 大約39公里
        assert distance < 50
    
    def test_calculate_distance_invalid_locations(self):
        """測試計算無效位置間的距離"""
        location1 = {"address": "光復鄉公所"}  # 沒有座標
        location2 = {"coordinates": {"lat": 23.9739, "lng": 121.6015}}
        
        distance = calculate_distance_between_locations(location1, location2)
        
        assert distance is None
    
    def test_validate_location_data(self):
        """測試位置資料驗證"""
        # 有效的位置資料
        valid_location = {
            "address": "光復鄉公所",
            "coordinates": {"lat": 23.6739, "lng": 121.4015}
        }
        
        with patch.object(location_service, 'validate_coordinates') as mock_validate:
            mock_validate.return_value = True
            assert validate_location_data(valid_location) is True
        
        # 只有地址的位置資料
        address_only_location = {"address": "光復鄉公所"}
        assert validate_location_data(address_only_location) is True
        
        # 無效的位置資料
        assert validate_location_data(None) is False
        assert validate_location_data({}) is False
        assert validate_location_data({"coordinates": {"lat": 23.6739, "lng": 121.4015}}) is False  # 沒有地址
    
    def test_format_location_for_display(self):
        """測試位置資料格式化顯示"""
        # 有格式化地址
        location_with_formatted = {
            "address": "光復鄉公所",
            "formatted_address": "970花蓮縣光復鄉中正路一段1號",
            "coordinates": {"lat": 23.6739, "lng": 121.4015}
        }
        
        result = format_location_for_display(location_with_formatted)
        assert result == "970花蓮縣光復鄉中正路一段1號"
        
        # 只有原始地址
        location_with_address = {
            "address": "光復鄉公所",
            "coordinates": {"lat": 23.6739, "lng": 121.4015}
        }
        
        result = format_location_for_display(location_with_address)
        assert result == "光復鄉公所"
        
        # 只有座標
        location_with_coords = {
            "coordinates": {"lat": 23.6739, "lng": 121.4015}
        }
        
        result = format_location_for_display(location_with_coords)
        assert "緯度: 23.6739" in result
        assert "經度: 121.4015" in result
        
        # 空資料
        result = format_location_for_display(None)
        assert result == "未知位置"
    
    def test_create_location_data_from_coordinates(self):
        """測試從座標創建位置資料"""
        result = create_location_data_from_coordinates(23.6739, 121.4015, "光復鄉公所")
        
        assert result["address"] == "光復鄉公所"
        assert result["coordinates"]["lat"] == 23.6739
        assert result["coordinates"]["lng"] == 121.4015
        
        # 沒有地址的情況
        result = create_location_data_from_coordinates(23.6739, 121.4015)
        assert "緯度: 23.6739" in result["address"]
        assert "經度: 121.4015" in result["address"]
    
    def test_create_location_data_from_address(self):
        """測試從地址創建位置資料"""
        result = create_location_data_from_address("光復鄉公所")
        
        assert result["address"] == "光復鄉公所"
        assert result["coordinates"] == {}
        assert result["formatted_address"] is None
    
    @pytest.mark.asyncio
    async def test_location_workflow_integration(self):
        """測試完整的位置處理工作流程"""
        # 1. 創建位置資料
        location_data = create_location_data_from_address("光復鄉公所")
        
        # 2. 驗證位置資料
        assert validate_location_data(location_data) is True
        
        # 3. 處理位置資料（地理編碼）
        with patch.object(location_service, 'geocode_address') as mock_geocode:
            mock_geocode.return_value = {
                "latitude": 23.6739,
                "longitude": 121.4015,
                "formatted_address": "970花蓮縣光復鄉中正路一段1號",
                "place_id": "ChIJtest123"
            }
            
            processed_data = await process_location_data(
                location_data["address"], 
                location_data.get("coordinates")
            )
        
        # 4. 提取座標
        coords = extract_coordinates_from_location_data(processed_data)
        assert coords is not None
        
        # 5. 格式化顯示
        display_text = format_location_for_display(processed_data)
        assert "光復鄉" in display_text
        
        # 6. 計算與另一個位置的距離
        another_location = create_location_data_from_coordinates(23.9739, 121.6015, "花蓮市")
        distance = calculate_distance_between_locations(processed_data, another_location)
        assert distance is not None
        assert distance > 0


# 效能測試
class TestLocationPerformance:
    """地理位置功能效能測試"""
    
    def test_distance_calculation_performance(self):
        """測試距離計算效能"""
        import time
        
        start_time = time.time()
        
        # 計算100次距離
        for i in range(100):
            distance = location_service.calculate_distance(
                23.6739, 121.4015,  # 光復鄉
                23.9739, 121.6015   # 花蓮市
            )
            assert distance > 0
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 100次計算應該在1秒內完成
        assert elapsed_time < 1.0
        print(f"100次距離計算耗時: {elapsed_time:.3f}秒")
    
    def test_coordinate_validation_performance(self):
        """測試座標驗證效能"""
        import time
        
        test_coordinates = [
            (23.6739, 121.4015),  # 有效座標
            (91.0, 121.4015),     # 無效緯度
            (23.6739, 181.0),     # 無效經度
            (35.6762, 139.6503),  # 台灣範圍外
        ]
        
        start_time = time.time()
        
        # 驗證1000次座標
        for i in range(250):
            for lat, lng in test_coordinates:
                location_service.validate_coordinates(lat, lng)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 1000次驗證應該在0.1秒內完成
        assert elapsed_time < 0.1
        print(f"1000次座標驗證耗時: {elapsed_time:.3f}秒")