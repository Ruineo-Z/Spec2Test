#!/bin/bash
# Spec2Test 快速验证脚本
# 用于日常开发中的快速功能验证

set -e

echo "⚡ Spec2Test 快速验证"
echo "========================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. 快速代码检查
echo "📝 代码格式检查..."
if black --check app/ --quiet 2>/dev/null; then
    print_success "代码格式正确"
else
    print_warning "代码格式需要调整"
    black app/ --quiet
fi

# 2. 核心功能快速测试
echo "🤖 测试核心功能..."
if python -c "
import sys
sys.path.append('.')
try:
    from app.core.ai_generator import AITestGenerator
    from app.core.models import APIEndpoint, HttpMethod

    endpoint = APIEndpoint(
        path='/test',
        method=HttpMethod.GET,
        summary='Test endpoint'
    )

    generator = AITestGenerator()
    result = generator.generate_test_cases([endpoint], 'normal')
    print(f'✅ 生成了 {len(result.test_cases)} 个测试用例')
except Exception as e:
    print(f'❌ 核心功能测试失败: {e}')
    sys.exit(1)
" 2>/dev/null; then
    print_success "核心功能正常"
else
    print_error "核心功能测试失败"
    exit 1
fi

# 3. 快速单元测试
echo "🧪 运行关键测试..."
if pytest tests/unit/ -x --tb=no --quiet 2>/dev/null; then
    print_success "关键测试通过"
else
    print_warning "部分测试失败，运行详细测试查看问题"
fi

# 4. API健康检查
echo "🌐 检查API服务..."
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    print_success "API服务正常运行"
else
    print_warning "API服务未运行"
fi

echo "========================"
print_success "快速验证完成！"
echo "💡 运行完整验证: ./scripts/comprehensive-validation.sh"
echo "🔧 修复代码格式: black app/ tests/"
echo "🧪 运行所有测试: pytest tests/ -v"
