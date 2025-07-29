#!/bin/bash
# Spec2Test 代码格式化脚本

set -e

echo "🔧 开始代码格式化..."
echo "==========================================="

# 1. 代码格式化
echo "📝 格式化代码 (Black)..."
black app/ tests/
echo "✅ 代码格式化完成"

# 2. 导入排序
echo "📦 排序导入 (isort)..."
isort app/ tests/
echo "✅ 导入排序完成"

# 3. 移除未使用的导入
echo "🧹 移除未使用的导入 (autoflake)..."
if command -v autoflake &> /dev/null; then
    autoflake --remove-all-unused-imports --recursive --in-place app/ tests/
    echo "✅ 未使用导入清理完成"
else
    echo "⚠️  autoflake 未安装，跳过未使用导入清理"
    echo "   安装命令: pip install autoflake"
fi

echo "==========================================="
echo "🎉 代码格式化完成！"
echo "💡 建议运行质量检查: ./scripts/quality-check.sh"
