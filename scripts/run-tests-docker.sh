#!/bin/bash
# Spec2Test Docker测试运行脚本

echo "🧪 在Docker环境中运行测试"
echo "==========================================="

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

# 检查服务是否运行
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

if ! $COMPOSE_CMD ps | grep -q "spec2test-postgres.*Up"; then
    echo "⚠️  数据库服务未运行，启动测试环境..."
    $COMPOSE_CMD up -d postgres redis
    echo "⏳ 等待数据库启动..."
    sleep 10
fi

# 创建测试报告目录
echo "📁 创建测试报告目录..."
mkdir -p reports/coverage
mkdir -p reports/junit

# 运行测试
echo "🚀 运行测试套件..."
$COMPOSE_CMD run --rm test-runner

# 检查测试结果
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "\n✅ 所有测试通过！"
    echo "\n📊 测试报告:"
    echo "   - 覆盖率报告: reports/coverage/index.html"
    echo "   - JUnit报告: reports/junit.xml"
else
    echo "\n❌ 测试失败，退出码: $TEST_EXIT_CODE"
    echo "\n🔍 查看详细日志:"
    echo "   $COMPOSE_CMD logs test-runner"
fi

# 清理测试容器
echo "\n🧹 清理测试容器..."
$COMPOSE_CMD rm -f test-runner

exit $TEST_EXIT_CODE
