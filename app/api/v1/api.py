"""
API v1路由汇总

汇总所有v1版本的API端点。
"""

from fastapi import APIRouter

from app.api.v1.endpoints import documents, tests, reports, tasks


# 创建v1路由器
api_router = APIRouter(prefix="/v1")

# 注册各个端点路由
api_router.include_router(documents.router)
api_router.include_router(tests.router)
api_router.include_router(reports.router)
api_router.include_router(tasks.router)


# API信息端点
@api_router.get("/", tags=["系统"])
async def api_info():
    """API版本信息"""
    return {
        "version": "1.0.0",
        "title": "Spec2Test API v1",
        "description": "智能API测试自动化平台 - 第一版API",
        "endpoints": {
            "documents": {
                "description": "文档管理和分析",
                "endpoints": [
                    "POST /documents/ - 上传文档",
                    "GET /documents/{id} - 获取文档信息",
                    "POST /documents/{id}/analyze - 分析文档",
                    "GET /documents/{id}/analysis - 获取分析结果",
                    "DELETE /documents/{id} - 删除文档",
                    "GET /documents/ - 获取文档列表"
                ]
            },
            "tests": {
                "description": "测试用例生成和执行",
                "endpoints": [
                    "POST /tests/generate - 生成测试用例",
                    "GET /tests/{id} - 获取测试套件",
                    "POST /tests/{id}/execute - 执行测试",
                    "GET /tests/{suite_id}/executions/{exec_id} - 获取执行结果",
                    "GET /tests/ - 获取测试套件列表"
                ]
            },
            "reports": {
                "description": "测试报告生成和管理",
                "endpoints": [
                    "POST /reports/generate - 生成报告",
                    "GET /reports/{id} - 获取报告信息",
                    "GET /reports/{id}/content - 获取报告内容",
                    "POST /reports/{id}/export - 导出报告",
                    "GET /reports/{id}/summary - 获取报告摘要",
                    "DELETE /reports/{id} - 删除报告",
                    "GET /reports/ - 获取报告列表"
                ]
            },
            "tasks": {
                "description": "异步任务状态查询",
                "endpoints": [
                    "GET /tasks/{id} - 查询任务状态",
                    "GET /tasks/ - 获取任务列表",
                    "GET /tasks/statistics - 获取任务统计"
                ]
            }
        },
        "workflow": {
            "description": "典型的API测试自动化工作流程",
            "steps": [
                {
                    "step": 1,
                    "action": "上传API文档",
                    "endpoint": "POST /documents/",
                    "description": "上传OpenAPI 3.0规范文档"
                },
                {
                    "step": 2,
                    "action": "分析文档",
                    "endpoint": "POST /documents/{id}/analyze",
                    "description": "解析文档，提取端点和数据模型"
                },
                {
                    "step": 3,
                    "action": "生成测试用例",
                    "endpoint": "POST /tests/generate",
                    "description": "基于文档分析结果生成测试用例"
                },
                {
                    "step": 4,
                    "action": "执行测试",
                    "endpoint": "POST /tests/{id}/execute",
                    "description": "对目标API执行测试用例"
                },
                {
                    "step": 5,
                    "action": "生成报告",
                    "endpoint": "POST /reports/generate",
                    "description": "分析测试结果并生成报告"
                },
                {
                    "step": 6,
                    "action": "查看报告",
                    "endpoint": "GET /reports/{id}/content",
                    "description": "查看或导出测试分析报告"
                }
            ]
        },
        "features": [
            "📋 智能文档分析 - 自动解析OpenAPI规范",
            "🧪 自动测试生成 - 基于文档生成全面测试用例",
            "⚡ 高性能执行 - 并发测试执行和实时监控",
            "📊 智能结果分析 - 失败模式识别和性能分析",
            "📄 多格式报告 - HTML、Markdown、JSON等格式",
            "🔄 异步任务处理 - 后台任务和状态跟踪",
            "🎯 RESTful设计 - 标准的REST API接口",
            "📖 自动文档生成 - Swagger/OpenAPI文档"
        ]
    }
