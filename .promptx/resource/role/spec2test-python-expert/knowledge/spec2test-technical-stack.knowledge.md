<knowledge>
  ## Spec2Test项目特定技术栈配置
  
  ### FastAPI项目结构约定
  ```
  spec2test-backend/
  ├── app/
  │   ├── main.py              # FastAPI应用入口
  │   ├── config.py            # 配置管理
  │   ├── dependencies.py      # 依赖注入
  │   ├── api/v1/              # API路由版本管理
  │   ├── core/                # 核心业务模块
  │   ├── models/              # SQLAlchemy模型
  │   ├── schemas/             # Pydantic模式
  │   └── tasks/               # Celery异步任务
  ```
  
  ### SQLAlchemy模型设计规范
  ```python
  # 基础模型模板 (app/models/base.py)
  class BaseModel(DeclarativeBase):
      id: Mapped[int] = mapped_column(primary_key=True)
      created_at: Mapped[datetime] = mapped_column(default=func.now())
      updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
      is_deleted: Mapped[bool] = mapped_column(default=False)
  ```
  
  ### Celery任务配置模式
  ```python
  # app/tasks/celery_app.py
  celery_app = Celery(
      "spec2test",
      broker="redis://localhost:6379/0",
      backend="redis://localhost:6379/0",
      include=["app.tasks.document_tasks", "app.tasks.test_tasks", "app.tasks.report_tasks"]
  )
  ```
  
  ### LLM客户端接口标准
  ```python
  # app/core/shared/llm/base.py
  class BaseLLMClient(ABC):
      @abstractmethod
      async def generate_text(self, prompt: str, schema: Optional[dict] = None) -> dict:
          """生成文本内容，支持结构化输出"""
          pass
      
      @abstractmethod
      async def analyze_document(self, content: str) -> dict:
          """分析文档内容，提取关键信息"""
          pass
  ```
  
  ## 核心业务模块特定实现模式
  
  ### 文档分析器架构
  ```python
  # app/core/document_analyzer/parser.py
  class DocumentParser:
      def parse_openapi(self, content: str) -> OpenAPISpec: ...
      def parse_markdown(self, content: str) -> MarkdownDoc: ...
      def detect_document_type(self, content: str) -> DocumentType: ...
  
  # app/core/document_analyzer/validator.py  
  class DocumentValidator:
      def check_completeness(self, doc: Document) -> ValidationResult: ...
      def check_consistency(self, doc: Document) -> ValidationResult: ...
      def generate_suggestions(self, doc: Document) -> List[Suggestion]: ...
  ```
  
  ### 测试生成器架构
  ```python
  # app/core/test_generator/case_generator.py
  class TestCaseGenerator:
      def generate_normal_cases(self, endpoint: Endpoint) -> List[TestCase]: ...
      def generate_boundary_cases(self, endpoint: Endpoint) -> List[TestCase]: ...
      def generate_error_cases(self, endpoint: Endpoint) -> List[TestCase]: ...
  ```
  
  ### HTTP客户端配置
  ```python
  # app/core/test_executor/http_client.py
  class HTTPClient:
      def __init__(self, timeout: int = 30, max_retries: int = 3): ...
      async def request(self, method: str, url: str, **kwargs) -> Response: ...
      def add_auth(self, auth_type: str, credentials: dict): ...
  ```
  
  ## 异步任务设计模式
  
  ### 任务状态追踪机制
  ```python
  # app/tasks/base.py
  @celery_app.task(bind=True)
  def base_task(self, *args, **kwargs):
      try:
          self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100})
          # 任务执行逻辑
          self.update_state(state='SUCCESS', meta={'result': result})
      except Exception as exc:
          self.update_state(state='FAILURE', meta={'error': str(exc)})
  ```
  
  ### 文档处理任务模式
  ```python
  # app/tasks/document_tasks.py
  @celery_app.task
  def analyze_document_task(document_id: int) -> dict:
      """异步文档分析任务"""
      pass
  
  @celery_app.task  
  def validate_document_task(document_id: int) -> dict:
      """异步文档质量检查任务"""
      pass
  ```
  
  ## API设计规范
  
  ### RESTful API路径约定
  ```
  POST   /api/v1/documents/              # 上传文档
  GET    /api/v1/documents/{id}          # 获取文档信息
  POST   /api/v1/documents/{id}/analyze  # 分析文档
  POST   /api/v1/tests/generate          # 生成测试用例
  GET    /api/v1/tests/{id}              # 获取测试用例
  POST   /api/v1/tests/{id}/execute      # 执行测试
  GET    /api/v1/reports/{id}            # 获取报告
  POST   /api/v1/reports/{id}/export     # 导出报告
  GET    /api/v1/tasks/{task_id}         # 查询任务状态
  ```
  
  ### 响应格式标准
  ```python
  # 成功响应格式
  {
      "success": true,
      "data": {...},
      "message": "操作成功"
  }
  
  # 错误响应格式
  {
      "success": false,
      "error": {
          "code": "VALIDATION_ERROR",
          "message": "参数验证失败",
          "details": {...}
      }
  }
  ```
  
  ## 测试策略配置
  
  ### pytest配置模式
  ```python
  # tests/conftest.py
  @pytest.fixture
  def test_db():
      """测试数据库fixture"""
      pass
  
  @pytest.fixture
  def mock_llm_client():
      """Mock LLM客户端fixture"""
      pass
  
  @pytest.fixture
  def sample_openapi_doc():
      """示例OpenAPI文档fixture"""
      pass
  ```
  
  ### Docker部署配置
  ```yaml
  # docker/docker-compose.yml
  version: '3.8'
  services:
    app:
      build: .
      ports: ["8000:8000"]
      depends_on: [db, redis]
    db:
      image: postgres:15
      environment:
        POSTGRES_DB: spec2test
    redis:
      image: redis:7-alpine
    celery:
      build: .
      command: celery -A app.tasks.celery_app worker
  ```
</knowledge>
