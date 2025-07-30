# Spec2Test 项目测试 Makefile

.PHONY: help install test test-unit test-integration test-api test-compatibility test-error test-performance test-all test-full test-coverage test-yaml clean setup dev-setup lint format check-format type-check security-check reports

# 默认目标
help:
	@echo "Spec2Test 测试命令:"
	@echo ""
	@echo "安装和设置:"
	@echo "  make install        - 安装项目依赖"
	@echo "  make setup          - 设置开发环境"
	@echo "  make dev-setup      - 设置开发环境（包括开发依赖）"
	@echo ""
	@echo "测试命令:"
	@echo "  make test           - 运行基本测试套件"
	@echo "  make test-unit      - 运行单元测试"
	@echo "  make test-integration - 运行集成测试"
	@echo "  make test-api       - 运行API测试"
	@echo "  make test-compatibility - 运行兼容性测试"
	@echo "  make test-error     - 运行错误处理测试"
	@echo "  make test-performance - 运行性能测试"
	@echo "  make test-all       - 运行所有测试（除慢速测试）"
	@echo "  make test-full      - 运行完整测试套件"
	@echo "  make test-coverage  - 生成测试覆盖率报告"
	@echo "  make test-yaml      - 使用test.yaml运行相关测试"
	@echo ""
	@echo "代码质量:"
	@echo "  make lint           - 运行代码检查"
	@echo "  make format         - 格式化代码"
	@echo "  make check-format   - 检查代码格式"
	@echo "  make type-check     - 运行类型检查"
	@echo "  make security-check - 运行安全检查"
	@echo ""
	@echo "工具:"
	@echo "  make clean          - 清理临时文件"
	@echo "  make reports        - 生成所有报告"

# 安装依赖
install:
	@echo "📦 安装项目依赖..."
	pip install -e .

# 设置开发环境
setup:
	@echo "🔧 设置开发环境..."
	pip install -e .
	mkdir -p reports
	mkdir -p logs

# 设置开发环境（包括开发依赖）
dev-setup:
	@echo "🛠️ 设置开发环境（包括开发工具）..."
	pip install -e ".[dev]"
	pip install pytest pytest-asyncio pytest-cov httpx black isort flake8 mypy bandit
	mkdir -p reports
	mkdir -p logs

# 基本测试
test:
	@echo "🧪 运行基本测试套件..."
	python run_tests.py all

# 单元测试
test-unit:
	@echo "🔬 运行单元测试..."
	python run_tests.py unit

# 集成测试
test-integration:
	@echo "🔗 运行集成测试..."
	python run_tests.py integration

# API测试
test-api:
	@echo "🌐 运行API测试..."
	python run_tests.py api

# 兼容性测试
test-compatibility:
	@echo "🔄 运行兼容性测试..."
	python run_tests.py compatibility

# 错误处理测试
test-error:
	@echo "⚠️ 运行错误处理测试..."
	python run_tests.py error

# 性能测试
test-performance:
	@echo "⚡ 运行性能测试..."
	python run_tests.py performance

# 所有测试（除慢速）
test-all:
	@echo "🎯 运行所有测试（除慢速测试）..."
	python run_tests.py all

# 完整测试套件
test-full:
	@echo "🚀 运行完整测试套件..."
	python run_tests.py full

# 覆盖率测试
test-coverage:
	@echo "📊 生成测试覆盖率报告..."
	python run_tests.py coverage
	@echo "📈 覆盖率报告已生成: reports/coverage/index.html"

# 使用test.yaml的测试
test-yaml:
	@echo "📄 使用test.yaml运行相关测试..."
	python run_tests.py yaml

# 代码检查
lint:
	@echo "🔍 运行代码检查..."
	-flake8 app tests --max-line-length=88 --extend-ignore=E203,W503
	-isort --check-only app tests
	-black --check app tests

# 格式化代码
format:
	@echo "✨ 格式化代码..."
	isort app tests
	black app tests

# 检查代码格式
check-format:
	@echo "📏 检查代码格式..."
	isort --check-only app tests
	black --check app tests

# 类型检查
type-check:
	@echo "🔎 运行类型检查..."
	-mypy app --ignore-missing-imports

# 安全检查
security-check:
	@echo "🔒 运行安全检查..."
	-bandit -r app -f json -o reports/security.json
	-bandit -r app

# 清理临时文件
clean:
	@echo "🧹 清理临时文件..."
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf reports/coverage
	rm -rf .mypy_cache
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# 生成所有报告
reports: test-coverage security-check
	@echo "📋 所有报告已生成在 reports/ 目录"

# 快速开发循环
dev: format lint type-check test
	@echo "🎉 开发检查完成！"

# CI/CD 流水线
ci: setup lint type-check security-check test-coverage
	@echo "🚀 CI/CD 流水线完成！"

# 发布前检查
pre-release: clean dev-setup ci test-full
	@echo "✅ 发布前检查完成！"
