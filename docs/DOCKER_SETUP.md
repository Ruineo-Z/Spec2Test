# Docker 开发环境设置指南

本文档介绍如何使用Docker搭建Spec2Test的开发环境。

## 📋 前置要求

- Docker Desktop (推荐最新版本)
- Docker Compose (通常随Docker Desktop一起安装)
- 至少4GB可用内存
- 至少2GB可用磁盘空间

## 🚀 快速开始

### 1. 启动开发环境

```bash
# 一键启动所有服务
./scripts/start-dev.sh
```

这个脚本会：
- 检查Docker环境
- 创建必要的目录
- 构建并启动所有服务
- 等待服务就绪
- 显示服务地址和管理命令

### 2. 验证环境

启动成功后，你可以访问：

- **应用主页**: http://localhost:8000
- **健康检查**: http://localhost:8000/health
- **API文档**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5433 (用户名: postgres, 密码: postgres)
- **Redis**: localhost:6380

### 3. 运行测试

```bash
# 在Docker环境中运行测试
./scripts/run-tests-docker.sh

# 或者在本地运行测试（需要先启动数据库服务）
pytest tests/ -v
```

### 4. 停止环境

```bash
# 停止所有服务
./scripts/stop-dev.sh
```

## 🏗️ 服务架构

### 主要服务

| 服务名 | 容器名 | 端口 | 描述 |
|--------|--------|------|------|
| app | spec2test-app | 8000 | 主应用服务 |
| postgres | spec2test-postgres | 5433 | PostgreSQL数据库 |
| redis | spec2test-redis | 6380 | Redis缓存 |
| test-runner | spec2test-tests | - | 测试运行器（按需启动） |

### 数据卷

- `postgres_data`: PostgreSQL数据持久化
- `redis_data`: Redis数据持久化

### 网络

- `spec2test-network`: 内部服务通信网络

## 🔧 开发工作流

### 日常开发

1. **启动环境**
   ```bash
   ./scripts/start-dev.sh
   ```

2. **查看日志**
   ```bash
   docker-compose logs -f app
   # 或查看所有服务日志
   docker-compose logs -f
   ```

3. **重启服务**
   ```bash
   docker-compose restart app
   ```

4. **进入容器**
   ```bash
   docker-compose exec app bash
   ```

5. **运行命令**
   ```bash
   # 运行数据库迁移
   docker-compose exec app alembic upgrade head

   # 运行CLI命令
   docker-compose exec app python -m app.cli --help
   ```

### 测试开发

1. **运行特定测试**
   ```bash
   docker-compose run --rm test-runner pytest tests/unit/test_openapi_parser.py -v
   ```

2. **运行带覆盖率的测试**
   ```bash
   ./scripts/run-tests-docker.sh
   ```

3. **查看覆盖率报告**
   ```bash
   open reports/coverage/index.html
   ```

## 🐛 故障排除

### 常见问题

#### 1. 端口冲突

如果遇到端口冲突，可以修改`docker-compose.yml`中的端口映射：

```yaml
ports:
  - "8001:8000"  # 将8000改为8001
```

#### 2. 数据库连接失败

检查PostgreSQL服务状态：
```bash
docker-compose ps postgres
docker-compose logs postgres
```

#### 3. 应用启动失败

查看应用日志：
```bash
docker-compose logs app
```

#### 4. 内存不足

增加Docker Desktop的内存限制，或停止其他不必要的容器：
```bash
docker system prune
```

### 重置环境

如果遇到严重问题，可以完全重置环境：

```bash
# 停止并删除所有容器和数据卷
./scripts/stop-dev.sh
# 选择清理数据卷和镜像

# 重新启动
./scripts/start-dev.sh
```

## 📊 监控和日志

### 健康检查

所有服务都配置了健康检查：

```bash
# 查看服务健康状态
docker-compose ps

# 查看具体健康检查日志
docker inspect spec2test-app | grep -A 10 Health
```

### 日志管理

```bash
# 查看实时日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f app

# 查看最近的日志
docker-compose logs --tail=100 app
```

## 🔒 安全注意事项

1. **数据库密码**: 开发环境使用默认密码，生产环境请修改
2. **端口暴露**: 仅在开发时暴露数据库端口
3. **数据持久化**: 重要数据请及时备份
4. **容器权限**: 应用以非root用户运行

## 📚 相关文档

- [代码质量工具配置](CODE_QUALITY.md)
- [项目需求文档](PRD.md)
- [任务清单](TODOLIST.md)
- [Docker官方文档](https://docs.docker.com/)
- [Docker Compose文档](https://docs.docker.com/compose/)

---

**最后更新**: 2025年1月
**维护者**: Spec2Test开发团队
