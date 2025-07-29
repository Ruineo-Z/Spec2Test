"""命令行接口

提供Spec2Test项目的命令行工具。
"""

from pathlib import Path
from typing import Optional

import typer
import uvicorn
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.config import get_settings, validate_settings
from app.utils.logger import get_logger, setup_logger

# 创建CLI应用
app = typer.Typer(
    name="spec2test",
    help="🚀 Spec2Test - AI驱动的自动化测试流水线",
    add_completion=False,
)

console = Console()
logger = get_logger(__name__)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="服务器主机地址"),
    port: int = typer.Option(8000, "--port", "-p", help="服务器端口"),
    reload: bool = typer.Option(False, "--reload", "-r", help="启用自动重载"),
    workers: int = typer.Option(1, "--workers", "-w", help="工作进程数"),
    log_level: str = typer.Option("info", "--log-level", "-l", help="日志级别"),
    env_file: Optional[str] = typer.Option(None, "--env-file", "-e", help="环境变量文件路径"),
):
    """启动API服务器"""
    try:
        # 设置环境变量文件
        if env_file:
            import os

            os.environ["ENV_FILE"] = env_file

        # 验证配置
        settings = get_settings()
        validate_settings(settings)

        # 设置日志
        setup_logger(settings.log)

        rprint(
            Panel.fit(
                f"🚀 启动 Spec2Test API 服务器\n"
                f"📍 地址: http://{host}:{port}\n"
                f"🔧 环境: {settings.app.environment}\n"
                f"📝 日志级别: {log_level}",
                title="Spec2Test Server",
                border_style="green",
            )
        )

        # 启动服务器
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,
            log_level=log_level,
            access_log=True,
        )

    except Exception as e:
        console.print(f"❌ 启动服务器失败: {e}", style="red")
        logger.error(f"启动服务器失败: {e}")
        raise typer.Exit(1)


@app.command()
def config(
    show: bool = typer.Option(False, "--show", "-s", help="显示当前配置"),
    validate: bool = typer.Option(False, "--validate", "-v", help="验证配置"),
    env_file: Optional[str] = typer.Option(None, "--env-file", "-e", help="环境变量文件路径"),
):
    """配置管理"""
    try:
        # 设置环境变量文件
        if env_file:
            import os

            os.environ["ENV_FILE"] = env_file

        settings = get_settings()

        if validate:
            validate_settings(settings)
            console.print("✅ 配置验证通过", style="green")
            return

        if show:
            # 创建配置表格
            table = Table(title="Spec2Test 配置信息")
            table.add_column("配置项", style="cyan")
            table.add_column("值", style="magenta")

            # 应用配置
            table.add_row("应用名称", settings.app.name)
            table.add_row("版本", settings.app.version)
            table.add_row("环境", settings.app.environment)
            table.add_row("调试模式", str(settings.app.debug))

            # LLM配置
            table.add_row("LLM提供商", settings.llm.provider)
            table.add_row("LLM模型", settings.llm.model)
            table.add_row("API密钥", "***" if settings.llm.api_key else "未设置")

            # 测试配置
            table.add_row("默认超时", f"{settings.test.default_timeout}秒")
            table.add_row("最大重试", str(settings.test.max_retries))
            table.add_row("并行执行", str(settings.test.parallel_execution))

            # 日志配置
            table.add_row("日志级别", settings.log.level)
            table.add_row("日志格式", settings.log.format)

            console.print(table)
        else:
            console.print("使用 --show 显示配置或 --validate 验证配置")

    except Exception as e:
        console.print(f"❌ 配置操作失败: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def init(
    project_name: str = typer.Argument(..., help="项目名称"),
    directory: Optional[str] = typer.Option(None, "--dir", "-d", help="项目目录"),
    template: str = typer.Option("basic", "--template", "-t", help="项目模板"),
):
    """初始化新的测试项目"""
    try:
        # 确定项目目录
        if directory:
            project_dir = Path(directory) / project_name
        else:
            project_dir = Path.cwd() / project_name

        # 检查目录是否存在
        if project_dir.exists():
            console.print(f"❌ 目录 {project_dir} 已存在", style="red")
            raise typer.Exit(1)

        # 创建项目目录结构
        project_dir.mkdir(parents=True)

        # 创建基本目录结构
        directories = ["docs", "tests", "reports", "configs", "data"]

        for dir_name in directories:
            (project_dir / dir_name).mkdir()

        # 创建基本配置文件
        env_content = f"""# Spec2Test 项目配置
APP_NAME={project_name}
APP_VERSION=0.1.0
APP_ENVIRONMENT=development
APP_DEBUG=true

# LLM配置
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
LLM_API_KEY=your-api-key-here

# 测试配置
TEST_DEFAULT_TIMEOUT=30
TEST_MAX_RETRIES=3
TEST_PARALLEL_EXECUTION=false

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json
"""

        (project_dir / ".env").write_text(env_content, encoding="utf-8")

        # 创建README文件
        readme_content = f"""# {project_name}

使用 Spec2Test 创建的自动化测试项目。

## 快速开始

1. 配置环境变量：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，设置必要的配置
   ```

2. 启动服务：
   ```bash
   spec2test serve --env-file .env
   ```

3. 访问API文档：
   http://localhost:8000/docs

## 目录结构

- `docs/` - 文档目录
- `tests/` - 测试用例目录
- `reports/` - 测试报告目录
- `configs/` - 配置文件目录
- `data/` - 测试数据目录

## 使用说明

请参考 [Spec2Test 文档](https://github.com/your-org/spec2test) 了解详细使用方法。
"""

        (project_dir / "README.md").write_text(readme_content, encoding="utf-8")

        # 创建gitignore文件
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
*.log
logs/

