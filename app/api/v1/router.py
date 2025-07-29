"""API v1 主路由

汇总所有v1版本的API端点路由。
"""

from fastapi import APIRouter

from app.api.v1.endpoints import executor, generator, parser, reporter

# 创建API路由器
api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(
    parser.router,
    prefix="/parser",
    tags=["Document Parser"],
)

api_router.include_router(
    generator.router,
    prefix="/generator",
    tags=["Test Generator"],
)

api_router.include_router(
    executor.router,
    prefix="/executor",
    tags=["Test Executor"],
)

api_router.include_router(
    reporter.router,
    prefix="/reporter",
    tags=["Test Reporter"],
)


# API信息接口
@api_router.get("/info", tags=["API Info"])
async def api_info():
    """获取API信息

    Returns:
        API版本和功能信息
    """
    return {
        "version": "v1",
        "description": "Spec2Test API v1 - AI驱动的自动化测试流水线",
        "endpoints": {
            "parser": "文档解析和质量分析",
            "generator": "AI测试用例和代码生成",
            "executor": "测试执行和结果收集",
            "reporter": "测试报告生成和AI分析",
        },
        "features": [
            "OpenAPI 3.0文档解析",
            "AI驱动的测试用例生成",
            "自动化测试代码生成",
            "并发测试执行",
            "智能测试报告分析",
        ],
    }
