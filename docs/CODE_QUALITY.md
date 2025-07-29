# 代码质量指南

本文档描述了 Spec2Test 项目的代码质量标准和工具使用方法。

## 🛠️ 代码质量工具

### 1. 代码格式化工具

#### Black
- **用途**: Python 代码格式化
- **配置**: `pyproject.toml` 中的 `[tool.black]` 部分
- **使用**: `black app/ tests/`

#### isort
- **用途**: 导入语句排序
- **配置**: `pyproject.toml` 中的 `[tool.isort]` 部分
- **使用**: `isort app/ tests/`

### 2. 代码检查工具

#### Flake8
- **用途**: 代码风格检查
- **配置**: `.flake8` 文件
- **使用**: `flake8 app/ tests/`

#### MyPy
- **用途**: 静态类型检查
- **配置**: `mypy.ini` 文件
- **使用**: `mypy app/`

#### Bandit
- **用途**: 安全漏洞检查
- **配置**: `.bandit` 文件
- **使用**: `bandit -r app/`

### 3. Pre-commit 钩子

#### 安装
```bash
pre-commit install
```

#### 手动运行
```bash
pre-commit run --all-files
```

## 🚀 快速使用

### 自动格式化代码
```bash
./scripts/format-code.sh
```

### 运行所有质量检查
```bash
./scripts/quality-check.sh
```

### 运行测试
```bash
pytest tests/unit/test_openapi_parser.py -v
```

## 📋 代码质量标准

### 1. 代码格式
- 使用 Black 进行代码格式化
- 行长度限制为 88 字符
- 使用 isort 对导入语句进行排序

### 2. 代码风格
- 遵循 PEP 8 标准
- 使用 Flake8 进行检查
- 函数复杂度不超过 10

### 3. 类型注解
- 所有公共函数必须有类型注解
- 使用 MyPy 进行类型检查
- 严格模式下运行

### 4. 安全性
- 使用 Bandit 检查安全漏洞
- 不允许硬编码密码和密钥
- 避免使用不安全的函数

### 5. 测试覆盖率
- 单元测试覆盖率目标 > 80%
- 关键功能必须有测试
- 使用 pytest 进行测试

## 🔧 配置文件说明

### `.pre-commit-config.yaml`
定义了 pre-commit 钩子，包括：
- Black 代码格式化
- isort 导入排序
- Flake8 代码检查
- MyPy 类型检查
- Bandit 安全检查
- 通用检查（尾随空格、文件结尾等）

### `.flake8`
配置 Flake8 代码风格检查：
- 最大行长度：88
- 忽略与 Black 冲突的规则
- 排除特定目录

### `mypy.ini`
配置 MyPy 类型检查：
- Python 版本：3.12
- 严格模式
- 忽略第三方库的类型错误

### `.bandit`
配置 Bandit 安全检查：
- 排除测试目录
- 跳过特定测试
- 输出 JSON 格式报告

## 📊 报告和输出

### 报告位置
- Bandit 安全报告：`reports/bandit-report.json`
- 测试覆盖率报告：`htmlcov/index.html`

### 查看报告
```bash
# 查看 Bandit 报告
cat reports/bandit-report.json | jq .

# 生成测试覆盖率报告
pytest --cov=app --cov-report=html tests/
```

## 🎯 最佳实践

1. **提交前检查**：每次提交前运行 `./scripts/quality-check.sh`
2. **自动格式化**：使用 `./scripts/format-code.sh` 自动修复格式问题
3. **增量检查**：使用 pre-commit 钩子进行增量检查
4. **定期审查**：定期查看 Bandit 安全报告
5. **测试驱动**：编写代码前先写测试

## 🚨 常见问题

### Q: Pre-commit 钩子失败怎么办？
A: 运行 `./scripts/format-code.sh` 自动修复格式问题，然后重新提交。

### Q: MyPy 类型检查失败？
A: 添加必要的类型注解，或在 `mypy.ini` 中添加忽略规则。

### Q: Bandit 报告安全问题？
A: 仔细审查报告的问题，修复真正的安全漏洞，对误报使用 `# nosec` 注释。

### Q: 测试覆盖率不足？
A: 为未覆盖的代码添加单元测试，特别是关键业务逻辑。
