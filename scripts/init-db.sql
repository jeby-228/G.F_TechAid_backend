-- 初始化資料庫腳本
-- 此腳本會在 Docker 容器啟動時自動執行

-- 建立資料庫（如果不存在）
SELECT 'CREATE DATABASE disaster_relief'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'disaster_relief')\gexec

-- 建立必要的擴展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";