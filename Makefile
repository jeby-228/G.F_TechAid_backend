# 災害救援平台 Makefile

.PHONY: help install dev test lint format clean docker-build docker-up docker-down migrate

# 預設目標
help:
	@echo "可用的命令："
	@echo "  install     - 安裝依賴套件"
	@echo "  dev         - 啟動開發伺服器"
	@echo "  test        - 執行測試"
	@echo "  lint        - 執行程式碼檢查"
	@echo "  format      - 格式化程式碼"
	@echo "  clean       - 清理暫存檔案"
	@echo "  docker-build - 建立 Docker 映像檔"
	@echo "  docker-up   - 啟動 Docker 服務"
	@echo "  docker-down - 停止 Docker 服務"
	@echo "  migrate     - 執行資料庫遷移"

# 安裝依賴
install:
	pip install -r requirements-dev.txt

# 啟動開發伺服器
dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 執行測試
test:
	pytest -v --cov=app --cov-report=html

# 程式碼檢查
lint:
	flake8 app/
	mypy app/

# 格式化程式碼
format:
	black app/ tests/
	isort app/ tests/

# 清理暫存檔案
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

# Docker 相關命令
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# 資料庫遷移
migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(MSG)"

migrate-rollback:
	alembic downgrade -1

# 重置資料庫
reset-db:
	alembic downgrade base
	alembic upgrade head