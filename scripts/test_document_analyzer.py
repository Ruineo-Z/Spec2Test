#!/usr/bin/env python3
"""
文档分析器集成测试脚本

测试文档分析器的功能和集成。
"""

import sys
import json
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.shared.utils.logger import get_logger
from app.core.document_analyzer import (
    DocumentAnalyzer, DocumentParser, DocumentValidator, DocumentChunker,
    DocumentType, DocumentFormat, ChunkingStrategy
)

logger = get_logger(__name__)


def test_analyzer_imports():
    """测试文档分析器模块导入"""
    logger.info("测试文档分析器模块导入...")
    
    try:
        from app.core.document_analyzer import (
            DocumentAnalyzer, DocumentParser, DocumentValidator, DocumentChunker,
            DocumentType, DocumentFormat, QualityLevel, IssueType, IssueSeverity,
            DocumentAnalysisResult, ChunkingStrategy
        )
        logger.info("✅ 文档分析器模块导入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ 文档分析器模块导入失败: {e}")
        return False


def test_document_parser():
    """测试文档解析器"""
    logger.info("测试文档解析器...")
    
    try:
        parser = DocumentParser()
        
        # 测试JSON格式解析
        json_content = '''
        {
            "openapi": "3.0.0",
            "info": {
                "title": "测试API",
                "version": "1.0.0",
                "description": "这是一个测试API"
            },
            "paths": {
                "/users": {
                    "get": {
                        "summary": "获取用户列表",
                        "responses": {
                            "200": {
                                "description": "成功"
                            }
                        }
                    }
                }
            }
        }
        '''
        
        parsed_doc = parser.parse_document(json_content)
        assert parsed_doc.is_valid, f"解析失败: {parsed_doc.parse_errors}"
        assert parsed_doc.document_type == DocumentType.OPENAPI_JSON
        logger.info("✅ JSON格式解析成功")
        
        # 测试API信息提取
        analysis_result = parser.extract_api_info(parsed_doc)
        assert analysis_result.title == "测试API"
        assert analysis_result.version == "1.0.0"
        assert len(analysis_result.endpoints) == 1
        logger.info("✅ API信息提取成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 文档解析器测试失败: {e}")
        return False


def test_document_validator():
    """测试文档验证器"""
    logger.info("测试文档验证器...")
    
    try:
        from app.core.document_analyzer.models import DocumentAnalysisResult, APIEndpoint
        
        validator = DocumentValidator()
        
        # 创建测试分析结果
        result = DocumentAnalysisResult(
            document_type=DocumentType.OPENAPI_JSON,
            document_format=DocumentFormat.JSON,
            title="测试API",
            version="1.0.0"
        )
        
        # 添加一个端点
        endpoint = APIEndpoint(
            path="/users",
            method="GET",
            summary="获取用户",
            responses={"200": {"description": "成功"}}
        )
        result.endpoints = [endpoint]
        result.total_endpoints = 1
        
        # 执行验证
        validated_result = validator.validate_document(result)
        
        assert validated_result.quality_metrics is not None
        logger.info(f"✅ 文档验证成功: 质量评分 {validated_result.quality_metrics.overall_score:.1f}")
        logger.info(f"   发现问题: {len(validated_result.issues)}个")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 文档验证器测试失败: {e}")
        return False


def test_document_chunker():
    """测试文档分块器"""
    logger.info("测试文档分块器...")
    
    try:
        from app.core.document_analyzer.models import DocumentAnalysisResult, APIEndpoint
        
        chunker = DocumentChunker()
        
        # 创建测试分析结果
        result = DocumentAnalysisResult(
            document_type=DocumentType.OPENAPI_JSON,
            document_format=DocumentFormat.JSON,
            title="测试API",
            version="1.0.0"
        )
        
        # 添加多个端点
        for i in range(5):
            endpoint = APIEndpoint(
                path=f"/users/{i}",
                method="GET",
                summary=f"获取用户{i}",
                description=f"这是获取用户{i}的详细描述，包含更多信息以增加内容长度。",
                responses={"200": {"description": "成功"}}
            )
            result.endpoints.append(endpoint)
        
        result.total_endpoints = len(result.endpoints)
        
        # 创建分块策略
        strategy = ChunkingStrategy(
            max_tokens=1000,
            overlap_tokens=100,
            chunk_by_endpoint=True
        )
        
        # 执行分块
        chunked_result = chunker.chunk_document(result, strategy)
        
        assert len(chunked_result.chunks) > 0
        logger.info(f"✅ 文档分块成功: {len(chunked_result.chunks)}个分块")
        
        for i, chunk in enumerate(chunked_result.chunks):
            logger.info(f"   分块{i+1}: {chunk.token_count} tokens, {len(chunk.endpoints)} endpoints")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 文档分块器测试失败: {e}")
        return False


