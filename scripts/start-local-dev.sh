#!/bin/bash
# Spec2Test 本地开发环境启动脚本（不依赖Docker镜像下载）

echo "🚀 启动 Spec2Test 本地开发环境"
echo "==========================================="

# 检查Python环境
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  建议在虚拟环境中运行"
    echo "   创建虚拟环境: python3 -m venv venv"
    echo "   激活虚拟环境: source venv/bin/activate"
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 安装依赖
echo "📦 安装Python依赖..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "❌ requirements.txt 不存在"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p reports/coverage
mkdir -p temp
mkdir -p test_output
mkdir -p logs

# 检查并启动PostgreSQL（如果可用）
echo "🗄️  检查数据库服务..."
if command -v brew >/dev/null 2>&1 && brew services list | grep -q "postgresql.*started"; then
    echo "✅ PostgreSQL 已运行"
    export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/spec2test"
elif command -v pg_ctl >/dev/null 2>&1; then
    echo "🔄 尝试启动 PostgreSQL..."
    pg_ctl start -D /usr/local/var/postgres 2>/dev/null || true
    export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/spec2test"
else
    echo "⚠️  PostgreSQL 未找到，使用SQLite作为替代"
    export DATABASE_URL="sqlite:///./spec2test.db"
fi

# 检查并启动Redis（如果可用）
echo "🔴 检查Redis服务..."
if command -v brew >/dev/null 2>&1 && brew services list | grep -q "redis.*started"; then
    echo "✅ Redis 已运行"
    export REDIS_URL="redis://localhost:6379"
elif command -v redis-server >/dev/null 2>&1; then
    echo "🔄 尝试启动 Redis..."
    redis-server --daemonize yes 2>/dev/null || true
    export REDIS_URL="redis://localhost:6379"
else
    echo "⚠️  Redis 未找到，将使用内存缓存"
    export REDIS_URL=""
fi

# 设置环境变量
export ENVIRONMENT="development"
export LOG_LEVEL="INFO"
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# 运行数据库迁移（如果有alembic）
if [ -f "alembic.ini" ]; then
    echo "🔄 运行数据库迁移..."
    alembic upgrade head 2>/dev/null || echo "⚠️  数据库迁移跳过（可能是首次运行）"
fi

# 启动应用
echo "\n🌟 启动应用服务器..."
echo "\n📋 环境信息:"
echo "   - Python: $(python3 --version)"
echo "   - 数据库: $DATABASE_URL"
echo "   - Redis: ${REDIS_URL:-'内存缓存'}"
echo "   - 工作目录: $(pwd)"
echo "\n🌐 服务将在以下地址启动:"
echo "   - 应用: http://localhost:8000"
echo "   - API文档: http://localhost:8000/docs"
echo "\n💡 使用 Ctrl+C 停止服务"
echo "==========================================="

# 启动FastAPI应用
if command -v uvicorn >/dev/null 2>&1; then
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
elif python3 -c "import uvicorn" 2>/dev/null; then
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "❌ uvicorn 未安装，请运行: pip install uvicorn"
    exit 1
fi
