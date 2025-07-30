# Spec2Test 环境变量配置指南

本文档详细说明了 Spec2Test 项目的环境变量配置方法和最佳实践。

## 快速开始

1. **复制配置模板**
   ```bash
   cp .env.example .env
   ```

2. **编辑配置文件**
   ```bash
   # 使用您喜欢的编辑器编辑 .env 文件
   nano .env
   # 或
   vim .env
   ```

3. **配置必需项**
   - 设置 LLM API 密钥（OpenAI 或 Gemini）
   - 更改生产环境的 SECRET_KEY
   - 根据需要调整其他配置

4. **验证配置**
   ```bash
   python scripts/check-env.py
   ```

## 配置分类

### 应用基础配置

```bash
# 应用信息
APP_NAME=Spec2Test
APP_VERSION=0.1.0
DEBUG=false

# API服务
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

# 安全配置
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### LLM 配置

```bash
# 选择提供商 (openai 或 gemini)
LLM_PROVIDER=gemini

# OpenAI 配置
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
OPENAI_BASE_URL=  # 可选，用于自定义端点

# Gemini 配置
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash

# 生成参数
LLM_MAX_TOKENS=2000
LLM_TEMPERATURE=0.1
LLM_TIMEOUT=60
LLM_MAX_RETRIES=3
LLM_RETRY_DELAY=1.0
```

### 测试配置

```bash
# 执行配置
TEST_TIMEOUT=30
TEST_MAX_RETRIES=2
TEST_PARALLEL_WORKERS=4

# 输出配置
TEST_OUTPUT_DIR=./test_output
TEST_KEEP_CODE=true

# 测试用例生成
TEST_MAX_CASES_PER_ENDPOINT=10
TEST_INCLUDE_EDGE_CASES=true
TEST_INCLUDE_SECURITY=true

# 报告配置
TEST_REPORT_FORMATS=["html","json"]
TEST_INCLUDE_AI_ANALYSIS=true
```

### 数据库配置

```bash
# 基础配置
DB_DRIVER=sqlite
DB_HOST=localhost
DB_PORT=5432
DB_NAME=spec2test.db
DB_USER=your-db-user
DB_PASSWORD=your-db-password

# 连接池配置
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# 调试配置
DB_ECHO=false
DB_ECHO_POOL=false
```

### 日志配置

```bash
# 基础配置
LOG_LEVEL=INFO
LOG_FORMAT={time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}

# 文件日志
LOG_FILE_ENABLED=true
LOG_FILE_PATH=./logs/app.log
LOG_FILE_ROTATION=10 MB
LOG_FILE_RETENTION=30 days

# 控制台日志
LOG_CONSOLE_ENABLED=true
LOG_CONSOLE_COLORIZE=true

# 高级配置
LOG_JSON_FORMAT=false
LOG_MASK_SENSITIVE=true
LOG_SENSITIVE_FIELDS=["password","token","api_key","secret"]
```

## 环境特定配置

### 开发环境

```bash
DEBUG=true
LOG_LEVEL=DEBUG
DB_ECHO=true
TEST_PARALLEL_WORKERS=2
```

### 生产环境

```bash
DEBUG=false
SECRET_KEY=your-super-secret-production-key
LOG_LEVEL=INFO
DB_ECHO=false
CORS_ORIGINS=["https://yourdomain.com"]
```

### 测试环境

```bash
DB_NAME=spec2test_test.db
LOG_LEVEL=DEBUG
TEST_TIMEOUT=10
TEST_PARALLEL_WORKERS=1
```

## 配置验证

### 1. 使用环境检查脚本

```bash
# 检查环境变量配置
python scripts/check-env.py
```

脚本会检查：
- `.env` 文件是否存在
- 必需的环境变量是否配置
- 数据库配置是否正确
- 相关目录是否存在
- 配置格式是否正确

### 2. 使用CLI工具验证配置

```bash
# 使用CLI工具验证配置
python -m app.cli config --validate
```

### 3. 快速配置测试

```bash
# 测试配置加载
python -c "from app.config.settings import settings; print('✅ 配置加载成功')"
```

## 安全注意事项

1. **API 密钥安全**
   - 不要在代码中硬编码 API 密钥
   - 使用环境变量或安全的密钥管理服务
   - 定期轮换 API 密钥

2. **生产环境配置**
   - 更改默认的 SECRET_KEY
   - 设置适当的 CORS 策略
   - 禁用调试模式
   - 使用 HTTPS

3. **文件权限**
   ```bash
   # 设置 .env 文件权限
   chmod 600 .env
   ```

4. **版本控制**
   - `.env` 文件已在 `.gitignore` 中
   - 只提交 `.env.example` 文件
   - 不要在版本控制中包含真实的密钥

## 故障排除

### 常见问题

1. **配置加载失败**
   ```
   ❌ 配置加载失败: error parsing value for field "cors_origins"
   ```
   **解决方案**: 检查 JSON 格式的配置项，确保使用双引号
   ```bash
   # 错误
   CORS_ORIGINS=['*']
   # 正确
   CORS_ORIGINS=["*"]
   ```

2. **数据库连接失败**
   ```
   ❌ 数据库连接失败
   ```
   **解决方案**: 检查数据库配置和权限
   ```bash
   # 检查 SQLite 文件权限
   ls -la spec2test.db
   # 检查目录权限
   ls -la ./
   ```

3. **LLM API 调用失败**
   ```
   ❌ LLM API 调用失败
   ```
   **解决方案**: 验证 API 密钥和网络连接
   ```bash
   # 测试 API 密钥
   python -c "from app.config.settings import settings; print(f'Provider: {settings.llm.provider}')"
   ```

### 调试技巧

1. **启用详细日志**
   ```bash
   LOG_LEVEL=DEBUG
   DB_ECHO=true
   ```

2. **检查配置值**
   ```bash
   python -c "from app.config.settings import settings; import json; print(json.dumps(settings.dict(), indent=2, default=str))"
   ```

3. **验证环境变量**
   ```bash
   env | grep -E '^(APP_|LLM_|TEST_|DB_|LOG_)'
   ```

## 配置优先级

配置加载的优先级顺序（从高到低）：

1. 环境变量
2. `.env` 文件
3. 代码中的默认值

## 最佳实践

1. **使用配置模板**
   - 始终从 `.env.example` 开始
   - 保持模板文件更新

2. **环境分离**
   - 为不同环境使用不同的配置文件
   - 使用环境变量覆盖特定设置

3. **文档化配置**
   - 为每个配置项添加注释
   - 说明配置的影响和推荐值

4. **定期检查**
   - 定期运行配置验证脚本
   - 监控配置相关的错误日志

5. **备份配置**
   - 备份重要的配置文件
   - 使用配置管理工具

## 相关文档

- [README.md](./README.md) - 项目概述和快速开始
- [API 文档](./docs/api.md) - API 接口说明
- [开发指南](./docs/development.md) - 开发环境设置
