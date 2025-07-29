#!/bin/bash
# Spec2Test 快速验证脚本

echo "🔍 快速验证代码质量工具配置"
echo "==========================================="

# 1. 验证核心工具
echo "📦 1. 核心工具验证"
echo "black --version: $(black --version 2>/dev/null || echo '❌ 未安装')"
echo "isort --version: $(isort --version 2>/dev/null || echo '❌ 未安装')"
echo "flake8 --version: $(flake8 --version 2>/dev/null || echo '❌ 未安装')"
echo "mypy --version: $(mypy --version 2>/dev/null || echo '❌ 未安装')"
echo "bandit --version: $(bandit --version 2>/dev/null || echo '❌ 未安装')"
echo "pytest --version: $(pytest --version 2>/dev/null || echo '❌ 未安装')"

# 2. 验证配置文件
echo "\n📄 2. 配置文件验证"
for file in ".flake8" "mypy.ini" ".bandit" ".pre-commit-config.yaml" "pyproject.toml"; do
    if [ -f "$file" ]; then
        echo "✅ $file 存在"
    else
        echo "❌ $file 不存在"
    fi
done

# 3. 验证脚本
echo "\n🔧 3. 脚本验证"
for script in "scripts/quality-check.sh" "scripts/format-code.sh"; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        echo "✅ $script 存在且可执行"
    else
        echo "❌ $script 不存在或不可执行"
    fi
done

# 4. 运行核心测试
echo "\n🧪 4. 核心功能测试"

# 测试代码格式检查
echo "测试 Black 格式检查..."
if black --check app/ tests/ >/dev/null 2>&1; then
    echo "✅ Black 格式检查通过"
else
    echo "⚠️  Black 格式需要调整"
fi

# 测试导入排序
echo "测试 isort 导入检查..."
if isort --check-only app/ tests/ >/dev/null 2>&1; then
    echo "✅ isort 导入检查通过"
else
    echo "⚠️  isort 导入需要调整"
fi

# 测试单元测试
echo "测试 pytest 单元测试..."
if pytest tests/unit/test_openapi_parser.py -v >/dev/null 2>&1; then
    echo "✅ pytest 单元测试通过"
else
    echo "❌ pytest 单元测试失败"
fi

# 5. 验证报告生成
echo "\n📊 5. 报告生成测试"
bandit -r app/ -f json -o reports/bandit-report.json >/dev/null 2>&1
if [ -f "reports/bandit-report.json" ]; then
    echo "✅ Bandit 安全报告生成成功"
else
    echo "❌ Bandit 安全报告生成失败"
fi

echo "\n==========================================="
echo "🎯 验证完成！"
echo "\n💡 使用以下命令进行详细检查："
echo "   ./scripts/quality-check.sh    # 完整质量检查"
echo "   ./scripts/format-code.sh     # 自动格式化代码"
echo "   pytest tests/ -v             # 运行所有测试"
echo "==========================================="
