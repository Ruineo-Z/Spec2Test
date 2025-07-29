#!/bin/bash
# Spec2Test 开发环境启动脚本

echo "🚀 启动 Spec2Test 开发环境"
echo "==========================================="

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

# 检查Docker Compose是否可用
if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p reports/coverage
mkdir -p temp
mkdir -p test_output

# 构建并启动服务
echo "🔨 构建并启动服务..."
if command -v docker-compose >/dev/null 2>&1; then
    docker-compose up --build -d
else
    docker compose up --build -d
fi

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "\n🔍 检查服务状态:"
if command -v docker-compose >/dev/null 2>&1; then
    docker-compose ps
else
    docker compose ps
fi

# 检查应用健康状态
echo "\n🏥 检查应用健康状态..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ 应用启动成功！"
        echo "\n🌐 服务地址:"
        echo "   - 应用: http://localhost:8000"
        echo "   - 健康检查: http://localhost:8000/health"
        echo "   - API文档: http://localhost:8000/docs"
        echo "   - PostgreSQL: localhost:5433"
        echo "   - Redis: localhost:6380"
        echo "\n💡 使用以下命令管理服务:"
        if command -v docker-compose >/dev/null 2>&1; then
            echo "   - 查看日志: docker-compose logs -f"
            echo "   - 停止服务: docker-compose down"
            echo "   - 重启服务: docker-compose restart"
        else
            echo "   - 查看日志: docker compose logs -f"
            echo "   - 停止服务: docker compose down"
            echo "   - 重启服务: docker compose restart"
        fi
        echo "\n🧪 运行测试:"
        echo "   - 本地测试: pytest tests/ -v"
        echo "   - Docker测试: ./scripts/run-tests-docker.sh"
        exit 0
    fi
    echo "等待应用启动... ($i/30)"
    sleep 2
done

echo "❌ 应用启动超时，请检查日志:"
if command -v docker-compose >/dev/null 2>&1; then
    docker-compose logs
else
    docker compose logs
fi
exit 1
