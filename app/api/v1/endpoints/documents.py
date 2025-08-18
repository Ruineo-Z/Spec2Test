"""
文档相关API端点

提供API文档上传、分析和管理功能。
"""

import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.shared.utils.logger import get_logger
from app.core.shared.utils.exceptions import BusinessException, ValidationException
from app.core.document_analyzer import DocumentAnalyzer, AnalysisConfig
from app.core.document_analyzer.models import DocumentAnalysisResult


# 创建路由器
router = APIRouter(prefix="/documents", tags=["文档"])
logger = get_logger(__name__)


# 请求/响应模型
class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    document_id: str = Field(description="文档ID")
    filename: str = Field(description="文件名")
    file_size: int = Field(description="文件大小(字节)")
    content_type: str = Field(description="文件类型")
    upload_time: datetime = Field(description="上传时间")
    status: str = Field(description="状态", default="uploaded")


class DocumentInfo(BaseModel):
    """文档信息"""
    document_id: str = Field(description="文档ID")
    filename: str = Field(description="文件名")
    file_size: int = Field(description="文件大小(字节)")
    content_type: str = Field(description="文件类型")
    upload_time: datetime = Field(description="上传时间")
    status: str = Field(description="状态")
    analysis_result: Optional[Dict[str, Any]] = Field(default=None, description="分析结果")


class DocumentAnalysisRequest(BaseModel):
    """文档分析请求"""
    config: Optional[Dict[str, Any]] = Field(default=None, description="分析配置")
    force_reanalyze: bool = Field(default=False, description="强制重新分析")


class DocumentAnalysisResponse(BaseModel):
    """文档分析响应"""
    document_id: str = Field(description="文档ID")
    analysis_id: str = Field(description="分析ID")
    status: str = Field(description="分析状态")
    started_at: datetime = Field(description="开始时间")
    message: str = Field(description="状态消息")


# 简单的内存存储（生产环境应使用数据库）
documents_store: Dict[str, Dict[str, Any]] = {}
analysis_results_store: Dict[str, DocumentAnalysisResult] = {}


@router.post("/", response_model=DocumentUploadResponse, summary="上传API文档")
async def upload_document(
    file: UploadFile = File(..., description="API文档文件")
) -> DocumentUploadResponse:
    """
    上传API文档文件
    
    支持的文件格式:
    - JSON格式的OpenAPI 3.0规范文档
    - YAML格式的OpenAPI 3.0规范文档
    
    文件大小限制: 10MB
    """
    logger.info(f"📤 接收文档上传请求: {file.filename}")
    
    # 验证文件
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    # 检查文件类型
    allowed_types = ["application/json", "text/yaml", "application/x-yaml", "text/plain"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件类型: {file.content_type}。支持的类型: {', '.join(allowed_types)}"
        )
    
    # 检查文件大小
    max_size = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=413, 
            detail=f"文件大小超过限制 ({max_size} bytes)"
        )
    
    # 生成文档ID
    document_id = str(uuid.uuid4())
    
    # 保存文档信息
    document_info = {
        "document_id": document_id,
        "filename": file.filename,
        "file_size": len(content),
        "content_type": file.content_type,
        "upload_time": datetime.now(),
        "status": "uploaded",
        "content": content.decode('utf-8'),
        "analysis_result": None
    }
    
    documents_store[document_id] = document_info
    
    logger.info(f"✅ 文档上传成功: {document_id} ({file.filename})")
    
    return DocumentUploadResponse(
        document_id=document_id,
        filename=file.filename,
        file_size=len(content),
        content_type=file.content_type,
        upload_time=document_info["upload_time"],
        status="uploaded"
    )


