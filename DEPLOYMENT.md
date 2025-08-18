# Spec2Test 部署指南

## 🚀 快速开始

### 前置要求
- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ 内存（推荐16GB）
- 20GB+ 磁盘空间

### 一键启动

```bash
# 1. 克隆项目
git clone <repository-url>
cd Spec2Test

# 2. 复制环境变量文件
cp .env.example .env.prod

# 3. 启动所有服务（生产环境）
./scripts/docker-start.sh

# 4. 初始化Ollama模型（可选，用于本地LLM）
./scripts/init-ollama.sh
```

访问应用：http://localhost

## 🔧 环境配置

### 生产环境
```bash
# 启动生产环境
./scripts/docker-start.sh -e production

# 访问地址
# - 应用: http://localhost
# - API文档: http://localhost/docs
# - 监控: http://localhost:9090 (Prometheus)
# - 仪表板: http://localhost:3000 (Grafana)
```

### 开发环境
```bash
# 启动开发环境
./scripts/docker-start.sh -e development

# 访问地址
# - 应用: http://localhost:8000
# - API文档: http://localhost:8000/docs
# - 数据库管理: http://localhost:5050 (pgAdmin)
# - Redis管理: http://localhost:8001 (RedisInsight)
# - 邮件测试: http://localhost:8025 (MailHog)
```

## 🤖 LLM配置

### 选项1: 使用Ollama（本地LLM，推荐）
```bash
# 1. 启动Ollama服务
./scripts/docker-start.sh --services ollama

# 2. 安装模型
./scripts/init-ollama.sh --model llama3.1:8b

# 3. 配置环境变量
echo "DEFAULT_LLM_PROVIDER=ollama" >> .env.prod
echo "OLLAMA_BASE_URL=http://ollama:11434" >> .env.prod
echo "OLLAMA_MODEL=llama3.1:8b" >> .env.prod
```

### 选项2: 使用Gemini API
```bash
# 配置环境变量
echo "DEFAULT_LLM_PROVIDER=gemini" >> .env.prod
echo "GEMINI_API_KEY=your_gemini_api_key_here" >> .env.prod
```

### 选项3: 使用OpenAI API
```bash
# 配置环境变量
echo "DEFAULT_LLM_PROVIDER=openai" >> .env.prod
echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env.prod
```

## 📋 常用命令

### 服务管理
```bash
# 启动所有服务
./scripts/docker-start.sh

# 启动指定服务
./scripts/docker-start.sh --services app,postgres,redis

# 前台运行（查看日志）
./scripts/docker-start.sh --foreground

# 停止所有服务
./scripts/docker-stop.sh

# 停止并删除数据（危险！）
./scripts/docker-stop.sh --remove-volumes
```

### 日志查看
```bash
# 查看所有服务日志
docker-compose -f docker/docker-compose.yml logs -f

# 查看特定服务日志
docker-compose -f docker/docker-compose.yml logs -f app

# 查看实时日志
docker-compose -f docker/docker-compose.yml logs -f --tail=100
```

### 数据库管理
```bash
# 进入数据库容器
docker-compose -f docker/docker-compose.yml exec postgres psql -U spec2test -d spec2test

# 备份数据库
docker-compose -f docker/docker-compose.yml exec postgres pg_dump -U spec2test spec2test > backup.sql

# 恢复数据库
docker-compose -f docker/docker-compose.yml exec -T postgres psql -U spec2test -d spec2test < backup.sql
```

## 🔍 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 检查端口占用
   lsof -i :80
   lsof -i :8000
   
   # 修改端口映射
   # 编辑 docker/docker-compose.yml 中的 ports 配置
   ```

2. **内存不足**
   ```bash
   # 检查内存使用
   docker stats
   
   # 减少服务或使用更小的模型
   ./scripts/init-ollama.sh --model mistral:7b
   ```

3. **磁盘空间不足**
   ```bash
   # 清理Docker资源
   docker system prune -a
   
   # 删除未使用的镜像
   docker image prune -a
   ```

4. **服务启动失败**
   ```bash
   # 查看服务状态
   docker-compose -f docker/docker-compose.yml ps
   
   # 查看错误日志
   docker-compose -f docker/docker-compose.yml logs app
   ```

### 健康检查
```bash
# 检查所有服务健康状态
python scripts/health_check.py

# 持续监控
python scripts/health_check.py --continuous --interval 30
```

## 🔒 安全配置

### 生产环境安全
1. **修改默认密码**
   ```bash
   # 编辑 .env.prod
   DATABASE_PASSWORD=your_secure_password
   REDIS_PASSWORD=your_redis_password
   ```

2. **配置SSL证书**
   ```bash
   # 将证书文件放入 docker/ssl/
   # 编辑 docker/nginx.conf 启用HTTPS配置
   ```

3. **限制网络访问**
   ```bash
   # 配置防火墙规则
   # 只开放必要端口：80, 443
   ```

## 📊 监控配置

### Prometheus + Grafana
```bash
# 启动监控服务
./scripts/docker-start.sh --services prometheus,grafana

# 访问Grafana: http://localhost:3000
# 默认账号: admin/admin123

# 导入预配置仪表板
# 在Grafana中导入 monitoring/dashboards/ 下的JSON文件
```

## 🔄 更新部署

### 更新应用
```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建并启动
./scripts/docker-start.sh --pull

# 3. 检查服务状态
docker-compose -f docker/docker-compose.yml ps
```

### 数据迁移
```bash
# 运行数据库迁移
docker-compose -f docker/docker-compose.yml exec app python scripts/init_db.py
```

## 📞 支持

如果遇到问题：
1. 查看日志文件
2. 检查环境变量配置
3. 确认服务依赖关系
4. 参考故障排除章节

---

**🎉 部署完成后，您就可以开始使用Spec2Test进行API文档测试了！**
