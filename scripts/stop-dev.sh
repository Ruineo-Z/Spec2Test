#!/bin/bash
# Spec2Test 开发环境停止脚本

echo "🛑 停止 Spec2Test 开发环境"
echo "==========================================="

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker 未运行"
    exit 1
fi

# 检查Docker Compose命令
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# 显示当前运行的服务
echo "📋 当前运行的服务:"
$COMPOSE_CMD ps

# 停止所有服务
echo "\n🔄 停止所有服务..."
$COMPOSE_CMD down

# 可选：清理数据卷（需要用户确认）
read -p "\n🗑️  是否清理数据卷？这将删除所有数据库数据 (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 清理数据卷..."
    $COMPOSE_CMD down -v
    docker volume prune -f
    echo "✅ 数据卷已清理"
fi

# 可选：清理镜像（需要用户确认）
read -p "\n🗑️  是否清理构建的镜像？ (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 清理镜像..."
    docker image prune -f
    # 删除项目相关镜像
    docker images | grep spec2test | awk '{print $3}' | xargs -r docker rmi
    echo "✅ 镜像已清理"
fi

echo "\n✅ 开发环境已停止"
echo "\n💡 重新启动开发环境:"
echo "   ./scripts/start-dev.sh"
