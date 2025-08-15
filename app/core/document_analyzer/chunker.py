"""
文档分块器

将大型API文档分割成适合LLM处理的小块。
"""

from typing import List
from .models import DocumentAnalysisResult, DocumentChunk, ChunkingStrategy, APIEndpoint
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentChunker:
    """文档分块器
    
    将大型API文档分割成适合LLM处理的小块。
    """
    
    def __init__(self):
        """初始化文档分块器"""
        self.logger = get_logger(f"{self.__class__.__name__}")
        self.logger.info("文档分块器初始化完成")
    
    def chunk_document(self, analysis_result: DocumentAnalysisResult, 
                      strategy: ChunkingStrategy) -> DocumentAnalysisResult:
        """对文档进行分块
        
        Args:
            analysis_result: 文档分析结果
            strategy: 分块策略
            
        Returns:
            DocumentAnalysisResult: 包含分块信息的分析结果
        """
        try:
            self.logger.info("开始文档分块")
            
            # 验证分块策略
            strategy_errors = strategy.validate_settings()
            if strategy_errors:
                self.logger.error(f"分块策略配置错误: {strategy_errors}")
                return analysis_result
            
            chunks = []
            
            if strategy.chunk_by_endpoint and analysis_result.endpoints:
                # 按端点分块
                chunks.extend(self._chunk_by_endpoints(analysis_result, strategy))
            else:
                # 按内容大小分块
                chunks.extend(self._chunk_by_size(analysis_result, strategy))
            
            analysis_result.chunks = chunks
            
            self.logger.info(f"文档分块完成: {len(chunks)}个分块")
            return analysis_result
            
        except Exception as e:
            error_msg = f"文档分块失败: {str(e)}"
            self.logger.error(error_msg)
            return analysis_result
    
    def _chunk_by_endpoints(self, analysis_result: DocumentAnalysisResult, 
                           strategy: ChunkingStrategy) -> List[DocumentChunk]:
        """按端点分块"""
        chunks = []
        current_chunk_content = []
        current_chunk_endpoints = []
        current_token_count = 0
        
        # 添加基本信息到第一个分块
        basic_info = self._format_basic_info(analysis_result)
        basic_token_count = self._estimate_token_count(basic_info)
        
        if basic_token_count < strategy.max_tokens:
            current_chunk_content.append(basic_info)
            current_token_count += basic_token_count
        
        for i, endpoint in enumerate(analysis_result.endpoints):
            endpoint_content = self._format_endpoint(endpoint)
            endpoint_token_count = self._estimate_token_count(endpoint_content)
            
            # 检查是否需要创建新分块
            if (current_token_count + endpoint_token_count > strategy.max_tokens and 
                current_chunk_content):
                
                # 创建当前分块
                chunk = DocumentChunk(
                    chunk_id=f"chunk_{len(chunks) + 1}",
                    content="\n\n".join(current_chunk_content),
                    chunk_type="endpoint_group",
                    token_count=current_token_count,
                    endpoints=current_chunk_endpoints.copy(),
                    metadata={
                        "endpoint_count": len(current_chunk_endpoints),
                        "chunk_index": len(chunks)
                    }
                )
                chunks.append(chunk)
                
                # 重置当前分块（保留重叠内容）
                if strategy.overlap_tokens > 0 and current_chunk_content:
                    overlap_content = current_chunk_content[-1]  # 保留最后一个端点
                    overlap_tokens = self._estimate_token_count(overlap_content)
                    if overlap_tokens <= strategy.overlap_tokens:
                        current_chunk_content = [overlap_content]
                        current_token_count = overlap_tokens
                        current_chunk_endpoints = [current_chunk_endpoints[-1]]
                    else:
                        current_chunk_content = []
                        current_token_count = 0
                        current_chunk_endpoints = []
                else:
                    current_chunk_content = []
                    current_token_count = 0
                    current_chunk_endpoints = []
            
            # 添加当前端点
            current_chunk_content.append(endpoint_content)
            current_token_count += endpoint_token_count
            current_chunk_endpoints.append(endpoint.endpoint_id)
        
        # 添加最后一个分块
        if current_chunk_content:
            chunk = DocumentChunk(
                chunk_id=f"chunk_{len(chunks) + 1}",
                content="\n\n".join(current_chunk_content),
                chunk_type="endpoint_group",
                token_count=current_token_count,
                endpoints=current_chunk_endpoints,
                metadata={
                    "endpoint_count": len(current_chunk_endpoints),
                    "chunk_index": len(chunks)
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_by_size(self, analysis_result: DocumentAnalysisResult, 
                      strategy: ChunkingStrategy) -> List[DocumentChunk]:
        """按内容大小分块"""
        chunks = []
        
        # 将所有内容合并
        full_content = self._format_full_document(analysis_result)
        
        # 按段落分割
        paragraphs = full_content.split('\n\n')
        
        current_chunk_content = []
        current_token_count = 0
        
        for paragraph in paragraphs:
            paragraph_tokens = self._estimate_token_count(paragraph)
            
            # 检查是否需要创建新分块
            if (current_token_count + paragraph_tokens > strategy.max_tokens and 
                current_chunk_content):
                
                # 创建当前分块
                chunk = DocumentChunk(
                    chunk_id=f"chunk_{len(chunks) + 1}",
                    content="\n\n".join(current_chunk_content),
                    chunk_type="content_block",
                    token_count=current_token_count,
                    metadata={
                        "paragraph_count": len(current_chunk_content),
                        "chunk_index": len(chunks)
                    }
                )
                chunks.append(chunk)
                
                # 重置当前分块
                current_chunk_content = []
                current_token_count = 0
            
            # 添加当前段落
            current_chunk_content.append(paragraph)
            current_token_count += paragraph_tokens
        
        # 添加最后一个分块
        if current_chunk_content:
            chunk = DocumentChunk(
                chunk_id=f"chunk_{len(chunks) + 1}",
                content="\n\n".join(current_chunk_content),
                chunk_type="content_block",
                token_count=current_token_count,
                metadata={
                    "paragraph_count": len(current_chunk_content),
                    "chunk_index": len(chunks)
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _format_basic_info(self, analysis_result: DocumentAnalysisResult) -> str:
        """格式化基本信息"""
        content = []
        
        if analysis_result.title:
            content.append(f"# {analysis_result.title}")
        
        if analysis_result.version:
            content.append(f"**版本**: {analysis_result.version}")
        
        if analysis_result.description:
            content.append(f"**描述**: {analysis_result.description}")
        
        if analysis_result.base_url:
            content.append(f"**基础URL**: {analysis_result.base_url}")
        
        return "\n\n".join(content)
    
    def _format_endpoint(self, endpoint: APIEndpoint) -> str:
        """格式化端点信息"""
        content = []
        
        # 端点标题
        content.append(f"## {endpoint.method} {endpoint.path}")
        
        # 摘要和描述
        if endpoint.summary:
            content.append(f"**摘要**: {endpoint.summary}")
        
        if endpoint.description:
            content.append(f"**描述**: {endpoint.description}")
        
        # 标签
        if endpoint.tags:
            content.append(f"**标签**: {', '.join(endpoint.tags)}")
        
        # 参数
        if endpoint.parameters:
            content.append("**参数**:")
            for param in endpoint.parameters:
                if isinstance(param, dict):
                    name = param.get("name", "")
                    param_type = param.get("type", param.get("schema", {}).get("type", ""))
                    required = param.get("required", False)
                    description = param.get("description", "")
                    
                    param_info = f"- `{name}` ({param_type})"
                    if required:
                        param_info += " *必需*"
                    if description:
                        param_info += f": {description}"
                    
                    content.append(param_info)
        
        # 响应
        if endpoint.responses:
            content.append("**响应**:")
            for status_code, response in endpoint.responses.items():
                if isinstance(response, dict):
                    description = response.get("description", "")
                    content.append(f"- `{status_code}`: {description}")
        
        return "\n\n".join(content)
    
    def _format_full_document(self, analysis_result: DocumentAnalysisResult) -> str:
        """格式化完整文档"""
        content = []
        
        # 基本信息
        content.append(self._format_basic_info(analysis_result))
        
        # 端点信息
        for endpoint in analysis_result.endpoints:
            content.append(self._format_endpoint(endpoint))
        
        return "\n\n".join(content)
    
    def _estimate_token_count(self, text: str) -> int:
        """估算Token数量
        
        简单的Token估算：大约4个字符=1个Token
        """
        return len(text) // 4
