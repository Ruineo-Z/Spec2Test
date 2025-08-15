# Spec2Test 开发 TodoList

**版本**: v1.0  
**创建日期**: 2025-08-14  
**负责人**: Sean (deepractice.ai)  
**开发原则**: 按依赖顺序，从底层到上层，确保每步完成后再进行下一步

---

## 开发顺序说明

```
项目基础设置 → 数据模型 → 共享组件 → 核心业务模块 → API接口 → 异步任务 → 测试 → 部署
```

**重要原则**:
- ✅ 每个阶段完成后，必须通过基础测试才能进入下一阶段
- ✅ 严格按照依赖关系开发，避免循环依赖
- ✅ 每个模块开发完成后立即编写单元测试

---

## 阶段1: 项目基础设置 (预计1天)

### 1.1 项目初始化
- [x] **1.1.1** 创建项目目录结构 ✅ **已完成**
  ```bash
  mkdir -p spec2test-backend/{app,tests,docker,scripts,docs}
  mkdir -p app/{api,core,models,schemas,tasks}
  mkdir -p app/core/{document_analyzer,test_generator,test_executor,report_analyzer,shared}
  ```

- [x] **1.1.2** 创建基础配置文件 ✅ **已完成**
  - [x] `pyproject.toml` - 项目配置和依赖管理
  - [x] `requirements.txt` - Python依赖列表
  - [x] `.env.example` - 环境变量模板
  - [x] `.gitignore` - Git忽略规则
  - [x] `README.md` - 项目说明

### 1.2 核心配置模块
- [x] **1.2.1** `app/config.py` - 配置管理类 ✅ **已完成**
  - [x] 数据库配置 (PostgreSQL)
  - [x] LLM配置 (Gemini, Ollama)
  - [x] Redis配置 (Celery)
  - [x] 文件存储配置
  - [x] 日志配置

- [x] **1.2.2** `app/dependencies.py` - 依赖注入 ✅ **已完成**
  - [x] 数据库会话依赖
  - [x] 配置依赖
  - [ ] 认证依赖（如需要）

### 1.3 基础工具模块
- [ ] **1.3.1** `app/core/shared/utils/logger.py` - 日志工具(loguru)
- [ ] **1.3.2** `app/core/shared/utils/exceptions.py` - 自定义异常
- [ ] **1.3.3** `app/core/shared/utils/helpers.py` - 通用工具函数

**完成标准**: 项目能够启动，配置能够正确加载，日志正常输出

---

## 阶段2: 数据模型层 (预计1.5天)

### 2.1 数据库基础
- [x] **2.1.1** `app/models/base.py` - 基础模型类 ✅ **已完成**
  - [x] 时间戳字段 (created_at, updated_at)
  - [x] 主键定义
  - [x] 软删除支持

- [x] **2.1.2** 数据库连接设置 ✅ **已完成**
  - [x] SQLAlchemy引擎配置
  - [x] 会话管理
  - [x] 连接池配置

### 2.2 核心数据模型
- [x] **2.2.1** `app/models/document.py` - 文档模型 ✅ **已完成**
  ```python
  class Document:
      id, filename, content, document_type,
      file_size, upload_time, status
  ```

- [x] **2.2.2** `app/models/test_case.py` - 测试用例模型 ✅ **已完成**
  ```python
  class TestCase:
      id, document_id, endpoint_path, method,
      test_data, expected_result, test_type
  ```

- [x] **2.2.3** `app/models/test_result.py` - 测试结果模型 ✅ **已完成**
  ```python
  class TestResult:
      id, test_case_id, status, response_data,
      execution_time, error_message
  ```

- [x] **2.2.4** `app/models/report.py` - 报告模型 ✅ **已完成**
  ```python
  class Report:
      id, document_id, summary_data, detailed_data,
      generation_time, report_type
  ```

### 2.3 数据验证模式 (Pydantic)
- [x] **2.3.1** `app/schemas/document.py` - 文档相关Schema ✅ **已完成**
- [x] **2.3.2** `app/schemas/test_case.py` - 测试用例Schema ✅ **已完成**
- [x] **2.3.3** `app/schemas/test_result.py` - 测试结果Schema ✅ **已完成**
- [x] **2.3.4** `app/schemas/report.py` - 报告Schema ✅ **已完成**

### 2.4 数据库迁移
- [x] **2.4.1** 配置Alembic ✅ **已完成**
- [x] **2.4.2** 创建初始迁移文件 ✅ **已完成**
- [x] **2.4.3** 测试迁移脚本 ✅ **已完成**

**完成标准**: 数据库表创建成功，模型关系正确，Schema验证通过

---

## 阶段3: 共享组件层 (预计2天)

### 3.1 共享组件开发
- [x] **3.1.1** `app/core/shared/llm/base.py` - LLM基础接口 ✅ **已完成**
  ```python
  class BaseLLMClient:
      def generate_text(prompt, schema) -> dict
      def analyze_document(content) -> dict
  ```

