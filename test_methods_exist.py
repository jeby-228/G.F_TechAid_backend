#!/usr/bin/env python3
"""
測試方法是否存在
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 重新載入模組
import importlib
import app.services.reporting_service
importlib.reload(app.services.reporting_service)

from app.services.reporting_service import reporting_service

def test_methods_exist():
    """測試方法是否存在"""
    print("檢查報表服務方法...")
    
    methods_to_check = [
        '_generate_csv_export',
        '_generate_excel_export', 
        '_generate_json_export',
        '_export_tasks_data',
        '_export_needs_data',
        '_export_supplies_data',
        '_export_users_data',
        '_export_logs_data',
        '_collect_comprehensive_analysis_data'
    ]
    
    for method_name in methods_to_check:
        if hasattr(reporting_service, method_name):
            print(f"✓ {method_name} 存在")
        else:
            print(f"✗ {method_name} 不存在")
    
    # 測試基本功能
    print("\n測試基本功能...")
    try:
        # 測試CSV匯出
        test_data = [{"項目": "測試", "數量": 1}]
        csv_result = reporting_service._generate_csv_export(test_data)
        print(f"✓ CSV匯出功能正常，結果長度: {len(csv_result)}")
    except Exception as e:
        print(f"✗ CSV匯出功能異常: {e}")
    
    try:
        # 測試Excel匯出
        excel_result = reporting_service._generate_excel_export(test_data)
        print(f"✓ Excel匯出功能正常，結果長度: {len(excel_result)}")
    except Exception as e:
        print(f"✗ Excel匯出功能異常: {e}")
    
    try:
        # 測試JSON匯出
        json_result = reporting_service._generate_json_export(test_data)
        print(f"✓ JSON匯出功能正常，結果長度: {len(json_result)}")
    except Exception as e:
        print(f"✗ JSON匯出功能異常: {e}")

if __name__ == "__main__":
    test_methods_exist()