"""Spec2Test FastAPI应用主入口

AI驱动的自动化测试流水线主应用。
"""

import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config.settings import settings, validate_settings
from app.core.database import database_lifespan
from app.utils.exceptions import Spec2TestException
from app.utils.logger import get_logger, log_api_request, setup_logger

# 加载.env文件
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 已加载环境变量文件: {env_path}")
    # 验证关键环境变量
    if os.getenv("GEMINI_API_KEY"):
        print(f"✅ GEMINI_API_KEY已设置")
    else:
        print(f"⚠️  GEMINI_API_KEY未设置")
else:
    print(f"⚠️  环境变量文件不存在: {env_path}")

# 设置日志
setup_logger()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("Starting Spec2Test application...")

    # 验证配置
    if not validate_settings():
        logger.error("Configuration validation failed")
        raise RuntimeError("Invalid configuration")

    # 初始化数据库
    async with database_lifespan():
        logger.info(
            f"Application {settings.app_name} v{settings.app_version} started successfully"
        )

        yield

    # 关闭时执行
    logger.info("Shutting down Spec2Test application...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI驱动的自动化测试流水线 - 从API规范文档到测试报告的全流程自动化",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


# 添加受信任主机中间件
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", settings.api_host],
    )


# 请求处理时间中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加请求处理时间头"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# 请求日志中间件
@app.middleware("http")
@log_api_request
async def log_requests(request: Request, call_next):
    """记录API请求日志"""
    return await call_next(request)


# 全局异常处理器
@app.exception_handler(Spec2TestException)
async def spec2test_exception_handler(request: Request, exc: Spec2TestException):
    """处理自定义异常"""
    logger.error(
        f"Spec2Test error: {exc.message}", extra={"error_code": exc.error_code}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """处理HTTP异常"""
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理通用异常"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": (
                    "An unexpected error occurred" if not settings.debug else str(exc)
                ),
            }
        },
    )


# 健康检查接口
@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """健康检查接口

    Returns:
        应用健康状态信息
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "timestamp": time.time(),
        "debug": settings.debug,
    }


# 根路径
@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """根路径接口

    Returns:
        应用基本信息
    """
    return {
        "message": "Welcome to Spec2Test API",
        "description": "AI驱动的自动化测试流水线",
        "version": settings.app_version,
        "docs_url": "/docs",
        "health_url": "/health",
        "api_prefix": settings.api_prefix,
    }


# 包含API路由
app.include_router(api_router, prefix=settings.api_prefix)


# CLI入口点
def cli():
    """命令行入口点"""
    import typer

    app_cli = typer.Typer()

    @app_cli.command()
    def serve(
        host: str = typer.Option(settings.api_host, help="Host to bind"),
        port: int = typer.Option(settings.api_port, help="Port to bind"),
        reload: bool = typer.Option(settings.debug, help="Enable auto-reload"),
        workers: int = typer.Option(1, help="Number of worker processes"),
    ):
        """启动API服务器"""
        logger.info(f"Starting server on {host}:{port}")
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,
            log_config=None,  # 使用我们的loguru配置
        )

    @app_cli.command()
    def validate_config():
        """验证配置"""
        if validate_settings():
            typer.echo("✅ Configuration is valid")
        else:
            typer.echo("❌ Configuration validation failed")
            raise typer.Exit(1)

    app_cli()


if __name__ == "__main__":
    # 直接运行时启动服务器
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_config=None,
    )
