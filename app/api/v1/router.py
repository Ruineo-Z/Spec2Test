"""API v1 主路由

汇总所有v1版本的API端点路由。
"""

from fastapi import APIRouter

from app.api.v1.endpoints import analyses, documents

# 创建API路由器
api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["Document Management"],
)

api_router.include_router(
    analyses.router,
    prefix="/analyses",
    tags=["Document Analysis"],
)

# TODO: 未来实现的端点
# api_router.include_router(
#     test_cases.router,
#     prefix="/test-cases",
#     tags=["Test Case Generation"],
# )
#
# api_router.include_router(
#     test_code.router,
#     prefix="/test-code",
#     tags=["Test Code Generation"],
# )


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
            "documents": "文档上传和管理",
            "analyses": "AI驱动的文档质量分析",
        },
        "features": [
            "OpenAPI 3.0文档解析",
            "AI驱动的测试用例生成",
            "自动化测试代码生成",
            "并发测试执行",
            "智能测试报告分析",
        ],
    }