@router.get("/{document_id}", response_model=DocumentInfo, summary="获取文档信息")
async def get_document_info(document_id: str) -> DocumentInfo:
    """
    获取指定文档的详细信息
    
    包括文档基本信息和分析结果（如果已分析）
    """
    logger.info(f"📋 获取文档信息: {document_id}")
    
    # 检查文档是否存在
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    doc_info = documents_store[document_id]
    
    # 构建响应
    response = DocumentInfo(
        document_id=doc_info["document_id"],
        filename=doc_info["filename"],
        file_size=doc_info["file_size"],
        content_type=doc_info["content_type"],
        upload_time=doc_info["upload_time"],
        status=doc_info["status"],
        analysis_result=doc_info.get("analysis_result")
    )
    
    logger.info(f"✅ 文档信息获取成功: {document_id}")
    return response


@router.post("/{document_id}/analyze", response_model=DocumentAnalysisResponse, summary="分析API文档")
async def analyze_document(
    document_id: str,
    request: DocumentAnalysisRequest,
    background_tasks: BackgroundTasks
) -> DocumentAnalysisResponse:
    """
    分析API文档，提取端点信息和数据模型
    
    分析过程包括:
    1. 文档格式验证
    2. OpenAPI规范解析
    3. 端点信息提取
    4. 数据模型分析
    5. 质量评估
    """
    logger.info(f"🔍 开始分析文档: {document_id}")
    
    # 检查文档是否存在
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    doc_info = documents_store[document_id]
    
    # 检查是否需要重新分析
    if not request.force_reanalyze and doc_info.get("analysis_result"):
        logger.info(f"📋 文档已分析，返回现有结果: {document_id}")
        return DocumentAnalysisResponse(
            document_id=document_id,
            analysis_id=doc_info["analysis_result"]["analysis_id"],
            status="completed",
            started_at=doc_info["analysis_result"]["started_at"],
            message="文档已分析完成"
        )
    
    # 生成分析ID
    analysis_id = str(uuid.uuid4())
    
    # 更新文档状态
    doc_info["status"] = "analyzing"
    doc_info["analysis_id"] = analysis_id
    
    # 创建分析配置
    config = AnalysisConfig()
    if request.config:
        # 应用用户配置
        for key, value in request.config.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    # 添加后台分析任务
    background_tasks.add_task(
        _perform_document_analysis,
        document_id,
        analysis_id,
        doc_info["content"],
        config
    )
    
    logger.info(f"🚀 文档分析任务已启动: {document_id} -> {analysis_id}")
    
    return DocumentAnalysisResponse(
        document_id=document_id,
        analysis_id=analysis_id,
        status="analyzing",
        started_at=datetime.now(),
        message="文档分析已开始，请稍后查询结果"
    )


@router.get("/{document_id}/analysis", summary="获取文档分析结果")
async def get_document_analysis(document_id: str) -> Dict[str, Any]:
    """
    获取文档分析结果
    
    返回详细的分析结果，包括端点信息、数据模型、质量评估等
    """
    logger.info(f"📊 获取文档分析结果: {document_id}")
    
    # 检查文档是否存在
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    doc_info = documents_store[document_id]
    
    # 检查是否已分析
    if not doc_info.get("analysis_result"):
        raise HTTPException(status_code=404, detail="文档尚未分析或分析失败")
    
    analysis_result = doc_info["analysis_result"]
    
    logger.info(f"✅ 分析结果获取成功: {document_id}")
    
    return {
        "document_id": document_id,
        "analysis_id": analysis_result["analysis_id"],
        "status": analysis_result["status"],
        "started_at": analysis_result["started_at"],
        "completed_at": analysis_result.get("completed_at"),
        "result": analysis_result.get("result"),
        "error": analysis_result.get("error")
    }


@router.delete("/{document_id}", summary="删除文档")
async def delete_document(document_id: str) -> Dict[str, Any]:
    """
    删除指定的文档及其分析结果
    """
    logger.info(f"🗑️ 删除文档: {document_id}")
    
    # 检查文档是否存在
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 删除文档
    del documents_store[document_id]
    
    # 删除分析结果
    if document_id in analysis_results_store:
        del analysis_results_store[document_id]
    
    logger.info(f"✅ 文档删除成功: {document_id}")
    
    return {
        "message": "文档删除成功",
        "document_id": document_id,
        "deleted_at": datetime.now()
    }


