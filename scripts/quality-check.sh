#!/bin/bash
# Spec2Test 代码质量检查脚本

set -e

echo "🔍 开始代码质量检查..."
echo "==========================================="

# 1. 代码格式化检查
echo "📝 检查代码格式 (Black)..."
black --check app/ tests/ || {
    echo "❌ 代码格式不符合标准，请运行: black app/ tests/"
    exit 1
}
echo "✅ 代码格式检查通过"

# 2. 导入排序检查
echo "📦 检查导入排序 (isort)..."
isort --check-only app/ tests/ || {
    echo "❌ 导入排序不正确，请运行: isort app/ tests/"
    exit 1
}
echo "✅ 导入排序检查通过"

# 3. 代码风格检查
echo "🎨 检查代码风格 (Flake8)..."
flake8 app/ tests/ --statistics || {
    echo "❌ 代码风格检查失败"
    exit 1
}
echo "✅ 代码风格检查通过"

# 4. 类型检查
echo "🔍 类型检查 (MyPy)..."
mypy app/ --show-error-codes || {
    echo "⚠️  类型检查发现问题，但继续执行"
}
echo "✅ 类型检查完成"

# 5. 安全检查
echo "🔒 安全检查 (Bandit)..."
bandit -r app/ -f json -o reports/bandit-report.json
echo "✅ 安全检查完成，报告已生成: reports/bandit-report.json"

# 6. 运行测试
echo "🧪 运行测试..."
pytest tests/unit/test_openapi_parser.py -v
echo "✅ 测试通过"

echo "==========================================="
echo "🎉 所有代码质量检查完成！"
echo "📊 查看详细报告:"
echo "   - Bandit安全报告: reports/bandit-report.json"
echo "   - 测试覆盖率: 运行 pytest --cov=app tests/"