- [x] **3.1.2** `app/core/shared/llm/gemini.py` - Gemini实现 ✅ **已完成**
- [x] **3.1.3** `app/core/shared/llm/ollama.py` - Ollama实现 ✅ **已完成**
- [x] **3.1.4** `app/core/shared/llm/factory.py` - LLM工厂类 ✅ **已完成**
- [x] **3.1.5** `app/core/shared/http/client.py` - HTTP客户端 ✅ **已完成**
- [x] **3.1.6** `app/core/shared/http/auth.py` - HTTP认证处理器 ✅ **已完成**
- [x] **3.1.7** `app/core/shared/http/performance.py` - HTTP性能监控 ✅ **已完成**

### 3.2 存储抽象层 ✅ **已完成**
- [x] **3.2.1** `app/core/shared/storage/base.py` - 存储抽象基类 ✅ **已完成**
- [x] **3.2.2** `app/core/shared/storage/file_storage.py` - 文件存储实现 ✅ **已完成**
- [x] **3.2.3** `app/core/shared/storage/db_storage.py` - 数据库存储实现 ✅ **已完成**
- [x] **3.2.4** `app/core/shared/storage/cache_storage.py` - 缓存存储实现 ✅ **已完成**
- [x] **3.2.5** `app/core/shared/storage/factory.py` - 存储工厂和管理器 ✅ **已完成**
- [x] **3.2.6** 功能验证测试：7/7测试通过 ✅ **已完成**

### 3.3 HTTP客户端 ✅ **已完成**
- [x] **3.3.1** `app/core/test_executor/http_client.py` - 测试执行器HTTP客户端 ✅ **已完成**
  - [x] 支持各种HTTP方法 ✅ **已完成**
  - [x] 认证处理 ✅ **已完成**
  - [x] 超时和重试机制 ✅ **已完成**
  - [x] 测试专用断言系统 ✅ **已完成**
  - [x] 测试套件执行 ✅ **已完成**
  - [x] 功能验证测试：9/9测试通过 ✅ **已完成**

**完成标准**: LLM客户端能够正常调用，存储组件功能正常，HTTP客户端测试通过

---

## 阶段4: 核心业务模块 (预计4天)

### 4.1 文档分析模块 ✅ **已完成**
- [x] **4.1.1** `app/core/document_analyzer/models.py` - 数据模型 ✅ **已完成**
- [x] **4.1.2** `app/core/document_analyzer/parser.py` - 文档解析器 ✅ **已完成**
  - [x] OpenAPI JSON/YAML解析 ✅ **已完成**
  - [x] Markdown解析 ✅ **已完成**
  - [x] 文档类型自动检测 ✅ **已完成**

- [x] **4.1.3** `app/core/document_analyzer/validator.py` - 质量检查器 ✅ **已完成**
  - [x] 完整性检查 ✅ **已完成**
  - [x] 一致性验证 ✅ **已完成**
  - [x] 改进建议生成 ✅ **已完成**

- [x] **4.1.4** `app/core/document_analyzer/chunker.py` - 文档分块器 ✅ **已完成**
  - [x] 按接口分组 ✅ **已完成**
  - [x] Token数量估算 ✅ **已完成**
  - [x] 智能分块优化 ✅ **已完成**

- [x] **4.1.5** `app/core/document_analyzer/analyzer.py` - 主分析器 ✅ **已完成**
- [x] **4.1.6** 功能验证测试：8/8测试通过 ✅ **已完成**

### 4.2 测试生成模块 (1天)
- [ ] **4.2.1** `app/core/test_generator/models.py` - 数据模型
- [ ] **4.2.2** `app/core/test_generator/prompt_builder.py` - 提示词构建
- [ ] **4.2.3** `app/core/test_generator/case_generator.py` - 用例生成器
  - [ ] 正常流程用例
  - [ ] 边界条件用例
  - [ ] 异常情况用例

### 4.3 测试执行模块 (1天)
- [ ] **4.3.1** `app/core/test_executor/models.py` - 数据模型
- [ ] **4.3.2** `app/core/test_executor/runner.py` - 测试运行器
  - [ ] 单个测试执行
  - [ ] 批量测试执行
  - [ ] 并发控制

- [ ] **4.3.3** `app/core/test_executor/scheduler.py` - 任务调度器

### 4.4 结果分析模块 (1天)
- [ ] **4.4.1** `app/core/report_analyzer/models.py` - 数据模型
- [ ] **4.4.2** `app/core/report_analyzer/analyzer.py` - 结果分析器
  - [ ] 失败原因分析
  - [ ] 模式识别
  - [ ] 修复建议

- [ ] **4.4.3** `app/core/report_analyzer/reporter.py` - 报告生成器
- [ ] **4.4.4** `app/core/report_analyzer/visualizer.py` - 可视化组件

**完成标准**: 每个模块的核心功能完成，单元测试通过，模块间接口调用正常

---

## 阶段5: API接口层 (预计2天)

