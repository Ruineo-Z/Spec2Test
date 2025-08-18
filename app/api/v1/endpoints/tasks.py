"""
任务状态API端点

提供异步任务状态查询和管理功能。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.shared.utils.logger import get_logger
from app.api.v1.endpoints.documents import documents_store
from app.api.v1.endpoints.tests import test_suites_store, test_executions_store
from app.api.v1.endpoints.reports import reports_store


# 创建路由器
router = APIRouter(prefix="/tasks", tags=["任务"])
logger = get_logger(__name__)


# 响应模型
class TaskStatus(BaseModel):
    """任务状态"""
    task_id: str = Field(description="任务ID")
    task_type: str = Field(description="任务类型")
    status: str = Field(description="任务状态")
    created_at: datetime = Field(description="创建时间")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    progress: Optional[float] = Field(default=None, description="进度百分比")
    message: str = Field(description="状态消息")
    result: Optional[Dict[str, Any]] = Field(default=None, description="任务结果")
    error: Optional[Dict[str, Any]] = Field(default=None, description="错误信息")


class TaskSummary(BaseModel):
    """任务摘要"""
    task_id: str = Field(description="任务ID")
    task_type: str = Field(description="任务类型")
    status: str = Field(description="任务状态")
    created_at: datetime = Field(description="创建时间")
    duration: Optional[float] = Field(default=None, description="执行时长(秒)")


@router.get("/statistics", summary="获取任务统计")
async def get_task_statistics() -> Dict[str, Any]:
    """
    获取任务统计信息

    包括各种任务类型的数量和状态分布
    """
    logger.info("📊 获取任务统计")

    stats = {
        "total_tasks": 0,
        "by_type": {
            "document_analysis": {"total": 0, "completed": 0, "failed": 0, "running": 0},
            "test_generation": {"total": 0, "completed": 0, "failed": 0, "running": 0},
            "test_execution": {"total": 0, "completed": 0, "failed": 0, "running": 0},
            "report_generation": {"total": 0, "completed": 0, "failed": 0, "running": 0}
        },
        "by_status": {
            "completed": 0,
            "failed": 0,
            "running": 0,
            "pending": 0
        }
    }

    # 统计文档分析任务
    for doc_info in documents_store.values():
        if doc_info.get("analysis_id"):
            stats["total_tasks"] += 1
            stats["by_type"]["document_analysis"]["total"] += 1

            status = doc_info["status"]
            if status == "analyzed":
                stats["by_type"]["document_analysis"]["completed"] += 1
                stats["by_status"]["completed"] += 1
            elif status == "analysis_failed":
                stats["by_type"]["document_analysis"]["failed"] += 1
                stats["by_status"]["failed"] += 1
            elif status == "analyzing":
                stats["by_type"]["document_analysis"]["running"] += 1
                stats["by_status"]["running"] += 1

    # 统计测试生成任务
    for suite_info in test_suites_store.values():
        stats["total_tasks"] += 1
        stats["by_type"]["test_generation"]["total"] += 1

        status = suite_info["status"]
        if status == "completed":
            stats["by_type"]["test_generation"]["completed"] += 1
            stats["by_status"]["completed"] += 1
        elif status == "failed":
            stats["by_type"]["test_generation"]["failed"] += 1
            stats["by_status"]["failed"] += 1
        elif status == "generating":
            stats["by_type"]["test_generation"]["running"] += 1
            stats["by_status"]["running"] += 1

    # 统计测试执行任务
    for exec_info in test_executions_store.values():
        stats["total_tasks"] += 1
        stats["by_type"]["test_execution"]["total"] += 1

        status = exec_info["status"]
        if status == "completed":
            stats["by_type"]["test_execution"]["completed"] += 1
            stats["by_status"]["completed"] += 1
        elif status == "failed":
            stats["by_type"]["test_execution"]["failed"] += 1
            stats["by_status"]["failed"] += 1
        elif status == "running":
            stats["by_type"]["test_execution"]["running"] += 1
            stats["by_status"]["running"] += 1

    # 统计报告生成任务
    for report_info in reports_store.values():
        stats["total_tasks"] += 1
        stats["by_type"]["report_generation"]["total"] += 1

        status = report_info["status"]
        if status == "completed":
            stats["by_type"]["report_generation"]["completed"] += 1
            stats["by_status"]["completed"] += 1
        elif status == "failed":
            stats["by_type"]["report_generation"]["failed"] += 1
            stats["by_status"]["failed"] += 1
        elif status == "generating":
            stats["by_type"]["report_generation"]["running"] += 1
            stats["by_status"]["running"] += 1

    logger.info(f"✅ 任务统计获取成功: {stats['total_tasks']} 个任务")

    return stats


@router.get("/{task_id}", response_model=TaskStatus, summary="查询任务状态")
async def get_task_status(task_id: str) -> TaskStatus:
    """
    查询指定任务的详细状态信息
    
    支持的任务类型:
    - document_analysis: 文档分析任务
    - test_generation: 测试生成任务
    - test_execution: 测试执行任务
    - report_generation: 报告生成任务
    """
    logger.info(f"🔍 查询任务状态: {task_id}")
    
    # 尝试在不同的存储中查找任务
    task_info = None
    task_type = None
    
    # 1. 检查文档分析任务
    for doc_id, doc_info in documents_store.items():
        if doc_info.get("analysis_id") == task_id:
            task_info = doc_info
            task_type = "document_analysis"
            break
    
    # 2. 检查测试生成任务
    if not task_info:
        if task_id in test_suites_store:
            task_info = test_suites_store[task_id]
            task_type = "test_generation"
    
    # 3. 检查测试执行任务
    if not task_info:
        if task_id in test_executions_store:
            task_info = test_executions_store[task_id]
            task_type = "test_execution"
    
    # 4. 检查报告生成任务
    if not task_info:
        if task_id in reports_store:
            task_info = reports_store[task_id]
            task_type = "report_generation"
    
    # 如果没有找到任务
    if not task_info:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 构建任务状态响应
    status_info = _build_task_status(task_id, task_type, task_info)
    
    logger.info(f"✅ 任务状态查询成功: {task_id} ({task_type})")
    return status_info


@router.get("/", summary="获取任务列表")
async def list_tasks(
    limit: int = 20,
    offset: int = 0,
    task_type: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取任务列表
    
    支持按任务类型和状态过滤
    """
    logger.info(f"📋 获取任务列表: limit={limit}, offset={offset}")
    
    all_tasks = []
    
    # 收集文档分析任务
    for doc_id, doc_info in documents_store.items():
        if doc_info.get("analysis_id"):
            task_summary = TaskSummary(
                task_id=doc_info["analysis_id"],
                task_type="document_analysis",
                status=doc_info["status"],
                created_at=doc_info["upload_time"],
                duration=_calculate_duration(
                    doc_info.get("analysis_result", {}).get("started_at"),
                    doc_info.get("analysis_result", {}).get("completed_at")
                )
            )
            all_tasks.append(task_summary)
    
    # 收集测试生成任务
    for suite_id, suite_info in test_suites_store.items():
        task_summary = TaskSummary(
            task_id=suite_id,
            task_type="test_generation",
            status=suite_info["status"],
            created_at=suite_info["created_at"],
            duration=_calculate_duration(
                suite_info["created_at"],
                suite_info.get("completed_at")
            )
        )
        all_tasks.append(task_summary)
    
    # 收集测试执行任务
    for exec_id, exec_info in test_executions_store.items():
        task_summary = TaskSummary(
            task_id=exec_id,
            task_type="test_execution",
            status=exec_info["status"],
            created_at=exec_info["started_at"],
            duration=_calculate_duration(
                exec_info["started_at"],
                exec_info.get("completed_at")
            )
        )
        all_tasks.append(task_summary)
    
    # 收集报告生成任务
    for report_id, report_info in reports_store.items():
        task_summary = TaskSummary(
            task_id=report_id,
            task_type="report_generation",
            status=report_info["status"],
            created_at=report_info["created_at"],
            duration=_calculate_duration(
                report_info["created_at"],
                report_info.get("completed_at")
            )
        )
        all_tasks.append(task_summary)
    
    # 过滤
    if task_type:
        all_tasks = [task for task in all_tasks if task.task_type == task_type]
    
    if status:
        all_tasks = [task for task in all_tasks if task.status == status]
    
    # 排序（按创建时间倒序）
    all_tasks.sort(key=lambda x: x.created_at, reverse=True)
    
    # 分页
    total = len(all_tasks)
    tasks = all_tasks[offset:offset + limit]
    
    # 转换为字典格式
    task_list = [task.dict() for task in tasks]
    
    logger.info(f"✅ 任务列表获取成功: {len(task_list)}/{total}")
    
    return {
        "tasks": task_list,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


@router.get("/statistics", summary="获取任务统计")
async def get_task_statistics() -> Dict[str, Any]:
    """
    获取任务统计信息
    
    包括各种任务类型的数量和状态分布
    """
    logger.info("📊 获取任务统计")
    
    stats = {
        "total_tasks": 0,
        "by_type": {
            "document_analysis": {"total": 0, "completed": 0, "failed": 0, "running": 0},
            "test_generation": {"total": 0, "completed": 0, "failed": 0, "running": 0},
            "test_execution": {"total": 0, "completed": 0, "failed": 0, "running": 0},
            "report_generation": {"total": 0, "completed": 0, "failed": 0, "running": 0}
        },
        "by_status": {
            "completed": 0,
            "failed": 0,
            "running": 0,
            "pending": 0
        }
    }
    
    # 统计文档分析任务
    for doc_info in documents_store.values():
        if doc_info.get("analysis_id"):
            stats["total_tasks"] += 1
            stats["by_type"]["document_analysis"]["total"] += 1
            
            status = doc_info["status"]
            if status == "analyzed":
                stats["by_type"]["document_analysis"]["completed"] += 1
                stats["by_status"]["completed"] += 1
            elif status == "analysis_failed":
                stats["by_type"]["document_analysis"]["failed"] += 1
                stats["by_status"]["failed"] += 1
            elif status == "analyzing":
                stats["by_type"]["document_analysis"]["running"] += 1
                stats["by_status"]["running"] += 1
    
    # 统计测试生成任务
    for suite_info in test_suites_store.values():
        stats["total_tasks"] += 1
        stats["by_type"]["test_generation"]["total"] += 1
        
        status = suite_info["status"]
        if status == "completed":
            stats["by_type"]["test_generation"]["completed"] += 1
            stats["by_status"]["completed"] += 1
        elif status == "failed":
            stats["by_type"]["test_generation"]["failed"] += 1
            stats["by_status"]["failed"] += 1
        elif status == "generating":
            stats["by_type"]["test_generation"]["running"] += 1
            stats["by_status"]["running"] += 1
    
    # 统计测试执行任务
    for exec_info in test_executions_store.values():
        stats["total_tasks"] += 1
        stats["by_type"]["test_execution"]["total"] += 1
        
        status = exec_info["status"]
        if status == "completed":
            stats["by_type"]["test_execution"]["completed"] += 1
            stats["by_status"]["completed"] += 1
        elif status == "failed":
            stats["by_type"]["test_execution"]["failed"] += 1
            stats["by_status"]["failed"] += 1
        elif status == "running":
            stats["by_type"]["test_execution"]["running"] += 1
            stats["by_status"]["running"] += 1
    
    # 统计报告生成任务
    for report_info in reports_store.values():
        stats["total_tasks"] += 1
        stats["by_type"]["report_generation"]["total"] += 1
        
        status = report_info["status"]
        if status == "completed":
            stats["by_type"]["report_generation"]["completed"] += 1
            stats["by_status"]["completed"] += 1
        elif status == "failed":
            stats["by_type"]["report_generation"]["failed"] += 1
            stats["by_status"]["failed"] += 1
        elif status == "generating":
            stats["by_type"]["report_generation"]["running"] += 1
            stats["by_status"]["running"] += 1
    
    logger.info(f"✅ 任务统计获取成功: {stats['total_tasks']} 个任务")
    
    return stats


def _build_task_status(task_id: str, task_type: str, task_info: Dict[str, Any]) -> TaskStatus:
    """构建任务状态响应"""
    
    # 根据任务类型构建不同的状态信息
    if task_type == "document_analysis":
        analysis_result = task_info.get("analysis_result", {})
        return TaskStatus(
            task_id=task_id,
            task_type=task_type,
            status=task_info["status"],
            created_at=task_info["upload_time"],
            started_at=analysis_result.get("started_at"),
            completed_at=analysis_result.get("completed_at"),
            message=_get_status_message(task_type, task_info["status"]),
            result=analysis_result.get("result"),
            error=analysis_result.get("error")
        )
    
    elif task_type == "test_generation":
        return TaskStatus(
            task_id=task_id,
            task_type=task_type,
            status=task_info["status"],
            created_at=task_info["created_at"],
            completed_at=task_info.get("completed_at"),
            message=_get_status_message(task_type, task_info["status"]),
            result={"total_tests": task_info["total_tests"]} if task_info["status"] == "completed" else None,
            error=task_info.get("error")
        )
    
    elif task_type == "test_execution":
        return TaskStatus(
            task_id=task_id,
            task_type=task_type,
            status=task_info["status"],
            created_at=task_info["started_at"],
            started_at=task_info["started_at"],
            completed_at=task_info.get("completed_at"),
            message=_get_status_message(task_type, task_info["status"]),
            result=task_info.get("result"),
            error=task_info.get("error")
        )
    
    elif task_type == "report_generation":
        return TaskStatus(
            task_id=task_id,
            task_type=task_type,
            status=task_info["status"],
            created_at=task_info["created_at"],
            completed_at=task_info.get("completed_at"),
            message=_get_status_message(task_type, task_info["status"]),
            result={"formats": task_info["formats"]} if task_info["status"] == "completed" else None,
            error=task_info.get("error")
        )
    
    else:
        # 默认处理
        return TaskStatus(
            task_id=task_id,
            task_type=task_type,
            status="unknown",
            created_at=datetime.now(),
            message="未知任务类型"
        )


def _get_status_message(task_type: str, status: str) -> str:
    """获取状态消息"""
    messages = {
        "document_analysis": {
            "uploaded": "文档已上传，等待分析",
            "analyzing": "正在分析文档...",
            "analyzed": "文档分析完成",
            "analysis_failed": "文档分析失败"
        },
        "test_generation": {
            "generating": "正在生成测试用例...",
            "completed": "测试用例生成完成",
            "failed": "测试用例生成失败"
        },
        "test_execution": {
            "running": "正在执行测试...",
            "completed": "测试执行完成",
            "failed": "测试执行失败"
        },
        "report_generation": {
            "generating": "正在生成报告...",
            "completed": "报告生成完成",
            "failed": "报告生成失败"
        }
    }
    
    return messages.get(task_type, {}).get(status, f"任务状态: {status}")


def _calculate_duration(start_time: Optional[datetime], end_time: Optional[datetime]) -> Optional[float]:
    """计算任务执行时长"""
    if not start_time:
        return None
    
    if not end_time:
        # 如果任务还在进行中，计算到现在的时长
        end_time = datetime.now()
    
    return (end_time - start_time).total_seconds()
