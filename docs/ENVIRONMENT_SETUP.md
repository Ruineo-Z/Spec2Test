# 环境变量配置指南

本文档介绍如何配置 Spec2Test 项目的环境变量。

## 快速开始

1. 复制环境变量模板文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，根据你的环境配置相应的值。

3. 重启应用以使配置生效。

## 配置分类

### 应用基础配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `APP_NAME` | `Spec2Test` | 应用名称 |
| `APP_VERSION` | `0.1.0` | 应用版本 |
| `DEBUG` | `false` | 是否启用调试模式 |
| `API_HOST` | `0.0.0.0` | API服务监听地址 |
| `API_PORT` | `8000` | API服务端口 |
| `API_PREFIX` | `/api/v1` | API路径前缀 |

### LLM配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `LLM_PROVIDER` | `gemini` | LLM服务提供商 (openai/gemini) |
| `OPENAI_API_KEY` | - | OpenAI API密钥 |
| `OPENAI_MODEL` | `gpt-4` | OpenAI模型名称 |
| `GEMINI_API_KEY` | - | Gemini API密钥 |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini模型名称 |
| `LLM_MAX_TOKENS` | `2000` | 最大生成token数 |
| `LLM_TEMPERATURE` | `0.1` | 生成温度 |
| `LLM_TIMEOUT` | `60` | 请求超时时间(秒) |

### 测试配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `TEST_TIMEOUT` | `30` | 测试超时时间(秒) |
| `TEST_MAX_RETRIES` | `2` | 最大重试次数 |
| `TEST_PARALLEL_WORKERS` | `4` | 并行工作进程数 |
| `TEST_OUTPUT_DIR` | `./test_output` | 测试输出目录 |
| `TEST_MAX_CASES_PER_ENDPOINT` | `10` | 每个端点最大测试用例数 |
| `TEST_INCLUDE_EDGE_CASES` | `true` | 是否包含边界测试 |
| `TEST_INCLUDE_SECURITY` | `true` | 是否包含安全测试 |

### 数据库配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DB_DRIVER` | `sqlite` | 数据库驱动 |
| `DB_HOST` | `localhost` | 数据库主机 |
| `DB_PORT` | `5432` | 数据库端口 |
| `DB_NAME` | `spec2test.db` | 数据库名称 |
| `DB_USER` | - | 数据库用户名 |
| `DB_PASSWORD` | - | 数据库密码 |

### 日志配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `LOG_FILE_ENABLED` | `true` | 是否启用文件日志 |
| `LOG_FILE_PATH` | `./logs/app.log` | 日志文件路径 |
| `LOG_CONSOLE_ENABLED` | `true` | 是否启用控制台日志 |
| `LOG_JSON_FORMAT` | `false` | 是否使用JSON格式 |

## 环境特定配置

### 开发环境

开发环境建议配置：
```bash
DEBUG=true
LOG_LEVEL=DEBUG
DB_ECHO=true
LOG_CONSOLE_COLORIZE=true
```

### 生产环境

生产环境必须配置：
```bash
DEBUG=false
SECRET_KEY=your-super-secret-production-key
OPENAI_API_KEY=your-production-openai-key
GEMINI_API_KEY=your-production-gemini-key
DB_HOST=your-production-db-host
DB_USER=your-production-db-user
DB_PASSWORD=your-production-db-password
```

### 测试环境

测试环境建议配置：
```bash
DB_NAME=spec2test_test.db
LOG_LEVEL=DEBUG
TEST_TIMEOUT=10
TEST_PARALLEL_WORKERS=2
```

## 安全注意事项

1. **永远不要将 `.env` 文件提交到版本控制系统**
2. **生产环境中使用强密码和密钥**
3. **定期轮换API密钥**
4. **限制数据库用户权限**
5. **使用HTTPS传输敏感数据**

## 配置验证

启动应用时，系统会自动验证配置的有效性。如果配置有误，会在日志中显示详细的错误信息。

你也可以使用CLI命令验证配置：
```bash
python -m app.cli config --validate
```

## 故障排除

### 常见问题

1. **API密钥无效**
   - 检查密钥是否正确
   - 确认密钥是否有相应权限
   - 检查网络连接

2. **数据库连接失败**
   - 检查数据库服务是否运行
   - 验证连接参数
   - 检查用户权限

3. **文件权限错误**
   - 确保应用有读写工作目录的权限
   - 检查日志目录权限

### 调试模式

启用调试模式获取更多信息：
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

## 配置优先级

配置的加载优先级（从高到低）：
1. 环境变量
2. `.env` 文件
3. 代码中的默认值

## 更多信息

- [项目文档](../README.md)
- [开发指南](./DEVELOPMENT.md)
- [部署指南](./DEPLOYMENT.md)
