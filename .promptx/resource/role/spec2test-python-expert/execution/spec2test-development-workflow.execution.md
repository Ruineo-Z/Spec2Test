<execution>
  <constraint>
    ## Spec2Test单节点开发硬性约束
    - **单节点限制**：每次只能开发一个TodoList节点，严禁跨节点或批量开发
    - **用户确认门禁**：每个节点完成后必须等待用户确认才能继续下一节点
    - **文档生成强制**：每次开发完成后必须在.dev目录生成开发结果文档
    - **开发顺序不可变**：必须严格按照TodoList中的节点顺序进行，不允许跳跃
    - **技术栈固定**：FastAPI + SQLAlchemy + Celery + Redis + PostgreSQL + Gemini/Ollama，不允许随意替换
    - **目录结构锁定**：严格按照TodoList中定义的目录结构创建，不允许自由发挥
    - **代码质量底线**：PEP8规范、类型注解、文档字符串、单元测试，四项缺一不可
  </constraint>

  <rule>
    ## 单节点开发强制规则
    - **节点门禁制**：每个节点完成后必须生成开发结果文档并等待用户确认
    - **单一职责制**：每次只专注于一个TodoList节点，不得同时开发多个节点
    - **依赖检查制**：开发任何节点前必须确认其依赖节点已完成并通过用户确认
    - **测试同步制**：每个节点开发完成后立即编写对应的单元测试
    - **代码审查制**：每个文件创建后必须进行代码规范检查
    - **文档同步制**：每个函数都必须有完整的文档字符串和类型注解
    - **状态记录制**：必须清楚记录当前节点状态和下一个待开发节点
  </rule>

  <guideline>
    ## 开发指导原则
    - **渐进式验证**：从单元测试→集成测试→端到端测试，逐层验证功能正确性
    - **防御式编程**：每个函数都要有完善的参数验证和异常处理
    - **配置外置化**：所有环境相关配置都通过config.py统一管理
    - **接口标准化**：同类功能的接口设计保持一致的命名和参数风格
    - **日志规范化**：使用loguru统一日志格式，关键操作都要有日志记录
  </guideline>

  <process>
    ## Spec2Test单节点开发标准流程

    ### 单节点执行模板
    ```mermaid
    flowchart TD
        A[接收开发任务] --> B[识别当前节点]
        B --> C[检查依赖节点状态]
        C --> D{依赖是否完成}
        D -->|否| E[提示等待依赖完成]
        D -->|是| F[开始开发当前节点]
        F --> G[创建必要文件]
        G --> H[编写代码实现]
        H --> I[编写单元测试]
        I --> J[代码规范检查]
        J --> K[功能验证测试]
        K --> L[生成开发结果文档]
        L --> M[保存到.dev目录]
        M --> N[通知用户确认]
        N --> O[等待用户确认]
        O --> P{用户确认结果}
        P -->|需要修改| Q[根据反馈修改]
        P -->|确认通过| R[标记节点完成]
        Q --> H
        R --> S[准备下一节点]
        E --> A
    ```

    ### 开发结果文档生成流程
    ```mermaid
    flowchart LR
        A[节点开发完成] --> B[收集开发内容]
        B --> C[生成文档结构]
        C --> D[填充详细信息]
        D --> E[保存到.dev目录]
        E --> F[通知用户审查]
    ```
    
    ### 阶段1: 项目基础设置执行流程
    ```
    1. 创建项目目录结构
       - mkdir -p spec2test-backend/{app,tests,docker,scripts,docs}
       - mkdir -p app/{api,core,models,schemas,tasks}
       - mkdir -p app/core/{document_analyzer,test_generator,test_executor,report_analyzer,shared}
    
    2. 创建基础配置文件
       - pyproject.toml: 项目元信息和依赖管理
       - requirements.txt: Python依赖清单
       - .env.example: 环境变量模板
       - .gitignore: Git忽略规则
       - README.md: 项目说明文档
    
    3. 开发核心配置模块
       - app/config.py: 配置管理类(数据库/LLM/Redis/存储/日志)
       - app/dependencies.py: FastAPI依赖注入
    
    4. 开发基础工具模块
       - app/core/shared/utils/logger.py: loguru日志工具
       - app/core/shared/utils/exceptions.py: 自定义异常类
       - app/core/shared/utils/helpers.py: 通用工具函数
    
    完成标准验证: 项目启动成功 + 配置加载正常 + 日志输出正常
    ```
    
    ### 阶段2: 数据模型层执行流程
    ```
    1. 数据库基础设置
       - app/models/base.py: 基础模型类(时间戳/主键/软删除)
       - 数据库连接配置: SQLAlchemy引擎/会话管理/连接池
    
    2. 核心数据模型开发
       - app/models/document.py: Document模型
       - app/models/test_case.py: TestCase模型
       - app/models/test_result.py: TestResult模型
       - app/models/report.py: Report模型
    
    3. Pydantic Schema开发
       - app/schemas/document.py: 文档Schema
       - app/schemas/test_case.py: 测试用例Schema
       - app/schemas/test_result.py: 测试结果Schema
       - app/schemas/report.py: 报告Schema
    
    4. 数据库迁移配置
       - 配置Alembic迁移工具
       - 创建初始迁移文件
       - 测试迁移脚本执行
    
    完成标准验证: 数据库表创建成功 + 模型关系正确 + Schema验证通过
    ```
    
    ### 阶段3: 共享组件层执行流程
    ```
    1. LLM抽象层开发
       - app/core/shared/llm/base.py: BaseLLMClient接口
       - app/core/shared/llm/gemini.py: Gemini客户端实现
       - app/core/shared/llm/ollama.py: Ollama客户端实现
       - app/core/shared/llm/factory.py: LLM工厂类
    
    2. 存储抽象层开发
       - app/core/shared/storage/file_storage.py: 文件存储组件
       - app/core/shared/storage/db_storage.py: 数据库存储组件
    
    3. HTTP客户端开发
       - app/core/test_executor/http_client.py: HTTP请求客户端
       - 支持各种HTTP方法、认证处理、超时重试机制
    
    完成标准验证: LLM客户端调用正常 + 存储组件功能正常 + HTTP客户端测试通过
    ```
    
    ### 开发结果文档标准模板
    ```markdown
    # 阶段X.Y - [节点名称] - 开发结果

    **开发时间**: YYYY-MM-DD HH:MM
    **节点状态**: ✅ 已完成 / ⚠️ 需修改
    **下一节点**: [下一个待开发节点名称]

    ## 📋 开发内容清单
    - [x] 任务项1：具体完成内容
    - [x] 任务项2：具体完成内容
    - [ ] 遗留问题（如有）

    ## 📁 创建的文件列表
    | 文件路径 | 文件类型 | 主要功能 | 代码行数 |
    |---------|---------|---------|---------|
    | path/to/file1.py | 核心模块 | 功能描述 | 50行 |
    | path/to/file2.py | 配置文件 | 功能描述 | 30行 |

    ## 🧪 测试结果
    - **单元测试**: ✅ 通过 (X/X)
    - **代码规范**: ✅ PEP8检查通过
    - **类型注解**: ✅ 100%覆盖
    - **文档字符串**: ✅ 100%覆盖

    ## ✅ 验证状态
    - [x] 功能实现完整
    - [x] 代码质量达标
    - [x] 测试用例通过
    - [x] 依赖关系正确

    ## 🔄 下一步计划
    **下一个节点**: [具体节点编号和名称]
    **预计开始**: 等待用户确认后开始
    **主要任务**: [简要描述下一节点的主要任务]

    ## 📝 备注说明
    [任何需要特别说明的内容]
    ```
  </process>

  <criteria>
    ## 质量评价标准
    
    ### 代码质量标准
    - ✅ PEP8规范100%符合
    - ✅ 类型注解覆盖率100%
    - ✅ 文档字符串覆盖率100%
    - ✅ 单元测试覆盖率>80%
    - ✅ 集成测试通过率100%
    
    ### 架构质量标准
    - ✅ 模块间依赖关系清晰无循环
    - ✅ 接口设计一致性良好
    - ✅ 错误处理机制完善
    - ✅ 配置管理规范统一
    - ✅ 日志记录完整清晰
    
    ### 功能质量标准
    - ✅ 每个阶段完成标准100%达成
    - ✅ 核心业务流程端到端验证通过
    - ✅ 异常情况处理机制有效
    - ✅ 性能指标满足预期要求
    - ✅ 部署配置正确可用
    
    ### 里程碑验收标准
    - ✅ 里程碑1: 单个OpenAPI文档完整流程可用
    - ✅ 里程碑2: 多格式文档支持功能完整
    - ✅ 里程碑3: 生产环境部署就绪
  </criteria>
</execution>
