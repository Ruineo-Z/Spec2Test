# API测试指南

本文档介绍如何测试Spec2Test的AI文档分析功能。

## 🚀 快速开始

### 1. 启动服务器

```bash
# 启动开发服务器
cd /path/to/Spec2Test
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 2. 访问API文档

打开浏览器访问：http://localhost:8001/docs

## 🔧 API端点说明

### 基础信息

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/info` | GET | 获取API基本信息 |
| `/api/v1/analyzer/health` | GET | 检查AI服务健康状态 |
| `/api/v1/analyzer/demo-spec` | GET | 获取演示OpenAPI文档 |

### 分析功能

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/analyzer/analyze` | POST | 分析OpenAPI文档（JSON格式） |
| `/api/v1/analyzer/analyze-file` | POST | 上传文件并分析 |

## 🧪 测试步骤

### 步骤1：检查服务状态

```bash
curl -X GET "http://localhost:8001/api/v1/info"
```

预期响应：
```json
{
  "version": "v1",
  "description": "Spec2Test API v1 - AI驱动的自动化测试流水线",
  "endpoints": {
    "analyzer": "AI驱动的文档质量分析",
    "parser": "文档解析和质量分析",
    "generator": "AI测试用例和代码生成",
    "executor": "测试执行和结果收集",
    "reporter": "测试报告生成和AI分析"
  }
}
```

### 步骤2：获取演示文档

```bash
curl -X GET "http://localhost:8001/api/v1/analyzer/demo-spec"
```

这将返回一个完整的OpenAPI文档示例，可用于后续测试。

### 步骤3：检查AI服务健康状态

⚠️ **需要设置GEMINI_API_KEY环境变量**

```bash
# 设置API密钥
export GEMINI_API_KEY=your_gemini_api_key

# 检查健康状态
curl -X GET "http://localhost:8001/api/v1/analyzer/health"
```

成功响应：
```json
{
  "gemini_available": true,
  "model_name": "gemini-2.0-flash-exp",
  "test_response": "Health check OK"
}
```

### 步骤4：测试文档分析

使用演示文档进行分析：

```bash
curl -X POST "http://localhost:8001/api/v1/analyzer/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "openapi_spec": {
      "openapi": "3.0.0",
      "info": {
        "title": "测试API",
        "version": "1.0.0"
      },
      "paths": {
        "/users": {
          "get": {
            "summary": "获取用户列表",
            "responses": {
              "200": {"description": "成功"}
            }
          }
        }
      }
    },
    "analysis_type": "quick",
    "custom_requirements": "请关注API的可测试性"
  }'
```

成功响应示例：
```json
{
  "success": true,
  "analysis_type": "quick",
  "analysis_time_seconds": 3.45,
  "endpoint_count": 1,
  "complexity_score": 0.3,
  "has_quality_issues": true,
  "needs_detailed_analysis": false,
  "overall_impression": "fair",
  "quick_issues": [
    "缺少请求参数定义",
    "响应Schema不完整"
  ],
  "gemini_model": "gemini-2.0-flash-exp",
  "analysis_timestamp": "2024-01-01T12:00:00.000Z"
}
```

## 🔍 使用Swagger UI测试

1. 打开 http://localhost:8001/docs
2. 找到 "AI Document Analyzer" 分组
3. 点击要测试的端点
4. 点击 "Try it out"
5. 填入参数
6. 点击 "Execute"

### 推荐测试顺序

1. **GET /api/v1/analyzer/demo-spec** - 获取演示文档
2. **GET /api/v1/analyzer/health** - 检查AI服务（需要API密钥）
3. **POST /api/v1/analyzer/analyze** - 使用演示文档进行分析

## 📁 文件上传测试

### 准备测试文件

创建一个简单的OpenAPI文件 `test-api.json`：

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "测试API",
    "version": "1.0.0",
    "description": "用于测试的简单API"
  },
  "paths": {
    "/ping": {
      "get": {
        "summary": "健康检查",
        "responses": {
          "200": {
            "description": "服务正常",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": {"type": "string"},
                    "timestamp": {"type": "string"}
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### 使用curl上传文件

```bash
curl -X POST "http://localhost:8001/api/v1/analyzer/analyze-file" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test-api.json" \
  -F "analysis_type=quick" \
  -F "custom_requirements=请评估API的完整性"
```

## 🚨 常见问题

### 1. 503 Service Unavailable

**原因**：未设置GEMINI_API_KEY环境变量

**解决**：
```bash
export GEMINI_API_KEY=your_actual_api_key
```

### 2. 连接超时

**原因**：Gemini API调用超时

**解决**：
- 检查网络连接
- 确认API密钥有效
- 减少文档大小

### 3. 400 Bad Request

**原因**：请求格式错误

**解决**：
- 检查JSON格式
- 确认OpenAPI文档结构正确
- 查看错误详情

## 📊 性能基准

| 文档大小 | 端点数量 | 预期响应时间 |
|---------|---------|-------------|
| 小型 | 1-5 | < 5秒 |
| 中型 | 6-20 | < 10秒 |
| 大型 | 21-50 | < 20秒 |

## 🎯 下一步

1. ✅ 基础API测试完成
2. 🔄 设置Gemini API密钥
3. 🔄 测试真实文档分析
4. 🔄 集成到前端界面
5. 🔄 添加批量分析功能

---

**记住：始终使用真实的OpenAPI文档进行测试，以获得最准确的分析结果！** 🚀
