# 🧪 Spec2Test 完整测试指南

本指南提供了完整的测试流程，帮助你验证项目功能并发现潜在问题。

## 🎯 测试目标

基于你的 `test.yaml` 接口文档，我们创建了全面的测试套件来验证：

1. **API文档上传功能** - 验证OpenAPI文档能否正确上传和解析
2. **文档质量分析** - 验证系统能否正确分析文档质量
3. **API兼容性** - 验证实际API实现与文档规范的一致性
4. **错误处理** - 验证各种异常情况的处理
5. **系统性能** - 验证系统在负载下的表现

## 🚀 快速开始

### 1. 环境准备

```bash
# 确保你在项目根目录
cd /Users/augenstern/development/personal/Spec2Test

# 安装依赖
make install
# 或者
pip install -e .
```

### 2. 一键测试

```bash
# 运行针对test.yaml的完整测试
make test-yaml

# 或者使用Python脚本
python run_tests.py yaml
```

### 3. 生成测试报告

```bash
# 运行完整测试并生成报告
python test_summary.py
```

## 📋 详细测试流程

### 阶段1: 基础验证

```bash
# 1. 检查项目结构
ls -la app/ tests/

# 2. 验证test.yaml文件
cat test.yaml | head -20

# 3. 运行健康检查
curl http://localhost:8000/health || echo "服务未启动"
```

### 阶段2: 单元测试

```bash
# 运行单元测试
make test-unit

# 详细输出
pytest tests/unit/ -v
```

### 阶段3: 集成测试

```bash
# 运行集成测试
make test-integration

# 包含文档上传和解析测试
pytest tests/integration/test_document_upload.py -v
```

### 阶段4: API兼容性测试

```bash
# 验证API与test.yaml的兼容性
make test-compatibility

# 详细兼容性检查
pytest tests/compatibility/test_api_compatibility.py -v
```

### 阶段5: 错误处理测试

```bash
# 测试各种错误场景
make test-error

# 详细错误处理测试
pytest tests/integration/test_error_scenarios.py -v
```

### 阶段6: 性能测试

```bash
# 运行性能测试
make test-performance

# 包含负载测试（可能较慢）
pytest tests/performance/test_load_testing.py -v
```

## 🔍 问题诊断流程

### 1. 服务启动检查

```bash
# 检查服务是否运行
curl -f http://localhost:8000/health

# 如果失败，启动服务
cd app
python -m uvicorn main:app --reload --port 8000
```

### 2. 数据库连接检查

```bash
# 检查数据库配置
cat app/config/settings.py | grep -i database

# 测试数据库连接
python -c "from app.database import engine; print('数据库连接正常')"
```

### 3. 依赖检查

```bash
# 检查Python依赖
pip list | grep -E "fastapi|uvicorn|pytest|httpx"

# 安装缺失依赖
pip install -r requirements.txt  # 如果有的话
```

### 4. 测试文件检查

```bash
# 验证test.yaml格式
python -c "import yaml; yaml.safe_load(open('test.yaml'))"

# 检查测试文件结构
find tests/ -name "*.py" | head -10
```

## 📊 测试结果解读

### 成功指标

- ✅ **所有基础测试通过** - API基本功能正常
- ✅ **文档上传成功** - 可以上传和解析test.yaml
- ✅ **质量分析正常** - 系统能分析文档质量
- ✅ **兼容性测试通过** - API实现与文档一致
- ✅ **错误处理正确** - 异常情况处理得当

### 常见问题及解决方案

#### 问题1: 服务连接失败
```
ConnectionError: Cannot connect to localhost:8000
```

**解决方案:**
```bash
# 启动服务
cd app
python -m uvicorn main:app --reload --port 8000 &

# 等待服务启动
sleep 5

# 重新运行测试
make test-yaml
```

#### 问题2: 数据库错误
```
OperationalError: no such table
```

**解决方案:**
```bash
# 初始化数据库
python -c "from app.database import create_tables; create_tables()"

# 或检查数据库配置
cat app/config/settings.py
```

#### 问题3: 文件上传失败
```
HTTP 422: Unprocessable Entity
```

**解决方案:**
```bash
# 检查test.yaml格式
yaml-lint test.yaml

# 或使用Python验证
python -c "import yaml; print(yaml.safe_load(open('test.yaml')))"
```

#### 问题4: 测试超时
```
TimeoutError: Test execution timeout
```

**解决方案:**
```bash
# 跳过慢速测试
pytest -m "not slow"

# 或增加超时时间
pytest --timeout=300
```

## 🛠️ 高级测试选项

### 自定义测试运行

```bash
# 运行特定测试文件
pytest tests/integration/test_document_upload.py::test_upload_test_yaml -v

# 运行特定标记的测试
pytest -m "api and not slow" -v

# 并行运行测试
pytest -n auto

# 生成详细报告
pytest --html=reports/pytest_report.html --self-contained-html
```

### 调试模式

```bash
# 详细输出模式
pytest -v -s --tb=long

# 失败时进入调试器
pytest --pdb

# 只运行失败的测试
pytest --lf
```

### 覆盖率分析

```bash
# 生成覆盖率报告
make test-coverage

# 查看HTML报告
open reports/coverage/index.html

# 查看覆盖率详情
pytest --cov=app --cov-report=term-missing
```

## 📈 持续改进

### 1. 定期测试

```bash
# 设置定时任务（可选）
echo "0 */6 * * * cd /path/to/project && make test-yaml" | crontab -
```

### 2. 测试自动化

```bash
# 创建测试脚本
echo '#!/bin/bash
cd /Users/augenstern/development/personal/Spec2Test
make test-yaml
python test_summary.py' > run_daily_tests.sh
chmod +x run_daily_tests.sh
```

### 3. 监控和报告

```bash
# 生成趋势报告
python test_summary.py > reports/daily_$(date +%Y%m%d).log
```

## 🎯 测试最佳实践

### 1. 测试前准备
- 确保服务正在运行
- 检查test.yaml文件完整性
- 清理之前的测试数据

### 2. 测试执行
- 按顺序运行测试套件
- 记录失败的测试用例
- 保存测试日志和报告

### 3. 结果分析
- 查看测试覆盖率
- 分析失败原因
- 制定改进计划

### 4. 问题修复
- 优先修复高优先级问题
- 验证修复效果
- 更新相关文档

## 📞 获取帮助

### 查看帮助信息

```bash
# Makefile帮助
make help

# pytest帮助
pytest --help

# 测试脚本帮助
python run_tests.py --help
```

### 常用命令速查

```bash
# 快速测试
make test-yaml                    # 测试test.yaml相关功能
make test                         # 运行基本测试套件
make test-all                     # 运行所有测试（除慢速）

# 问题诊断
python test_summary.py            # 生成完整测试报告
make test-coverage                # 生成覆盖率报告
make lint                         # 代码质量检查

# 开发辅助
make dev                          # 开发环境检查
make clean                        # 清理临时文件
make setup                        # 环境设置
```

---

## 🎉 开始测试

现在你可以开始测试了！建议按以下顺序执行：

1. **环境检查**: `make setup`
2. **快速测试**: `make test-yaml`
3. **完整报告**: `python test_summary.py`
4. **问题修复**: 根据报告修复发现的问题
5. **重新验证**: 再次运行测试确认修复效果

**祝你测试顺利！** 🚀