@router.get("/", summary="获取文档列表")
async def list_documents(
    limit: int = 10,
    offset: int = 0,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取文档列表
    
    支持分页和状态过滤
    """
    logger.info(f"📋 获取文档列表: limit={limit}, offset={offset}, status={status}")
    
    # 获取所有文档
    all_docs = list(documents_store.values())
    
    # 状态过滤
    if status:
        all_docs = [doc for doc in all_docs if doc["status"] == status]
    
    # 排序（按上传时间倒序）
    all_docs.sort(key=lambda x: x["upload_time"], reverse=True)
    
    # 分页
    total = len(all_docs)
    docs = all_docs[offset:offset + limit]
    
    # 构建响应
    documents = []
    for doc in docs:
        documents.append({
            "document_id": doc["document_id"],
            "filename": doc["filename"],
            "file_size": doc["file_size"],
            "content_type": doc["content_type"],
            "upload_time": doc["upload_time"],
            "status": doc["status"]
        })
    
    logger.info(f"✅ 文档列表获取成功: {len(documents)}/{total}")
    
    return {
        "documents": documents,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


async def _perform_document_analysis(
    document_id: str,
    analysis_id: str,
    content: str,
    config: AnalysisConfig
):
    """执行文档分析（后台任务）"""
    logger.info(f"🔍 开始执行文档分析: {document_id}")
    
    try:
        # 创建分析器
        analyzer = DocumentAnalyzer(config)
        
        # 执行分析
        result = analyzer.analyze_document_content(content)
        
        # 保存分析结果
        analysis_result = {
            "analysis_id": analysis_id,
            "status": "completed",
            "started_at": datetime.now(),
            "completed_at": datetime.now(),
            "result": {
                "document_info": {
                    "title": result.document_info.title,
                    "version": result.document_info.version,
                    "description": result.document_info.description,
                    "servers": [{"url": server.url, "description": server.description} 
                              for server in result.document_info.servers]
                },
                "endpoints": [
                    {
                        "path": ep.path,
                        "method": ep.method,
                        "summary": ep.summary,
                        "description": ep.description,
                        "parameters": [
                            {
                                "name": param.name,
                                "location": param.location,
                                "type": param.type,
                                "required": param.required,
                                "description": param.description
                            }
                            for param in ep.parameters
                        ],
                        "responses": [
                            {
                                "status_code": resp.status_code,
                                "description": resp.description,
                                "content_type": resp.content_type
                            }
                            for resp in ep.responses
                        ]
                    }
                    for ep in result.endpoints
                ],
                "data_models": [
                    {
                        "name": model.name,
                        "type": model.type,
                        "properties": model.properties,
                        "required": model.required,
                        "description": model.description
                    }
                    for model in result.data_models
                ],
                "quality_score": result.quality_score,
                "issues": [
                    {
                        "type": issue.issue_type,
                        "severity": issue.severity,
                        "message": issue.message,
                        "location": issue.location
                    }
                    for issue in result.issues
                ]
            }
        }
        
        # 更新文档状态
        documents_store[document_id]["status"] = "analyzed"
        documents_store[document_id]["analysis_result"] = analysis_result
        
        # 保存到分析结果存储
        analysis_results_store[document_id] = result
        
        logger.info(f"✅ 文档分析完成: {document_id}")
        
    except Exception as e:
        logger.error(f"❌ 文档分析失败: {document_id} - {str(e)}")
        
        # 保存错误结果
        error_result = {
            "analysis_id": analysis_id,
            "status": "failed",
            "started_at": datetime.now(),
            "completed_at": datetime.now(),
            "error": {
                "type": type(e).__name__,
                "message": str(e)
            }
        }
        
        # 更新文档状态
        documents_store[document_id]["status"] = "analysis_failed"
        documents_store[document_id]["analysis_result"] = error_result
