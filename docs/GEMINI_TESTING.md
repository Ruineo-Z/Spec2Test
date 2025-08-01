# Gemini结构化输出测试指南

本文档介绍如何测试Gemini 2.5 Flash的结构化输出功能。

## 🎯 测试目标

验证Gemini客户端能够：
1. ✅ 正确连接Gemini API
2. ✅ 生成符合Schema的结构化输出
3. ✅ 处理各种错误情况
4. ✅ 保持输出的一致性
5. ✅ 支持复杂的文档分析任务

## 🔧 环境准备

### 1. 获取Gemini API密钥

1. 访问 [Google AI Studio](https://aistudio.google.com/)
2. 创建新项目或选择现有项目
3. 生成API密钥
4. 设置环境变量：

```bash
export GEMINI_API_KEY=your_api_key_here
```

### 2. 安装依赖

```bash
# 安装Gemini SDK
pip install google-generativeai

# 或者使用项目依赖
pip install -r requirements.txt
```

## 🧪 测试方式

### 1. 单元测试（Mock测试）

运行不需要真实API的单元测试：

```bash
# 测试所有Gemini客户端功能
pytest tests/unit/test_gemini_client.py -v

# 测试特定功能
pytest tests/unit/test_gemini_client.py::TestGeminiClient::test_generate_structured_success -v
```

### 2. 集成测试（真实API）

⚠️ **注意：集成测试会调用真实的Gemini API，可能产生费用！**

```bash
# 启用集成测试
export ENABLE_GEMINI_INTEGRATION_TESTS=1
export GEMINI_API_KEY=your_api_key

# 运行集成测试
pytest tests/integration/test_gemini_real_api.py -v

# 运行特定测试
pytest tests/integration/test_gemini_real_api.py::TestGeminiRealAPI::test_real_gemini_health_check -v
```

### 3. 演示脚本

运行交互式演示：

```bash
# 设置API密钥
export GEMINI_API_KEY=your_api_key

# 运行演示
python scripts/test_gemini_structured_output.py
```

## 📊 测试用例说明

### 单元测试覆盖

| 测试类别 | 测试用例 | 说明 |
|---------|---------|------|
| **配置测试** | `test_valid_gemini_config_creation` | 验证配置创建 |
| | `test_gemini_config_defaults` | 验证默认值 |
| | `test_gemini_config_validation_errors` | 验证参数校验 |
| **客户端测试** | `test_gemini_client_initialization_success` | 验证客户端初始化 |
| | `test_gemini_client_initialization_failure_*` | 验证初始化错误处理 |
| **结构化输出** | `test_generate_structured_success` | 验证结构化生成成功 |
| | `test_generate_structured_empty_response` | 验证空响应处理 |
| | `test_generate_structured_invalid_json` | 验证无效JSON处理 |
| | `test_generate_structured_timeout` | 验证超时处理 |
| **文本生成** | `test_generate_text_success` | 验证普通文本生成 |
| **健康检查** | `test_health_check_success` | 验证健康检查成功 |
| | `test_health_check_failure` | 验证健康检查失败 |

### 集成测试覆盖

| 测试用例 | 说明 | 验证内容 |
|---------|------|----------|
| `test_real_gemini_health_check` | 真实API健康检查 | API连接性 |
| `test_real_structured_output_quick_assessment` | 真实结构化输出 | Schema符合性、字段有效性 |
| `test_real_structured_output_consistency` | 输出一致性 | 多次调用结果的一致性 |
| `test_real_error_handling` | 真实错误处理 | API错误响应处理 |

## 🔍 测试数据

### 示例OpenAPI文档

测试使用真实的OpenAPI 3.0文档，包含：

- ✅ 完整的info部分
- ✅ 多个端点（GET、POST）
- ✅ 详细的参数定义
- ✅ 完整的响应定义
- ✅ 组件Schema定义
- ✅ 请求/响应示例

### 预期输出格式

```json
{
  "endpoint_count": 3,
  "complexity_score": 0.6,
  "has_quality_issues": false,
  "needs_detailed_analysis": true,
  "estimated_analysis_time": 15,
  "reason": "文档结构完整，但部分端点缺少详细示例",
  "quick_issues": [
    "DELETE端点缺少请求示例",
    "错误响应缺少详细Schema"
  ],
  "overall_impression": "good",
  "schema_version": "1.0",
  "generated_at": "2024-01-01T12:00:00.000Z"
}
```

## ⚡ 性能基准

### 响应时间期望

| 操作类型 | 预期时间 | 说明 |
|---------|---------|------|
| 健康检查 | < 3秒 | 简单文本生成 |
| 快速评估 | < 8秒 | 小型文档（<10端点） |
| 详细分析 | < 15秒 | 中型文档（10-30端点） |
| 大型文档 | < 30秒 | 大型文档（>30端点） |

### Token消耗估算

| 文档大小 | 输入Token | 输出Token | 总成本估算 |
|---------|-----------|-----------|------------|
| 小型（<5端点） | ~2,000 | ~500 | $0.01 |
| 中型（5-20端点） | ~8,000 | ~1,000 | $0.03 |
| 大型（>20端点） | ~20,000 | ~2,000 | $0.08 |

## 🚨 注意事项

### API限制

1. **速率限制**：Gemini API有请求频率限制
2. **Token限制**：单次请求最大1M输入token，8K输出token
3. **成本控制**：每次API调用都会产生费用

### 测试最佳实践

1. **单元测试优先**：大部分测试使用Mock，避免API费用
2. **集成测试谨慎**：只在必要时运行真实API测试
3. **错误处理完整**：测试各种异常情况
4. **一致性验证**：确保多次调用结果稳定

### 故障排除

| 问题 | 可能原因 | 解决方案 |
|------|---------|----------|
| API密钥错误 | 密钥无效或过期 | 重新生成密钥 |
| 连接超时 | 网络问题或API限流 | 增加超时时间，添加重试 |
| JSON解析错误 | LLM返回格式不正确 | 检查Schema定义，调整提示词 |
| 权限错误 | API密钥权限不足 | 检查项目设置和API启用状态 |

## 📈 测试报告

运行测试后，查看详细报告：

```bash
# 生成HTML测试报告
pytest tests/unit/test_gemini_client.py --html=reports/gemini_test_report.html

# 生成覆盖率报告
pytest tests/unit/test_gemini_client.py --cov=app.core.llm --cov-report=html
```

## 🎯 下一步

1. ✅ 完成Gemini结构化输出测试
2. 🔄 实现智能分层分析器
3. 🔄 集成文档质量分析流水线
4. 🔄 添加更多Schema类型支持

---

**记住：始终遵循TDD原则，先写测试，后实现功能！** 🚀
