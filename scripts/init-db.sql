-- Spec2Test数据库初始化脚本
-- 创建开发和测试数据库

-- 创建测试数据库
CREATE DATABASE spec2test_test;

-- 创建扩展（如果需要）
\c spec2test;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\c spec2test_test;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 创建用户（如果需要）
-- CREATE USER spec2test_user WITH PASSWORD 'spec2test_password';
-- GRANT ALL PRIVILEGES ON DATABASE spec2test TO spec2test_user;
-- GRANT ALL PRIVILEGES ON DATABASE spec2test_test TO spec2test_user;

-- 输出初始化完成信息
\echo 'Database initialization completed successfully!'
