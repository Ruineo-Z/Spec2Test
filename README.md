# Spec2Test
通过AI实现自动化测试流水线

## 项目结构说明

### 核心必需文件/目录 ⭐

这些是项目运行的核心组件，不可删除：

```
app/                          # 主应用目录
├── __init__.py              # Python包标识
├── main.py                  # FastAPI应用入口
├── cli.py                   # 命令行接口
├── config/                  # 配置管理
│   ├── __init__.py
│   └── settings.py          # 应用设置和环境变量
├── core/                    # 核心业务逻辑
│   ├── __init__.py
│   ├── models.py            # Pydantic数据模型定义
│   ├── db_models.py         # SQLAlchemy数据库模型
│   ├── database.py          # 数据库连接和会话管理
│   ├── config.py            # 核心配置
│   ├── ai_generator.py      # AI测试用例生成核心逻辑
│   ├── prompts.py           # AI提示词模板
│   ├── quality_control.py   # 质量控制模块
│   └── parser/              # OpenAPI文档解析器
├── api/                     # API路由层
│   ├── __init__.py
│   └── v1/                  # API版本1路由
└── utils/                   # 工具函数
    ├── __init__.py
    ├── exceptions.py        # 自定义异常处理
    ├── helpers.py           # 通用辅助函数
    └── logger.py            # 日志配置和管理

requirements.txt             # Python依赖包列表
pyproject.toml              # 项目配置和依赖管理
main.py                     # 项目启动入口文件
```

### 开发工具文件 🔧

这些文件用于开发环境配置和代码质量控制，可根据需要保留：

#### 代码质量检查配置
```
.pre-commit-config.yaml     # Git提交前自动检查配置
.flake8                     # Python代码风格检查配置（PEP8）
.bandit                     # Python安全漏洞扫描配置
mypy.ini                    # Python静态类型检查配置
pytest.ini                  # 单元测试框架配置
```

#### Docker容器化配置
```
.dockerignore              # Docker构建时忽略文件
Dockerfile                 # Docker镜像构建配置
docker-compose.yml         # Docker多容器编排配置
```

#### 项目配置文件
```
pyproject.toml             # 现代Python项目配置（依赖、构建、工具配置）
requirements.txt           # Python依赖包列表
```

### 数据库相关 🗄️

数据库迁移和管理文件：

```
alembic.ini                # 数据库迁移配置
alembic/                   # 数据库迁移脚本
spec2test.db              # SQLite数据库文件（生产环境可删除）
```

### 测试相关 🧪

测试代码和测试数据：

```
tests/                     # 测试代码
├── __init__.py
├── conftest.py           # 测试配置
├── fixtures/             # 测试数据
└── unit/                 # 单元测试
```

### 脚本工具 📜

开发和部署辅助脚本：

#### 开发环境管理脚本
```
scripts/
├── start-dev.sh              # 启动开发环境服务器
├── start-local-dev.sh        # 启动本地开发环境
├── stop-dev.sh               # 停止开发环境服务器
└── init-db.sql               # 数据库初始化SQL脚本
```

#### 代码质量和验证脚本
```
├── quality-check.sh          # 运行所有代码质量检查
├── format-code.sh            # 自动格式化代码
├── api-validation.py         # API接口验证脚本
├── quick-validation.sh       # 快速验证脚本
├── quick-verify.sh           # 快速验证检查
├── comprehensive-validation.sh # 全面验证检查
└── verify-setup.sh           # 验证环境设置
```

#### 测试相关脚本
```
└── run-tests-docker.sh       # 在Docker环境中运行测试
```

### 文档和报告 📚

项目文档和分析报告：

#### 项目文档
```
docs/
├── PRD.md                    # 产品需求文档
├── CODE_QUALITY.md           # 代码质量规范
├── DOCKER_SETUP.md           # Docker环境搭建指南
├── PHASE1_COMPLETION_SUMMARY.md # 第一阶段完成总结
└── TODOLIST.md               # 待办事项清单

project_structure.md          # 项目结构详细说明
README.md                     # 项目说明文档（本文件）
```

#### 代码质量报告
```
reports/
├── bandit-report.json        # 安全扫描报告
└── coverage/                 # 测试覆盖率报告
```

### 可删除的文件/目录 🗑️

这些文件/目录可以安全删除而不影响核心功能：

```
.mypy_cache/              # MyPy缓存（自动生成）
.venv/                    # 虚拟环境（可重新创建）
reports/                  # 代码质量报告
temp/                     # 临时文件
test_output/              # 测试输出
workspace/                # 工作空间文件
uv.lock                   # UV包管理器锁文件（如果不用UV）
.promptx/                 # PromptX配置（如果不用该工具）
```

### 环境和配置文件 ⚙️

```
.gitignore                # Git忽略规则（建议保留）
.dockerignore             # Docker忽略规则
```

## 最小运行配置

如果只想运行核心功能，最少需要保留：

1. `app/` 目录及其所有内容
2. `requirements.txt`
3. `main.py`
4. `pyproject.toml`（如果使用现代Python包管理）

## 建议保留

为了更好的开发体验，建议保留：

- 所有核心必需文件
- 测试相关文件（`tests/`）
- 基本的开发工具配置（`.gitignore`, `.flake8`等）
- 数据库迁移文件（`alembic/`）
- 启动脚本（`scripts/start-dev.sh`等）
