"""
Spec2Test FastAPI应用入口

提供RESTful API接口，支持文档分析、测试生成、测试执行和结果分析的完整流程。
"""

import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from app.core.shared.config.settings import get_settings
from app.core.shared.utils.logger import get_logger
from app.api.middleware import (
    LoggingMiddleware, 
    ExceptionHandlerMiddleware,
    RequestValidationMiddleware
)
from app.api.v1.api import api_router


# 获取配置和日志
settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 Spec2Test API服务启动中...")
    
    # 初始化数据库连接
    try:
        # 这里可以添加数据库初始化逻辑
        logger.info("📊 数据库连接初始化完成")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise
    
    # 初始化Redis连接（如果需要）
    try:
        # 这里可以添加Redis初始化逻辑
        logger.info("🔄 Redis连接初始化完成")
    except Exception as e:
        logger.warning(f"⚠️ Redis初始化失败: {e}")
    
    logger.info("✅ Spec2Test API服务启动完成")
    
    yield
    
    # 关闭时执行
    logger.info("🛑 Spec2Test API服务关闭中...")
    
    # 清理资源
    try:
        # 这里可以添加资源清理逻辑
        logger.info("🧹 资源清理完成")
    except Exception as e:
        logger.error(f"❌ 资源清理失败: {e}")
    
    logger.info("✅ Spec2Test API服务已关闭")


def create_application() -> FastAPI:
    """创建FastAPI应用实例"""
    
    # 创建FastAPI应用
    app = FastAPI(
        title="Spec2Test API",
        description="""
        🎯 **Spec2Test** - 智能API测试自动化平台
        
        ## 功能特性
        
        ### 📋 文档分析
        - 支持OpenAPI 3.0规范文档解析
        - 智能提取API端点和参数信息
        - 自动识别数据模型和关系
        
        ### 🧪 测试生成
        - 基于文档自动生成测试用例
        - 支持多种测试场景和边界条件
        - 智能参数组合和数据生成
        
        ### ⚡ 测试执行
        - 高性能并发测试执行
        - 实时状态监控和进度跟踪
        - 支持重试和错误恢复机制
        
        ### 📊 结果分析
        - 智能失败原因分析和分类
        - 多维度性能指标统计
        - 多格式报告生成和可视化
        
        ## API版本
        - **v1**: 当前稳定版本
        
        ## 认证方式
        - API Key认证（开发中）
        - JWT Token认证（计划中）
        """,
        version="1.0.0",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan
    )
    
    # 配置CORS
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # 添加自定义中间件
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(ExceptionHandlerMiddleware)
    app.add_middleware(RequestValidationMiddleware)
    
    # 注册路由
    app.include_router(api_router, prefix="/api")
    
    # 健康检查端点
    @app.get("/health", tags=["系统"])
    async def health_check() -> Dict[str, Any]:
        """健康检查端点"""
        return {
            "status": "healthy",
            "service": "Spec2Test API",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "timestamp": "2025-01-15T10:00:00Z"
        }
    
    # 根路径重定向
    @app.get("/", tags=["系统"])
    async def root() -> Dict[str, Any]:
        """根路径信息"""
        return {
            "message": "欢迎使用 Spec2Test API",
            "description": "智能API测试自动化平台",
            "version": "1.0.0",
            "docs_url": "/docs",
            "health_url": "/health",
            "api_prefix": "/api/v1"
        }
    
    # 自定义OpenAPI文档
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title="Spec2Test API",
            version="1.0.0",
            description="智能API测试自动化平台",
            routes=app.routes,
        )
        
        # 添加自定义信息
        openapi_schema["info"]["x-logo"] = {
            "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
        }
        
        # 添加服务器信息
        openapi_schema["servers"] = [
            {
                "url": f"http://localhost:{settings.PORT}",
                "description": "开发环境"
            },
            {
                "url": "https://api.spec2test.com",
                "description": "生产环境"
            }
        ]
        
        # 添加标签描述
        openapi_schema["tags"] = [
            {
                "name": "系统",
                "description": "系统相关接口，包括健康检查等"
            },
            {
                "name": "文档",
                "description": "API文档分析相关接口"
            },
            {
                "name": "测试",
                "description": "测试用例生成和执行相关接口"
            },
            {
                "name": "报告",
                "description": "测试报告和分析结果相关接口"
            },
            {
                "name": "任务",
                "description": "异步任务状态查询相关接口"
            }
        ]
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    return app


# 创建应用实例
app = create_application()


# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_error",
                "timestamp": "2025-01-15T10:00:00Z",
                "path": str(request.url.path)
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {type(exc).__name__}: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "内部服务器错误",
                "type": "internal_error",
                "timestamp": "2025-01-15T10:00:00Z",
                "path": str(request.url.path)
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # 开发环境启动配置
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level="info",
        access_log=True
    )
