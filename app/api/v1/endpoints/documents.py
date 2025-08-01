"""文档管理API端点

提供文档上传、存储、查询等功能。
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List

import yaml
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.db_models import DocumentModel
from app.core.models import DocumentQuality
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# 请求/响应模型


class DocumentValidation(BaseModel):
    """文档验证结果"""

    is_valid: bool = Field(..., description="是否有效")
    format_errors: List[str] = Field(default_factory=list, description="格式错误")
    warnings: List[str] = Field(default_factory=list, description="警告信息")


class DocumentInfo(BaseModel):
    """文档基本信息"""

    format: str = Field(..., description="文档格式")
    version: str = Field(..., description="OpenAPI版本")
    title: str = Field(..., description="API标题")
    endpoint_count: int = Field(..., description="端点数量")
    estimated_complexity: str = Field(..., description="预估复杂度")


class UploadInfo(BaseModel):
    """上传信息"""

    filename: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小")
    file_hash: str = Field(..., description="文件哈希")
    mime_type: str = Field(..., description="MIME类型")
    uploaded_at: str = Field(..., description="上传时间")


class NextStep(BaseModel):
    """下一步操作建议"""

    action: str = Field(..., description="建议操作")
    endpoint: str = Field(..., description="API端点")
    estimated_time: str = Field(..., description="预估时间")


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""

    success: bool = Field(..., description="是否成功")
    document_id: str = Field(..., description="文档ID")
    upload_info: UploadInfo = Field(..., description="上传信息")
    document_info: DocumentInfo = Field(..., description="文档信息")
    validation: DocumentValidation = Field(..., description="验证结果")
    next_step: NextStep = Field(..., description="下一步建议")


class DocumentDetailResponse(BaseModel):
    """文档详情响应"""

    resource_type: str = Field(..., description="资源类型")
    resource_id: str = Field(..., description="资源ID")
    status: str = Field(..., description="处理状态")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    filename: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小")
    endpoint_count: int = Field(..., description="端点数量")
    processing_history: List[Dict[str, Any]] = Field(
        default_factory=list, description="处理历史"
    )
    related_resources: Dict[str, List[str]] = Field(
        default_factory=dict, description="关联资源"
    )
    available_actions: List[str] = Field(default_factory=list, description="可用操作")


# 工具函数
def validate_openapi_content(
    content: str,
) -> tuple[bool, Dict[str, Any], List[str], List[str]]:
    """验证OpenAPI文档内容

    Returns:
        (is_valid, parsed_content, errors, warnings)
    """
    errors = []
    warnings = []
    parsed_content = {}

    try:
        # 尝试解析JSON
        try:
            parsed_content = json.loads(content)
        except json.JSONDecodeError:
            # 尝试解析YAML
            try:
                parsed_content = yaml.safe_load(content)
            except yaml.YAMLError as e:
                errors.append(f"YAML解析错误: {str(e)}")
                return False, {}, errors, warnings

        # 验证OpenAPI基本结构
        if not isinstance(parsed_content, dict):
            errors.append("文档必须是JSON对象格式")
            return False, {}, errors, warnings

        if "openapi" not in parsed_content:
            errors.append("缺少'openapi'字段")
            return False, {}, errors, warnings

        if "info" not in parsed_content:
            errors.append("缺少'info'字段")
            return False, {}, errors, warnings

        if "paths" not in parsed_content:
            warnings.append("缺少'paths'字段，可能是空API文档")

        # 检查版本
        openapi_version = parsed_content.get("openapi", "")
        if not openapi_version.startswith("3."):
            warnings.append(f"OpenAPI版本 {openapi_version} 可能不被完全支持，建议使用3.x版本")

        # 检查基本信息
        info = parsed_content.get("info", {})
        if not info.get("title"):
            warnings.append("建议在info中添加title字段")

        if not info.get("version"):
            warnings.append("建议在info中添加version字段")

        return True, parsed_content, errors, warnings

    except Exception as e:
        errors.append(f"文档解析异常: {str(e)}")
        return False, {}, errors, warnings


def analyze_document_complexity(parsed_content: Dict[str, Any]) -> tuple[int, str]:
    """分析文档复杂度

    Returns:
        (endpoint_count, complexity_level)
    """
    paths = parsed_content.get("paths", {})
    endpoint_count = 0

    for path, methods in paths.items():
        if isinstance(methods, dict):
            endpoint_count += len(
                [
                    m
                    for m in methods.keys()
                    if m.lower()
                    in ["get", "post", "put", "delete", "patch", "head", "options"]
                ]
            )

    # 根据端点数量判断复杂度
    if endpoint_count <= 5:
        complexity = "simple"
    elif endpoint_count <= 20:
        complexity = "medium"
    elif endpoint_count <= 50:
        complexity = "complex"
    else:
        complexity = "very_complex"

    return endpoint_count, complexity


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="OpenAPI文档文件(JSON/YAML)"),
    db: AsyncSession = Depends(get_async_db),
) -> DocumentUploadResponse:
    """上传OpenAPI文档文件

    Args:
        file: OpenAPI文档文件 (JSON/YAML)

    Returns:
        上传结果和文档信息

    Raises:
        HTTPException: 文件格式错误或上传失败
    """
    logger.info(f"Uploading document file: {file.filename}")

    try:
        # 验证文件类型
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")

        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in ["json", "yaml", "yml"]:
            raise HTTPException(
                status_code=400, detail=f"不支持的文件类型: {file_ext}。支持的类型: json, yaml, yml"
            )

        # 读取文件内容
        content = await file.read()
        content_str = content.decode("utf-8")

        # 计算文件哈希
        file_hash = hashlib.md5(content).hexdigest()

        # 验证文档内容
        is_valid, parsed_content, errors, warnings = validate_openapi_content(
            content_str
        )

        if not is_valid:
            raise HTTPException(status_code=400, detail=f"文档格式无效: {'; '.join(errors)}")

        # 分析文档复杂度
        endpoint_count, complexity = analyze_document_complexity(parsed_content)

        # 检查是否已存在相同文档
        existing_doc = await db.execute(
            select(DocumentModel).where(DocumentModel.file_hash == file_hash)
        )
        existing_doc = existing_doc.scalar_one_or_none()

        if existing_doc:
            logger.info(f"Document already exists with ID: {existing_doc.id}")
            document_id = f"doc_{existing_doc.id:08x}"
        else:
            # 创建新文档记录
            document = DocumentModel(
                name=file.filename or "unknown",
                file_path=f"memory://{file.filename or 'unknown'}",
                file_hash=file_hash,
                file_size=len(content),
                mime_type=file.content_type or "application/octet-stream",
                document_type="openapi",
                version=parsed_content.get("openapi", "3.0.0"),
                quality_score=60.0,  # 默认分数，分析后更新
                quality_level=DocumentQuality.FAIR,
                total_endpoints=endpoint_count,
                documented_endpoints=endpoint_count,
                analysis_result={
                    "content": content_str,
                    "parsed_content": parsed_content,
                    "uploaded_at": datetime.now().isoformat(),
                },
            )

            db.add(document)
            await db.commit()
            await db.refresh(document)

            document_id = f"doc_{document.id:08x}"
            logger.info(f"Document stored with ID: {document_id}")

        # 构建响应
        info = parsed_content.get("info", {})
        response = DocumentUploadResponse(
            success=True,
            document_id=document_id,
            upload_info=UploadInfo(
                filename=file.filename or "unknown",
                file_size=len(content),
                file_hash=f"md5:{file_hash}",
                mime_type=file.content_type or "application/octet-stream",
                uploaded_at=datetime.now().isoformat(),
            ),
            document_info=DocumentInfo(
                format="openapi",
                version=parsed_content.get("openapi", "3.0.0"),
                title=info.get("title", "Unknown API"),
                endpoint_count=endpoint_count,
                estimated_complexity=complexity,
            ),
            validation=DocumentValidation(
                is_valid=is_valid, format_errors=errors, warnings=warnings
            ),
            next_step=NextStep(
                action="analyze_document",
                endpoint=f"/api/v1/documents/{document_id}/analyze",
                estimated_time="5-15秒",
            ),
        )

        logger.info(f"Document upload completed: {document_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document_detail(
    document_id: str,
    db: AsyncSession = Depends(get_async_db),
) -> DocumentDetailResponse:
    """获取文档详细信息

    Args:
        document_id: 文档ID

    Returns:
        文档详细信息

    Raises:
        HTTPException: 文档不存在
    """
    logger.info(f"Getting document detail: {document_id}")

    try:
        # 解析文档ID
        hex_id = document_id.replace("doc_", "")
        db_id = int(hex_id, 16)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的文档ID格式")

    # 查询文档
    result = await db.execute(select(DocumentModel).where(DocumentModel.id == db_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 构建响应
    analysis_result = document.analysis_result or {}

    response = DocumentDetailResponse(
        resource_type="document",
        resource_id=document_id,
        status="uploaded",
        created_at=document.created_at.isoformat() if document.created_at else "",
        updated_at=document.updated_at.isoformat() if document.updated_at else "",
        filename=document.name,
        file_size=document.file_size or 0,
        endpoint_count=document.total_endpoints or 0,
        processing_history=[
            {
                "step": "upload",
                "completed_at": analysis_result.get("uploaded_at", ""),
                "duration": 0.5,
            }
        ],
        related_resources={"analyses": [], "test_cases": [], "test_code": []},
        available_actions=["analyze", "delete"],
    )

    logger.info(f"Document detail retrieved: {document_id}")
    return response


@router.get("")
async def list_documents(
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """获取文档列表

    Returns:
        文档列表
    """
    logger.info("Listing documents")

    # 查询所有文档
    result = await db.execute(select(DocumentModel))
    documents = result.scalars().all()

    document_list = []
    for doc in documents:
        document_list.append(
            {
                "id": f"doc_{doc.id:08x}",
                "name": doc.name,
                "upload_time": doc.created_at.isoformat() if doc.created_at else None,
                "file_size": doc.file_size,
                "endpoint_count": doc.total_endpoints,
                "status": "uploaded",
                "document_type": doc.document_type,
            }
        )

    logger.info(f"Found {len(document_list)} documents")

    return {
        "documents": document_list,
        "total": len(document_list),
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """删除文档

    Args:
        document_id: 文档ID

    Returns:
        删除结果

    Raises:
        HTTPException: 文档不存在
    """
    logger.info(f"Deleting document: {document_id}")

    try:
        # 解析文档ID
        hex_id = document_id.replace("doc_", "")
        db_id = int(hex_id, 16)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的文档ID格式")

    # 查询文档
    result = await db.execute(select(DocumentModel).where(DocumentModel.id == db_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 删除文档
    filename = document.name
    await db.delete(document)
    await db.commit()

    logger.info(f"Document deleted: {filename}")

    return {"message": "文档删除成功", "document_id": document_id, "filename": filename}