# Reports
reports/*.html
reports/*.json
reports/*.xml

# Temporary files
*.tmp
*.temp
.DS_Store
Thumbs.db
"""

        (project_dir / ".gitignore").write_text(gitignore_content, encoding="utf-8")

        console.print(
            Panel.fit(
                f"✅ 项目 '{project_name}' 初始化成功！\n"
                f"📁 项目目录: {project_dir}\n\n"
                f"下一步：\n"
                f"1. cd {project_name}\n"
                f"2. 编辑 .env 文件设置配置\n"
                f"3. spec2test serve --env-file .env",
                title="项目初始化完成",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(f"❌ 项目初始化失败: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def version():
    """显示版本信息"""
    from app import __version__

    version_info = Table(title="Spec2Test 版本信息")
    version_info.add_column("组件", style="cyan")
    version_info.add_column("版本", style="magenta")

    version_info.add_row("Spec2Test", __version__)

    try:
        import uvicorn

        version_info.add_row("Uvicorn", uvicorn.__version__)
    except ImportError:
        pass

    try:
        import fastapi

        version_info.add_row("FastAPI", fastapi.__version__)
    except ImportError:
        pass

    try:
        import pydantic

        version_info.add_row("Pydantic", pydantic.VERSION)
    except ImportError:
        pass

    console.print(version_info)


@app.command()
def health(
    url: str = typer.Option("http://localhost:8000", "--url", "-u", help="服务器URL")
):
    """检查服务器健康状态"""
    try:
        import httpx

        with console.status("检查服务器状态..."):
            response = httpx.get(f"{url}/health", timeout=10)

        if response.status_code == 200:
            data = response.json()

            health_table = Table(title="服务器健康状态")
            health_table.add_column("项目", style="cyan")
            health_table.add_column("状态", style="magenta")

            health_table.add_row(
                "服务状态", "🟢 正常" if data.get("status") == "healthy" else "🔴 异常"
            )
            health_table.add_row("服务器时间", data.get("timestamp", "未知"))
            health_table.add_row("版本", data.get("version", "未知"))
            health_table.add_row("环境", data.get("environment", "未知"))

            console.print(health_table)
        else:
            console.print(f"❌ 服务器响应异常: {response.status_code}", style="red")

    except Exception as e:
        console.print(f"❌ 无法连接到服务器: {e}", style="red")
        raise typer.Exit(1)


def main():
    """CLI入口点"""
    app()


if __name__ == "__main__":
    main()
