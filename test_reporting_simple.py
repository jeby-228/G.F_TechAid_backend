#!/usr/bin/env python3
"""
簡單的報表功能測試
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.services.reporting_service import reporting_service

def test_pdf_generation():
    """測試PDF生成功能"""
    print("測試PDF報表生成...")
    
    # 建立測試資料
    test_data = {
        "report_title": "測試報表",
        "period": {
            "start_date": "2024-01-01",
            "end_date": "2024-01-07",
            "days": 7
        },
        "summary": {
            "total_items": 10,
            "completed_items": 8,
            "completion_rate": 80.0
        },
        "details": {
            "items": [
                {"項目": "測試項目1", "狀態": "完成", "數量": 5},
                {"項目": "測試項目2", "狀態": "進行中", "數量": 3}
            ]
        },
        "generated_at": "2024-01-07 12:00:00"
    }
    
    try:
        # 生成PDF
        pdf_bytes = reporting_service._generate_pdf_report(test_data, "測試報表")
        
        # 驗證PDF生成成功
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
        
        print("✓ PDF報表生成成功")
        print(f"  檔案大小: {len(pdf_bytes)} bytes")
        
        # 儲存測試檔案
        with open("test_report.pdf", "wb") as f:
            f.write(pdf_bytes)
        print("  測試檔案已儲存為 test_report.pdf")
        
    except Exception as e:
        print(f"✗ PDF報表生成失敗: {e}")
        return False
    
    return True

def test_csv_generation():
    """測試CSV生成功能"""
    print("\n測試CSV報表生成...")
    
    # 建立測試資料
    test_data = {
        "report_title": "測試報表",
        "period": {
            "start_date": "2024-01-01",
            "end_date": "2024-01-07",
            "days": 7
        },
        "details": {
            "items": [
                {"項目": "測試項目1", "狀態": "完成", "數量": 5},
                {"項目": "測試項目2", "狀態": "進行中", "數量": 3}
            ]
        },
        "generated_at": "2024-01-07 12:00:00"
    }
    
    try:
        # 生成CSV
        csv_bytes = reporting_service._generate_csv_report(test_data)
        
        # 驗證CSV生成成功
        assert isinstance(csv_bytes, bytes)
        assert len(csv_bytes) > 0
        
        # 驗證CSV內容
        csv_content = csv_bytes.decode('utf-8-sig')
        assert "測試報表" in csv_content
        assert "項目,狀態,數量" in csv_content
        assert "測試項目1,完成,5" in csv_content
        
        print("✓ CSV報表生成成功")
        print(f"  檔案大小: {len(csv_bytes)} bytes")
        
        # 儲存測試檔案
        with open("test_report.csv", "wb") as f:
            f.write(csv_bytes)
        print("  測試檔案已儲存為 test_report.csv")
        
    except Exception as e:
        print(f"✗ CSV報表生成失敗: {e}")
        return False
    
    return True

def test_excel_generation():
    """測試Excel生成功能"""
    print("\n測試Excel報表生成...")
    
    # 建立測試資料
    test_data = {
        "report_title": "測試報表",
        "period": {
            "start_date": "2024-01-01",
            "end_date": "2024-01-07",
            "days": 7
        },
        "summary": {
            "total_items": 10,
            "completed_items": 8
        },
        "details": {
            "items": [
                {"項目": "測試項目1", "狀態": "完成", "數量": 5},
                {"項目": "測試項目2", "狀態": "進行中", "數量": 3}
            ]
        },
        "generated_at": "2024-01-07 12:00:00"
    }
    
    try:
        # 生成Excel
        excel_bytes = reporting_service._generate_excel_report(test_data, "測試報表")
        
        # 驗證Excel生成成功
        assert isinstance(excel_bytes, bytes)
        assert len(excel_bytes) > 0
        assert excel_bytes.startswith(b'PK')  # ZIP格式標頭
        
        print("✓ Excel報表生成成功")
        print(f"  檔案大小: {len(excel_bytes)} bytes")
        
        # 儲存測試檔案
        with open("test_report.xlsx", "wb") as f:
            f.write(excel_bytes)
        print("  測試檔案已儲存為 test_report.xlsx")
        
    except Exception as e:
        print(f"✗ Excel報表生成失敗: {e}")
        return False
    
    return True

def main():
    """主測試函數"""
    print("=== 報表功能測試 ===")
    
    success_count = 0
    total_tests = 3
    
    # 執行測試
    if test_pdf_generation():
        success_count += 1
    
    if test_csv_generation():
        success_count += 1
    
    if test_excel_generation():
        success_count += 1
    
    # 顯示結果
    print(f"\n=== 測試結果 ===")
    print(f"成功: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("✓ 所有報表功能測試通過！")
        return True
    else:
        print("✗ 部分測試失敗")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)