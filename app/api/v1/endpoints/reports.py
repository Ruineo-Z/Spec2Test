"""
报告相关API端点

提供测试报告生成、查看和导出功能。
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Response
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from app.core.shared.utils.logger import get_logger
from app.core.report_analyzer import ResultAnalyzer, ReportGenerator, ReportVisualizer, AnalysisConfig
from app.api.v1.endpoints.tests import test_executions_store


# 创建路由器
router = APIRouter(prefix="/reports", tags=["报告"])
logger = get_logger(__name__)


# 请求/响应模型
class ReportGenerationRequest(BaseModel):
    """报告生成请求"""
    execution_id: str = Field(description="测试执行ID")
    config: Optional[Dict[str, Any]] = Field(default=None, description="分析配置")
    report_formats: List[str] = Field(default=["html"], description="报告格式")


class ReportGenerationResponse(BaseModel):
    """报告生成响应"""
    report_id: str = Field(description="报告ID")
    execution_id: str = Field(description="测试执行ID")
    status: str = Field(description="生成状态")
    started_at: datetime = Field(description="开始时间")
    formats: List[str] = Field(description="报告格式")
    message: str = Field(description="状态消息")


class ReportInfo(BaseModel):
    """报告信息"""
    report_id: str = Field(description="报告ID")
    execution_id: str = Field(description="测试执行ID")
    report_name: str = Field(description="报告名称")
    formats: List[str] = Field(description="可用格式")
    created_at: datetime = Field(description="创建时间")
    status: str = Field(description="状态")
    file_sizes: Dict[str, int] = Field(description="文件大小")


class ReportExportRequest(BaseModel):
    """报告导出请求"""
    format: str = Field(description="导出格式", default="html")
    include_charts: bool = Field(description="包含图表", default=True)


# 简单的内存存储
reports_store: Dict[str, Dict[str, Any]] = {}


@router.post("/generate", response_model=ReportGenerationResponse, summary="生成测试报告")
async def generate_report(
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks
) -> ReportGenerationResponse:
    """
    基于测试执行结果生成分析报告
    
    生成过程包括:
    1. 分析测试执行结果
    2. 识别失败模式和性能问题
    3. 生成改进建议
    4. 创建多格式报告
    5. 生成可视化图表
    """
    logger.info(f"📊 开始生成测试报告: {request.execution_id}")
    
    # 检查测试执行是否存在且已完成
    if request.execution_id not in test_executions_store:
        raise HTTPException(status_code=404, detail="测试执行记录不存在")
    
    execution_info = test_executions_store[request.execution_id]
    if execution_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="测试执行尚未完成")
    
    if not execution_info.get("execution_result"):
        raise HTTPException(status_code=404, detail="测试执行结果不存在")
    
    # 验证报告格式
    supported_formats = ["html", "markdown", "json", "pdf"]
    invalid_formats = [fmt for fmt in request.report_formats if fmt not in supported_formats]
    if invalid_formats:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的报告格式: {invalid_formats}。支持的格式: {supported_formats}"
        )
    
    # 生成报告ID
    report_id = str(uuid.uuid4())
    
    # 创建报告记录
    report_info = {
        "report_id": report_id,
        "execution_id": request.execution_id,
        "report_name": f"测试报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "status": "generating",
        "created_at": datetime.now(),
        "formats": request.report_formats,
        "config": request.config or {},
        "files": {},
        "file_sizes": {},
        "analysis_report": None
    }
    
    reports_store[report_id] = report_info
    
    # 添加后台生成任务
    background_tasks.add_task(
        _perform_report_generation,
        report_id,
        request.execution_id,
        request.config or {},
        request.report_formats
    )
    
    logger.info(f"🚀 报告生成任务已启动: {report_id}")
    
    return ReportGenerationResponse(
        report_id=report_id,
        execution_id=request.execution_id,
        status="generating",
        started_at=datetime.now(),
        formats=request.report_formats,
        message="报告生成已开始，请稍后查询结果"
    )


@router.get("/{report_id}", response_model=ReportInfo, summary="获取报告信息")
async def get_report_info(report_id: str) -> ReportInfo:
    """
    获取报告的基本信息和生成状态
    """
    logger.info(f"📋 获取报告信息: {report_id}")
    
    # 检查报告是否存在
    if report_id not in reports_store:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    report_info = reports_store[report_id]
    
    response = ReportInfo(
        report_id=report_info["report_id"],
        execution_id=report_info["execution_id"],
        report_name=report_info["report_name"],
        formats=report_info["formats"],
        created_at=report_info["created_at"],
        status=report_info["status"],
        file_sizes=report_info["file_sizes"]
    )
    
    logger.info(f"✅ 报告信息获取成功: {report_id}")
    return response


@router.get("/{report_id}/content", summary="获取报告内容")
async def get_report_content(
    report_id: str,
    format: str = "html"
) -> Dict[str, Any]:
    """
    获取指定格式的报告内容
    
    支持的格式: html, markdown, json
    """
    logger.info(f"📄 获取报告内容: {report_id} ({format})")
    
    # 检查报告是否存在
    if report_id not in reports_store:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    report_info = reports_store[report_id]
    
    # 检查报告是否已生成
    if report_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="报告尚未生成完成")
    
    # 检查格式是否可用
    if format not in report_info["files"]:
        raise HTTPException(status_code=404, detail=f"报告格式 {format} 不存在")
    
    content = report_info["files"][format]
    
    logger.info(f"✅ 报告内容获取成功: {report_id} ({format})")
    
    return {
        "report_id": report_id,
        "format": format,
        "content": content,
        "generated_at": report_info["created_at"]
    }


@router.post("/{report_id}/export", summary="导出报告文件")
async def export_report(
    report_id: str,
    request: ReportExportRequest
) -> Response:
    """
    导出报告为文件
    
    支持导出为HTML、Markdown、JSON等格式
    """
    logger.info(f"📤 导出报告: {report_id} ({request.format})")
    
    # 检查报告是否存在
    if report_id not in reports_store:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    report_info = reports_store[report_id]
    
    # 检查报告是否已生成
    if report_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="报告尚未生成完成")
    
    # 检查格式是否可用
    if request.format not in report_info["files"]:
        raise HTTPException(status_code=404, detail=f"报告格式 {request.format} 不存在")
    
    content = report_info["files"][request.format]
    
    # 设置文件名和Content-Type
    filename = f"{report_info['report_name']}.{request.format}"
    content_types = {
        "html": "text/html",
        "markdown": "text/markdown",
        "json": "application/json",
        "pdf": "application/pdf"
    }
    content_type = content_types.get(request.format, "text/plain")
    
    logger.info(f"✅ 报告导出成功: {report_id} ({request.format})")
    
    return Response(
        content=content.encode('utf-8') if isinstance(content, str) else content,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length": str(len(content))
        }
    )


@router.get("/{report_id}/summary", summary="获取报告摘要")
async def get_report_summary(report_id: str) -> Dict[str, Any]:
    """
    获取报告的摘要信息
    
    包括关键指标、主要发现和建议
    """
    logger.info(f"📋 获取报告摘要: {report_id}")
    
    # 检查报告是否存在
    if report_id not in reports_store:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    report_info = reports_store[report_id]
    
    # 检查报告是否已生成
    if report_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="报告尚未生成完成")
    
    analysis_report = report_info.get("analysis_report")
    if not analysis_report:
        raise HTTPException(status_code=404, detail="分析报告不存在")
    
    # 构建摘要
    summary = {
        "report_id": report_id,
        "execution_id": report_info["execution_id"],
        "overall_metrics": {
            "total_tests": analysis_report.overall_metrics.total_tests,
            "passed_tests": analysis_report.overall_metrics.passed_tests,
            "failed_tests": analysis_report.overall_metrics.failed_tests,
            "success_rate": analysis_report.overall_metrics.success_rate,
            "avg_response_time": analysis_report.overall_metrics.avg_response_time,
            "total_execution_time": analysis_report.overall_metrics.total_execution_time
        },
        "risk_level": analysis_report.risk_level,
        "key_findings": analysis_report.key_findings,
        "recommendations": analysis_report.recommendations,
        "critical_issues": analysis_report.critical_issues,
        "failure_patterns_count": len(analysis_report.failure_patterns),
        "endpoints_analyzed": len(analysis_report.endpoint_analyses)
    }
    
    logger.info(f"✅ 报告摘要获取成功: {report_id}")
    return summary


@router.get("/", summary="获取报告列表")
async def list_reports(
    limit: int = 10,
    offset: int = 0,
    execution_id: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取报告列表
    
    支持按执行ID和状态过滤
    """
    logger.info(f"📋 获取报告列表: limit={limit}, offset={offset}")
    
    # 获取所有报告
    all_reports = list(reports_store.values())
    
    # 过滤
    if execution_id:
        all_reports = [report for report in all_reports if report["execution_id"] == execution_id]
    
    if status:
        all_reports = [report for report in all_reports if report["status"] == status]
    
    # 排序（按创建时间倒序）
    all_reports.sort(key=lambda x: x["created_at"], reverse=True)
    
    # 分页
    total = len(all_reports)
    reports = all_reports[offset:offset + limit]
    
    # 构建响应
    report_list = []
    for report in reports:
        report_list.append({
            "report_id": report["report_id"],
            "execution_id": report["execution_id"],
            "report_name": report["report_name"],
            "formats": report["formats"],
            "created_at": report["created_at"],
            "status": report["status"],
            "file_sizes": report["file_sizes"]
        })
    
    logger.info(f"✅ 报告列表获取成功: {len(report_list)}/{total}")
    
    return {
        "reports": report_list,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


@router.delete("/{report_id}", summary="删除报告")
async def delete_report(report_id: str) -> Dict[str, Any]:
    """
    删除指定的报告及其所有文件
    """
    logger.info(f"🗑️ 删除报告: {report_id}")
    
    # 检查报告是否存在
    if report_id not in reports_store:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # 删除报告
    del reports_store[report_id]
    
    logger.info(f"✅ 报告删除成功: {report_id}")
    
    return {
        "message": "报告删除成功",
        "report_id": report_id,
        "deleted_at": datetime.now()
    }


async def _perform_report_generation(
    report_id: str,
    execution_id: str,
    config: Dict[str, Any],
    formats: List[str]
):
    """执行报告生成（后台任务）"""
    logger.info(f"📊 开始执行报告生成: {report_id}")
    
    try:
        # 获取测试执行结果
        execution_info = test_executions_store[execution_id]
        execution_result = execution_info["execution_result"]
        
        # 创建分析配置
        analysis_config = AnalysisConfig()
        for key, value in config.items():
            if hasattr(analysis_config, key):
                setattr(analysis_config, key, value)
        
        # 创建结果分析器
        analyzer = ResultAnalyzer(analysis_config)
        
        # 分析测试结果
        analysis_report = analyzer.analyze_suite_result(execution_result)
        
        # 创建报告生成器
        generator = ReportGenerator(analysis_config)
        
        # 生成不同格式的报告
        files = {}
        file_sizes = {}
        
        for format_type in formats:
            if format_type == "html":
                content = generator.generate_html_report(analysis_report)
            elif format_type == "markdown":
                content = generator.generate_markdown_report(analysis_report)
            elif format_type == "json":
                content = generator.generate_json_report(analysis_report)
            else:
                continue  # 跳过不支持的格式
            
            files[format_type] = content
            file_sizes[format_type] = len(content.encode('utf-8'))
        
        # 更新报告记录
        reports_store[report_id].update({
            "status": "completed",
            "completed_at": datetime.now(),
            "files": files,
            "file_sizes": file_sizes,
            "analysis_report": analysis_report
        })
        
        logger.info(f"✅ 报告生成完成: {report_id} ({len(formats)} 种格式)")
        
    except Exception as e:
        logger.error(f"❌ 报告生成失败: {report_id} - {str(e)}")
        
        # 更新失败状态
        reports_store[report_id].update({
            "status": "failed",
            "completed_at": datetime.now(),
            "error": {
                "type": type(e).__name__,
                "message": str(e)
            }
        })
