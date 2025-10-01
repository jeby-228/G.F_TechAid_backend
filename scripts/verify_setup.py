#!/usr/bin/env python3
"""
驗證專案設定腳本
"""
import sys
import os
import importlib.util

def check_python_version():
    """檢查 Python 版本"""
    if sys.version_info < (3, 9):
        print("❌ Python 版本需要 3.9 或以上")
        return False
    print(f"✅ Python 版本: {sys.version}")
    return True

def check_required_modules():
    """檢查必要模組"""
    required_modules = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'alembic',
        'redis',
        'pydantic',
        'jose',
        'passlib'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module} 已安裝")
        except ImportError:
            print(f"❌ {module} 未安裝")
            missing_modules.append(module)
    
    return len(missing_modules) == 0

def check_project_structure():
    """檢查專案結構"""
    required_dirs = [
        'app',
        'app/api',
        'app/core',
        'app/models',
        'app/schemas',
        'app/services',
        'app/utils',
        'app/crud',
        'app/middleware',
        'app/dependencies',
        'alembic',
        'tests',
        'scripts'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path}/ 目錄存在")
        else:
            print(f"❌ {dir_path}/ 目錄不存在")
            missing_dirs.append(dir_path)
    
    return len(missing_dirs) == 0

def check_config_files():
    """檢查配置檔案"""
    required_files = [
        'pyproject.toml',
        'requirements.txt',
        'requirements-dev.txt',
        'Dockerfile',
        'docker-compose.yml',
        '.env.example',
        'alembic.ini',
        'Makefile'
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} 檔案存在")
        else:
            print(f"❌ {file_path} 檔案不存在")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def main():
    """主函數"""
    print("🔍 開始驗證專案設定...")
    print("=" * 50)
    
    checks = [
        ("Python 版本檢查", check_python_version),
        ("必要模組檢查", check_required_modules),
        ("專案結構檢查", check_project_structure),
        ("配置檔案檢查", check_config_files)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        print("-" * 30)
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有檢查通過！專案設定完成。")
        print("\n下一步:")
        print("1. 複製 .env.example 為 .env 並設定環境變數")
        print("2. 執行 'docker-compose up -d' 啟動服務")
        print("3. 執行 'alembic upgrade head' 建立資料庫表格")
        print("4. 訪問 http://localhost:8000/docs 查看 API 文件")
        return 0
    else:
        print("❌ 部分檢查失敗，請修正後重新執行。")
        return 1

if __name__ == "__main__":
    exit(main())