#!/usr/bin/env python3
"""
API v1 路由汇总
"""

from fastapi import APIRouter

from app.api.v1.endpoints import generator, parser

# 创建API路由器
api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(generator.router, prefix="/generator", tags=["测试用例生成"])

api_router.include_router(parser.router, prefix="/parser", tags=["文档解析"])


# 根路径
@api_router.get("/")
async def api_info():
    """API信息"""
    return {
        "message": "Spec2Test API v1",
        "description": "基于AI的API测试用例生成器",
        "version": "1.0.0",
        "endpoints": {"generator": "测试用例生成相关接口", "parser": "文档解析相关接口"},
    }
