#!/usr/bin/env python3
"""
報表API測試
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from datetime import date, timedelta
from app.main import app

def test_reporting_api():
    """測試報表API端點"""
    print("=== 報表API測試 ===")
    
    client = TestClient(app)
    
    # 測試健康檢查端點
    print("\n測試健康檢查端點...")
    try:
        response = client.get("/api/v1/reports/health")
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"回應: {data}")
            print("✓ 健康檢查端點正常")
        else:
            print("✗ 健康檢查端點異常")
            return False
    except Exception as e:
        print(f"✗ 健康檢查端點錯誤: {e}")
        return False
    
    # 測試報表模板端點
    print("\n測試報表模板端點...")
    try:
        response = client.get("/api/v1/reports/templates")
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"模板數量: {data.get('total_count', 0)}")
            print("✓ 報表模板端點正常")
        else:
            print("✗ 報表模板端點異常")
            return False
    except Exception as e:
        print(f"✗ 報表模板端點錯誤: {e}")
        return False
    
    # 測試快速摘要端點
    print("\n測試快速摘要端點...")
    try:
        response = client.get("/api/v1/reports/quick/disaster-relief-summary?days=7")
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"摘要資料: {data}")
            print("✓ 快速摘要端點正常")
        else:
            print("✗ 快速摘要端點異常")
            return False
    except Exception as e:
        print(f"✗ 快速摘要端點錯誤: {e}")
        return False
    
    print("\n✓ 所有API端點測試通過！")
    return True

def main():
    """主測試函數"""
    success = test_reporting_api()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)