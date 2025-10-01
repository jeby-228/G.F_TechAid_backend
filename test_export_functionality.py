#!/usr/bin/env python3
"""
測試匯出功能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.services.reporting_service import reporting_service

def test_csv_export():
    """測試CSV匯出功能"""
    print("測試CSV匯出功能...")
    
    # 建立測試資料
    test_data = [
        {"項目": "測試項目1", "狀態": "完成", "數量": 5, "時間": "2024-01-01"},
        {"項目": "測試項目2", "狀態": "進行中", "數量": 3, "時間": "2024-01-02"},
        {"項目": "測試項目3", "狀態": "待處理", "數量": 8, "時間": "2024-01-03"}
    ]
    
    try:
        # 生成CSV匯出
        csv_bytes = reporting_service._generate_csv_export(test_data)
        
        # 驗證CSV匯出成功
        assert isinstance(csv_bytes, bytes)
        assert len(csv_bytes) > 0
        
        # 驗證CSV內容
        csv_content = csv_bytes.decode('utf-8-sig')
        assert "項目,狀態,數量,時間" in csv_content
        assert "測試項目1,完成,5,2024-01-01" in csv_content
        
        print("✓ CSV匯出功能正常")
        print(f"  檔案大小: {len(csv_bytes)} bytes")
        
        # 儲存測試檔案
        with open("test_export.csv", "wb") as f:
            f.write(csv_bytes)
        print("  測試檔案已儲存為 test_export.csv")
        
    except Exception as e:
        print(f"✗ CSV匯出功能失敗: {e}")
        return False
    
    return True

def test_excel_export():
    """測試Excel匯出功能"""
    print("\n測試Excel匯出功能...")
    
    # 建立測試資料
    test_data = [
        {"項目": "測試項目1", "狀態": "完成", "數量": 5, "時間": "2024-01-01"},
        {"項目": "測試項目2", "狀態": "進行中", "數量": 3, "時間": "2024-01-02"},
        {"項目": "測試項目3", "狀態": "待處理", "數量": 8, "時間": "2024-01-03"}
    ]
    
    try:
        # 生成Excel匯出
        excel_bytes = reporting_service._generate_excel_export(test_data)
        
        # 驗證Excel匯出成功
        assert isinstance(excel_bytes, bytes)
        assert len(excel_bytes) > 0
        assert excel_bytes.startswith(b'PK')  # ZIP格式標頭
        
        print("✓ Excel匯出功能正常")
        print(f"  檔案大小: {len(excel_bytes)} bytes")
        
        # 儲存測試檔案
        with open("test_export.xlsx", "wb") as f:
            f.write(excel_bytes)
        print("  測試檔案已儲存為 test_export.xlsx")
        
    except Exception as e:
        print(f"✗ Excel匯出功能失敗: {e}")
        return False
    
    return True

def test_json_export():
    """測試JSON匯出功能"""
    print("\n測試JSON匯出功能...")
    
    # 建立測試資料
    test_data = [
        {"項目": "測試項目1", "狀態": "完成", "數量": 5, "時間": "2024-01-01"},
        {"項目": "測試項目2", "狀態": "進行中", "數量": 3, "時間": "2024-01-02"},
        {"項目": "測試項目3", "狀態": "待處理", "數量": 8, "時間": "2024-01-03"}
    ]
    
    try:
        # 生成JSON匯出
        json_bytes = reporting_service._generate_json_export(test_data)
        
        # 驗證JSON匯出成功
        assert isinstance(json_bytes, bytes)
        assert len(json_bytes) > 0
        
        # 驗證JSON內容
        import json
        json_content = json.loads(json_bytes.decode('utf-8'))
        assert isinstance(json_content, list)
        assert len(json_content) == 3
        assert json_content[0]["項目"] == "測試項目1"
        
        print("✓ JSON匯出功能正常")
        print(f"  檔案大小: {len(json_bytes)} bytes")
        
        # 儲存測試檔案
        with open("test_export.json", "wb") as f:
            f.write(json_bytes)
        print("  測試檔案已儲存為 test_export.json")
        
    except Exception as e:
        print(f"✗ JSON匯出功能失敗: {e}")
        return False
    
    return True

def test_empty_data_export():
    """測試空資料匯出"""
    print("\n測試空資料匯出...")
    
    try:
        # 測試空資料的CSV匯出
        csv_bytes = reporting_service._generate_csv_export([])
        assert csv_bytes == b""
        print("✓ 空資料CSV匯出正常")
        
        # 測試空資料的Excel匯出
        excel_bytes = reporting_service._generate_excel_export([])
        assert excel_bytes == b""
        print("✓ 空資料Excel匯出正常")
        
        # 測試空資料的JSON匯出
        json_bytes = reporting_service._generate_json_export([])
        assert json_bytes == b"[]"
        print("✓ 空資料JSON匯出正常")
        
    except Exception as e:
        print(f"✗ 空資料匯出測試失敗: {e}")
        return False
    
    return True

def test_comprehensive_analysis_data_structure():
    """測試綜合分析資料結構"""
    print("\n測試綜合分析資料結構...")
    
    try:
        # 建立測試資料結構
        test_data = {
            "report_title": "綜合分析報表",
            "period": {
                "start_date": "2024-01-01",
                "end_date": "2024-01-07",
                "days": 7
            },
            "summary": {
                "disaster_progress": {"overall_completion_rate": 75.5},
                "task_completion": {"completion_rate": 80.0},
                "supply_flow": {"delivery_efficiency": 85.2},
                "user_activity": {"activity_rate": 65.3},
                "location_analysis": {"total_locations": 15}
            },
            "details": {
                "daily_trends": [
                    {"日期": "2024-01-01", "新增任務": 5, "新增需求": 3, "總活動": 8},
                    {"日期": "2024-01-02", "新增任務": 7, "新增需求": 4, "總活動": 11}
                ]
            },
            "generated_at": "2024-01-07 12:00:00"
        }
        
        # 生成PDF報表
        pdf_bytes = reporting_service._generate_pdf_report(test_data, "綜合分析報表")
        
        # 驗證PDF生成成功
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
        
        print("✓ 綜合分析報表結構正常")
        print(f"  PDF檔案大小: {len(pdf_bytes)} bytes")
        
        # 儲存測試檔案
        with open("test_comprehensive_analysis.pdf", "wb") as f:
            f.write(pdf_bytes)
        print("  測試檔案已儲存為 test_comprehensive_analysis.pdf")
        
    except Exception as e:
        print(f"✗ 綜合分析報表結構測試失敗: {e}")
        return False
    
    return True

def main():
    """主測試函數"""
    print("=== 匯出功能測試 ===")
    
    success_count = 0
    total_tests = 5
    
    # 執行測試
    if test_csv_export():
        success_count += 1
    
    if test_excel_export():
        success_count += 1
    
    if test_json_export():
        success_count += 1
    
    if test_empty_data_export():
        success_count += 1
    
    if test_comprehensive_analysis_data_structure():
        success_count += 1
    
    # 顯示結果
    print(f"\n=== 測試結果 ===")
    print(f"成功: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("✓ 所有匯出功能測試通過！")
        return True
    else:
        print("✗ 部分測試失敗")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)