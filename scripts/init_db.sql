-- Spec2Test 数据库初始化SQL脚本
-- 用于Docker容器启动时的数据库初始化

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 创建系统配置表（如果不存在）
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建API密钥表（如果不存在）
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    permissions JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE
);

-- 插入默认系统配置
INSERT INTO system_config (key, value, description) VALUES
    ('max_file_size', '10485760', 'Maximum file size in bytes (10MB)'),
    ('supported_formats', '["json", "yaml", "yml", "md"]', 'Supported document formats'),
    ('default_test_timeout', '30', 'Default test timeout in seconds'),
    ('max_concurrent_tests', '10', 'Maximum concurrent test executions'),
    ('llm_request_timeout', '60', 'LLM request timeout in seconds'),
    ('task_retry_count', '3', 'Default task retry count'),
    ('cache_expire_time', '3600', 'Default cache expiration time in seconds')
ON CONFLICT (key) DO NOTHING;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(key);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为系统配置表创建更新时间触发器
DROP TRIGGER IF EXISTS update_system_config_updated_at ON system_config;
CREATE TRIGGER update_system_config_updated_at
    BEFORE UPDATE ON system_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 为API密钥表创建更新时间触发器
DROP TRIGGER IF EXISTS update_api_keys_updated_at ON api_keys;
CREATE TRIGGER update_api_keys_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 创建用户和权限（如果需要）
-- 注意：在生产环境中应该使用更安全的密码
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'spec2test_readonly') THEN
        CREATE ROLE spec2test_readonly;
    END IF;
    
    -- 授予只读权限
    GRANT CONNECT ON DATABASE spec2test TO spec2test_readonly;
    GRANT USAGE ON SCHEMA public TO spec2test_readonly;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO spec2test_readonly;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO spec2test_readonly;
END
$$;
