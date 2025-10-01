# 災害救援平台 justfile

# 顯示可用的命令
help:
    just --fmt --unstable
    just --list --unsorted

# 安裝依賴
[group('develop')]
install:
    pip install -r requirements-dev.txt

# 啟動開發伺服器
[group('develop')]
dev:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 執行測試
[group('test')]
test:
    pytest -v --cov=app --cov-report=html

# 程式碼檢查
[group('style')]
lint:
    flake8 app/
    mypy app/

# 格式化程式碼
[group('style')]
format:
    black app/ tests/
    isort app/ tests/

# 清理暫存檔案
[group('develop')]
clean:
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -delete
    rm -rf .pytest_cache/
    rm -rf htmlcov/
    rm -rf .coverage
    rm -rf dist/
    rm -rf build/
    rm -rf *.egg-info/

[group('Docker')]
docker-build:
    docker-compose build

[group('Docker')]
docker-up:
    docker-compose up -d

[group('Docker')]
docker-down:
    docker-compose down

[group('Docker')]
docker-logs:
    docker-compose logs -f

# 資料庫遷移
[group('alembic')]
migrate:
    alembic upgrade head

# 創建新的遷移檔案（需要提供 MSG 參數）
[group('alembic')]
migrate-create MSG:
    alembic revision --autogenerate -m "{{ MSG }}"

# 回滾最後一次遷移
[group('alembic')]
migrate-rollback:
    alembic downgrade -1

# 重置資料庫
[group('alembic')]
reset-db:
    alembic downgrade base
    alembic upgrade head
