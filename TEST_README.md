# Spec2Test 测试指南

本文档描述了如何运行测试以及项目的测试策略。

## 🎯 测试目标

基于 `test.yaml` 接口文档，本项目实现了全面的测试策略：

1. **文档上传测试** - 验证OpenAPI文档上传功能
2. **文档解析测试** - 验证文档解析和质量分析
3. **API兼容性测试** - 验证实际API与规范的一致性
4. **错误处理测试** - 验证各种错误场景的处理
5. **性能测试** - 验证系统性能和负载能力

## 📁 测试结构

```
tests/
├── conftest.py                    # pytest配置和fixtures
├── fixtures/                      # 测试数据
│   ├── poor_quality_openapi.yaml
│   └── sample_openapi.yaml
├── unit/                          # 单元测试
│   └── test_openapi_parser.py
├── integration/                   # 集成测试
│   ├── test_document_upload.py    # 文档上传和解析测试
│   └── test_error_scenarios.py    # 错误场景测试
├── compatibility/                 # 兼容性测试
│   └── test_api_compatibility.py  # API兼容性测试
├── performance/                   # 性能测试
│   └── test_load_testing.py       # 负载和性能测试
└── utils.py                       # 测试工具函数
```

## 🚀 快速开始

### 1. 环境设置

```bash
# 安装依赖
make install

# 或设置开发环境
make dev-setup
```

### 2. 运行测试

```bash
# 查看所有可用命令
make help

# 运行基本测试套件
make test

# 使用test.yaml运行相关测试
make test-yaml
```

## 📋 测试命令详解

### 基础测试命令

```bash
# 单元测试
make test-unit
python run_tests.py unit

# 集成测试
make test-integration
python run_tests.py integration

# API测试
make test-api
python run_tests.py api
```

### 专项测试命令

```bash
# 兼容性测试
make test-compatibility
python run_tests.py compatibility

# 错误处理测试
make test-error
python run_tests.py error

# 性能测试
make test-performance
python run_tests.py performance
```

### 综合测试命令

```bash
# 所有测试（除慢速测试）
make test-all
python run_tests.py all

# 完整测试套件（包括慢速测试）
make test-full
python run_tests.py full

# 生成覆盖率报告
make test-coverage
python run_tests.py coverage
```

### 特定文档测试

```bash
# 使用test.yaml文件运行相关测试
make test-yaml
python run_tests.py yaml
```

## 🧪 测试类型说明

### 1. 文档上传测试 (`test_document_upload.py`)

- ✅ 健康检查和基本API信息
- ✅ 成功上传test.yaml文档
- ✅ 文档解析和质量分析
- ✅ 获取文档列表
- ✅ 删除文档
- ✅ 验证test.yaml内容结构
- ✅ 验证API端点详情

### 2. 错误处理测试 (`test_error_scenarios.py`)

- ❌ 无效文件类型处理
- ❌ 空文件和损坏文件处理
- ❌ 格式错误的YAML处理
- ❌ 不存在的文档ID处理
- ❌ 并发操作处理
- ❌ 边界条件测试

### 3. API兼容性测试 (`test_api_compatibility.py`)

- 🔄 OpenAPI版本兼容性
- 🔄 API信息一致性
- 🔄 端点存在性验证
- 🔄 请求/响应模型验证
- 🔄 认证方案验证
- 🔄 错误响应一致性

### 4. 性能测试 (`test_load_testing.py`)

- ⚡ 响应时间基线测试
- ⚡ 文件上传性能测试
- ⚡ 并发请求测试
- ⚡ 内存和资源使用测试
- ⚡ 负载压力测试（标记为slow）

## 📊 测试报告

### 覆盖率报告

```bash
make test-coverage
# 报告位置: reports/coverage/index.html
```

### JUnit XML报告

```bash
# 自动生成在: reports/junit.xml
```

### 性能报告

```bash
make test-performance
# 包含响应时间统计
```

## 🏷️ 测试标记

使用pytest标记来分类和过滤测试：

```bash
# 运行特定标记的测试
pytest -m "unit"                    # 单元测试
pytest -m "integration"             # 集成测试
pytest -m "api"                     # API测试
pytest -m "compatibility"           # 兼容性测试
pytest -m "error_handling"          # 错误处理测试
pytest -m "performance"             # 性能测试
pytest -m "slow"                    # 慢速测试
pytest -m "not slow"                # 排除慢速测试
```

## 🔧 配置文件

### pytest.ini

包含pytest的全局配置，包括：
- 测试发现规则
- 输出格式配置
- 覆盖率设置
- 标记定义
- 警告过滤

### conftest.py

包含测试fixtures和配置：
- 数据库测试配置
- HTTP客户端配置
- 测试数据fixtures
- 辅助函数

## 🐛 调试测试

### 详细输出

```bash
pytest -v -s                        # 详细输出，不捕获print
pytest --tb=long                    # 详细错误追踪
pytest --pdb                        # 失败时进入调试器
```

### 运行特定测试

```bash
pytest tests/integration/test_document_upload.py::test_upload_test_yaml
pytest -k "test_upload"             # 运行名称包含"test_upload"的测试
```

### 失败重试

```bash
pytest --lf                         # 只运行上次失败的测试
pytest --ff                         # 先运行上次失败的测试
```

## 📈 持续集成

### CI/CD流水线

```bash
make ci                             # 完整CI检查
```

包含：
1. 环境设置
2. 代码检查（lint）
3. 类型检查
4. 安全检查
5. 测试覆盖率

### 发布前检查

```bash
make pre-release                    # 发布前完整检查
```

## 🎯 测试最佳实践

### 1. 测试隔离
- 每个测试都是独立的
- 使用fixtures提供测试数据
- 测试后自动清理

### 2. 测试数据
- 使用真实的test.yaml文件
- 提供多种测试场景的数据
- 包含边界条件和错误情况

### 3. 断言策略
- 明确的断言消息
- 验证关键字段和结构
- 检查错误响应格式

### 4. 性能考虑
- 标记慢速测试
- 合理的超时设置
- 并发测试的资源管理

## 🚨 常见问题

### 1. 测试失败

```bash
# 检查服务是否运行
curl http://localhost:8000/health

# 检查数据库连接
# 查看日志文件
```

### 2. 覆盖率不足

```bash
# 查看详细覆盖率报告
make test-coverage
open reports/coverage/index.html
```

### 3. 性能测试超时

```bash
# 跳过慢速测试
pytest -m "not slow"

# 调整超时设置
# 在conftest.py中修改timeout配置
```

## 📝 贡献指南

### 添加新测试

1. 选择合适的测试目录
2. 使用适当的测试标记
3. 遵循命名约定
4. 添加必要的文档

### 测试命名约定

- `test_*.py` - 测试文件
- `test_*()` - 测试函数
- `Test*` - 测试类
- 描述性的测试名称

### 提交前检查

```bash
make dev                            # 开发检查
make ci                             # CI检查
```

---

🎉 **开始测试吧！** 使用 `make test-yaml` 来验证你的 `test.yaml` 接口文档。