### 5.1 API基础设置
- [ ] **5.1.1** `app/main.py` - FastAPI应用入口
- [ ] **5.1.2** `app/api/middleware.py` - 中间件配置
  - [ ] CORS处理
  - [ ] 请求日志
  - [ ] 异常处理

### 5.2 API端点开发
- [ ] **5.2.1** `app/api/v1/endpoints/documents.py` - 文档相关API
  - [ ] `POST /api/v1/documents/` - 上传文档
  - [ ] `GET /api/v1/documents/{id}` - 获取文档信息
  - [ ] `POST /api/v1/documents/{id}/analyze` - 分析文档

- [ ] **5.2.2** `app/api/v1/endpoints/tests.py` - 测试相关API
  - [ ] `POST /api/v1/tests/generate` - 生成测试用例
  - [ ] `GET /api/v1/tests/{id}` - 获取测试用例
  - [ ] `POST /api/v1/tests/{id}/execute` - 执行测试

- [ ] **5.2.3** `app/api/v1/endpoints/reports.py` - 报告相关API
  - [ ] `GET /api/v1/reports/{id}` - 获取报告
  - [ ] `POST /api/v1/reports/{id}/export` - 导出报告

- [ ] **5.2.4** `app/api/v1/endpoints/tasks.py` - 任务状态API
  - [ ] `GET /api/v1/tasks/{task_id}` - 查询任务状态

### 5.3 API路由汇总
- [ ] **5.3.1** `app/api/v1/api.py` - 路由汇总
- [ ] **5.3.2** API文档生成和测试

**完成标准**: 所有API端点正常响应，文档自动生成，基础功能测试通过

---

## 阶段6: 异步任务层 (预计1天)

### 6.1 Celery配置
- [ ] **6.1.1** `app/tasks/celery_app.py` - Celery应用配置
- [ ] **6.1.2** Redis连接配置

### 6.2 异步任务定义
- [ ] **6.2.1** `app/tasks/document_tasks.py` - 文档处理任务
  - [ ] 文档分析任务
  - [ ] 质量检查任务

- [ ] **6.2.2** `app/tasks/test_tasks.py` - 测试相关任务
  - [ ] 测试用例生成任务
  - [ ] 测试执行任务

- [ ] **6.2.3** `app/tasks/report_tasks.py` - 报告生成任务

### 6.3 任务状态管理
- [ ] **6.3.1** 任务进度追踪
- [ ] **6.3.2** 任务结果存储
- [ ] **6.3.3** 错误处理和重试机制

**完成标准**: 异步任务能够正常执行，状态追踪正常，错误处理完善

---

## 阶段7: 测试层 (预计1.5天)

### 7.1 单元测试
- [ ] **7.1.1** `tests/unit/test_document_analyzer/` - 文档分析模块测试
- [ ] **7.1.2** `tests/unit/test_test_generator/` - 测试生成模块测试
- [ ] **7.1.3** `tests/unit/test_test_executor/` - 测试执行模块测试
- [ ] **7.1.4** `tests/unit/test_report_analyzer/` - 结果分析模块测试

### 7.2 集成测试
- [ ] **7.2.1** `tests/integration/test_api/` - API集成测试
- [ ] **7.2.2** `tests/integration/test_workflows/` - 完整流程测试

### 7.3 测试数据准备
- [ ] **7.3.1** `tests/fixtures/` - 测试数据文件
  - [ ] 示例OpenAPI文档
  - [ ] 示例Markdown文档
  - [ ] 预期结果数据

**完成标准**: 测试覆盖率 > 80%，所有测试通过，CI/CD流程正常

---

## 阶段8: 部署配置 (预计0.5天)

### 8.1 Docker配置
- [ ] **8.1.1** `docker/Dockerfile` - 应用镜像
- [ ] **8.1.2** `docker/docker-compose.yml` - 服务编排
- [ ] **8.1.3** `docker/docker-compose.dev.yml` - 开发环境

### 8.2 部署脚本
- [ ] **8.2.1** `scripts/init_db.py` - 数据库初始化
- [ ] **8.2.2** `scripts/run_tests.py` - 测试运行脚本
- [ ] **8.2.3** `scripts/deploy.py` - 部署脚本

**完成标准**: Docker容器正常启动，服务间通信正常，部署脚本执行成功

---

## 开发检查清单

### 每个阶段完成后检查
- [ ] 代码符合PEP8规范
- [ ] 所有函数都有类型注解
- [ ] 关键函数都有文档字符串
- [ ] 单元测试覆盖核心逻辑
- [ ] 没有明显的性能问题
- [ ] 错误处理完善

### 里程碑检查
- [ ] **里程碑1**: 单个OpenAPI文档完整流程 (阶段1-6完成)
- [ ] **里程碑2**: 多格式文档支持 (阶段7完成)
- [ ] **里程碑3**: 生产就绪 (阶段8完成)

---

**总预计开发时间**: 12天  
**建议并行开发**: 在阶段4可以多人并行开发不同模块  
**关键风险点**: LLM集成调试、异步任务稳定性、大文档处理性能