def test_document_analyzer():
    """测试文档分析器主类"""
    logger.info("测试文档分析器主类...")
    
    try:
        # 创建分析器
        analyzer = DocumentAnalyzer(config={
            "enable_validation": True,
            "enable_chunking": True,
            "max_tokens": 2000
        })
        
        # 测试内容
        openapi_content = '''
        {
            "openapi": "3.0.0",
            "info": {
                "title": "用户管理API",
                "version": "2.0.0",
                "description": "提供用户管理相关的API接口"
            },
            "servers": [
                {
                    "url": "https://api.example.com/v2"
                }
            ],
            "paths": {
                "/users": {
                    "get": {
                        "summary": "获取用户列表",
                        "description": "分页获取用户列表",
                        "tags": ["用户管理"],
                        "parameters": [
                            {
                                "name": "page",
                                "in": "query",
                                "description": "页码",
                                "schema": {"type": "integer", "default": 1}
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "成功返回用户列表"
                            }
                        }
                    },
                    "post": {
                        "summary": "创建用户",
                        "tags": ["用户管理"],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "email": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {
                                "description": "用户创建成功"
                            }
                        }
                    }
                }
            }
        }
        '''
        
        # 执行分析
        result = analyzer.analyze_content(openapi_content, "test_api.json")
        
        # 验证结果
        assert result.title == "用户管理API"
        assert result.version == "2.0.0"
        assert result.base_url == "https://api.example.com/v2"
        assert result.total_endpoints == 2
        assert result.quality_metrics is not None
        assert len(result.chunks) > 0
        
        logger.info(f"✅ 文档分析成功:")
        logger.info(f"   标题: {result.title}")
        logger.info(f"   版本: {result.version}")
        logger.info(f"   端点数: {result.total_endpoints}")
        logger.info(f"   质量评分: {result.quality_metrics.overall_score:.1f}")
        logger.info(f"   分块数: {len(result.chunks)}")
        logger.info(f"   问题数: {len(result.issues)}")
        logger.info(f"   分析耗时: {result.analysis_duration:.3f}秒")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 文档分析器测试失败: {e}")
        return False


def test_analysis_summary():
    """测试分析摘要"""
    logger.info("测试分析摘要...")
    
    try:
        analyzer = DocumentAnalyzer()
        
        # 简单的测试内容
        content = '''
        {
            "openapi": "3.0.0",
            "info": {
                "title": "简单API",
                "version": "1.0.0"
            },
            "paths": {
                "/test": {
                    "get": {
                        "summary": "测试端点",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        }
        '''
        
        result = analyzer.analyze_content(content)
        summary = analyzer.get_analysis_summary(result)
        
        assert "document_info" in summary
        assert "api_info" in summary
        assert "quality_info" in summary
        assert "analysis_info" in summary
        
        logger.info("✅ 分析摘要生成成功:")
        logger.info(f"   文档类型: {summary['document_info']['type']}")
        logger.info(f"   端点总数: {summary['api_info']['total_endpoints']}")
        logger.info(f"   质量评分: {summary['quality_info']['overall_score']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 分析摘要测试失败: {e}")
        return False


def test_file_analysis():
    """测试文件分析"""
    logger.info("测试文件分析...")
    
    try:
        # 创建临时文件
        test_content = '''
        {
            "openapi": "3.0.0",
            "info": {
                "title": "文件测试API",
                "version": "1.0.0"
            },
            "paths": {
                "/file-test": {
                    "get": {
                        "summary": "文件测试端点",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        }
        '''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(test_content)
            temp_file = f.name
        
        try:
            analyzer = DocumentAnalyzer()
            result = analyzer.analyze_file(temp_file)
            
            assert result.title == "文件测试API"
            assert result.total_endpoints == 1
            
            logger.info("✅ 文件分析成功")
            
        finally:
            # 清理临时文件
            Path(temp_file).unlink()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 文件分析测试失败: {e}")
        return False


def test_export_report():
    """测试报告导出"""
    logger.info("测试报告导出...")
    
    try:
        analyzer = DocumentAnalyzer()
        
        content = '''
        {
            "openapi": "3.0.0",
            "info": {
                "title": "导出测试API",
                "version": "1.0.0"
            },
            "paths": {
                "/export": {
                    "get": {
                        "summary": "导出测试",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        }
        '''
        
        result = analyzer.analyze_content(content)
        
        # 测试JSON导出
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            json_file = f.name
        
        try:
            success = analyzer.export_analysis_report(result, json_file, "json")
            assert success, "JSON导出失败"
            
            # 验证文件存在且有内容
            assert Path(json_file).exists()
            assert Path(json_file).stat().st_size > 0
            
            logger.info("✅ JSON报告导出成功")
            
        finally:
            Path(json_file).unlink()
        
        # 测试Markdown导出
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
            md_file = f.name
        
        try:
            success = analyzer.export_analysis_report(result, md_file, "markdown")
            assert success, "Markdown导出失败"
            
            # 验证文件存在且有内容
            assert Path(md_file).exists()
            assert Path(md_file).stat().st_size > 0
            
            logger.info("✅ Markdown报告导出成功")
            
        finally:
            Path(md_file).unlink()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 报告导出测试失败: {e}")
        return False


def main():
    """主函数"""
    try:
        logger.info("🚀 开始文档分析器集成测试...")
        
        tests = [
            ("文档分析器模块导入", test_analyzer_imports),
            ("文档解析器", test_document_parser),
            ("文档验证器", test_document_validator),
            ("文档分块器", test_document_chunker),
            ("文档分析器主类", test_document_analyzer),
            ("分析摘要", test_analysis_summary),
            ("文件分析", test_file_analysis),
            ("报告导出", test_export_report),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n--- 测试: {test_name} ---")
            try:
                if test_func():
                    passed += 1
                    logger.info(f"✅ {test_name} 通过")
                else:
                    logger.error(f"❌ {test_name} 失败")
            except Exception as e:
                logger.error(f"💥 {test_name} 异常: {e}")
        
        logger.info(f"\n🎯 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            logger.info("🎉 所有文档分析器测试通过！")
        else:
            logger.warning(f"⚠️ {total - passed} 个测试失败")
            
        return passed == total
        
    except Exception as e:
        logger.error(f"💥 文档分析器测试失败: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
