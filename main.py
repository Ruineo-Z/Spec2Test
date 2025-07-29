#!/usr/bin/env python3
"""
Spec2Test - API规范到测试用例生成器
主应用入口点
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core.config import settings
from app.utils.logger import logger


def create_application() -> FastAPI:
    """创建FastAPI应用实例"""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="基于AI的API测试用例生成器",
        version="1.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
    )

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return JSONResponse(
            content={
                "status": "healthy",
                "service": settings.PROJECT_NAME,
                "version": "1.0.0",
            }
        )

    # 启动事件
    @app.on_event("startup")
    async def startup_event():
        """应用启动事件"""
        logger.info(f"启动 {settings.PROJECT_NAME} 服务")
        logger.info(f"API文档地址: http://localhost:8000{settings.API_V1_STR}/docs")

    # 关闭事件
    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭事件"""
        logger.info(f"关闭 {settings.PROJECT_NAME} 服务")

    return app


app = create_application()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
