#!/usr/bin/env python3
"""
数据模型测试脚本

测试核心数据模型的定义和关系是否正确。
使用SQLite内存数据库进行测试。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import (
    BaseModel, Document, TestCase, TestResult, Report,
    DocumentType, DocumentStatus, TestCaseType, HTTPMethod, TestStatus, ReportType
)
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


def test_model_definitions():
    """测试模型定义"""
    logger.info("开始测试模型定义...")
    
    # 创建内存SQLite数据库
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # 创建所有表
    BaseModel.metadata.create_all(engine)
    logger.info("✅ 数据表创建成功")
    
    # 检查表是否创建
    tables = BaseModel.metadata.tables.keys()
    expected_tables = {'documents', 'test_cases', 'test_results', 'reports'}
    
    for table in expected_tables:
        if table in tables:
            logger.info(f"✅ 表 {table} 创建成功")
        else:
            logger.error(f"❌ 表 {table} 创建失败")
            return False
    
    return True


def test_model_relationships():
    """测试模型关系"""
    logger.info("开始测试模型关系...")
    
    # 创建内存SQLite数据库
    engine = create_engine("sqlite:///:memory:", echo=False)
    BaseModel.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 创建文档
        document = Document(
            name="测试API文档",
            description="这是一个测试文档",
            document_type=DocumentType.OPENAPI,
            status=DocumentStatus.UPLOADED
        )
        session.add(document)
        session.commit()
        logger.info(f"✅ 文档创建成功: {document}")
        
        # 创建测试用例
        test_case = TestCase(
            document_id=document.id,
            name="测试用例1",
            description="这是一个测试用例",
            test_type=TestCaseType.NORMAL,
            endpoint_path="/api/users",
            http_method=HTTPMethod.GET,
            expected_status_code=200
        )
        session.add(test_case)
        session.commit()
        logger.info(f"✅ 测试用例创建成功: {test_case}")
        
        # 创建测试结果
        test_result = TestResult(
            test_case_id=test_case.id,
            status=TestStatus.PASSED,
            response_status_code=200,
            response_time=0.5
        )
        session.add(test_result)
        session.commit()
        logger.info(f"✅ 测试结果创建成功: {test_result}")
        
        # 创建报告
        report = Report(
            document_id=document.id,
            name="测试报告1",
            description="这是一个测试报告",
            report_type=ReportType.EXECUTION_SUMMARY,
            total_test_cases=1,
            passed_count=1,
            failed_count=0
        )
        session.add(report)
        session.commit()
        logger.info(f"✅ 报告创建成功: {report}")
        
        # 测试关系查询
        # 文档 -> 测试用例
        doc_test_cases = document.test_cases.all()
        logger.info(f"✅ 文档关联的测试用例数量: {len(doc_test_cases)}")
        
        # 文档 -> 报告
        doc_reports = document.reports.all()
        logger.info(f"✅ 文档关联的报告数量: {len(doc_reports)}")
        
        # 测试用例 -> 测试结果
        case_results = test_case.test_results.all()
        logger.info(f"✅ 测试用例关联的结果数量: {len(case_results)}")
        
        # 反向关系
        logger.info(f"✅ 测试用例关联的文档: {test_case.document.name}")
        logger.info(f"✅ 测试结果关联的测试用例: {test_result.test_case.name}")
        logger.info(f"✅ 报告关联的文档: {report.document.name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 模型关系测试失败: {e}")
        return False
    finally:
        session.close()


def test_model_methods():
    """测试模型方法"""
    logger.info("开始测试模型方法...")
    
    # 创建内存SQLite数据库
    engine = create_engine("sqlite:///:memory:", echo=False)
    BaseModel.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 测试Document方法
        document = Document(
            name="测试文档",
            document_type=DocumentType.OPENAPI,
            status=DocumentStatus.PARSED
        )
        session.add(document)
        session.commit()
        
        assert document.is_parsed() == True
        assert document.is_valid() == False
        assert document.has_errors() == False
        logger.info("✅ Document方法测试通过")
        
        # 测试TestCase方法
        test_case = TestCase(
            document_id=document.id,
            name="测试用例",
            endpoint_path="/api/test",
            http_method=HTTPMethod.POST,
            test_type=TestCaseType.PERFORMANCE,
            max_response_time=2.0
        )
        session.add(test_case)
        session.commit()
        
        full_url = test_case.get_full_url("https://api.example.com")
        assert full_url == "https://api.example.com/api/test"
        assert test_case.is_performance_test() == True
        logger.info("✅ TestCase方法测试通过")
        
        # 测试TestResult方法
        test_result = TestResult(
            test_case_id=test_case.id,
            status=TestStatus.PASSED,
            response_time=1.5,
            assertions_passed=5,
            assertions_failed=0
        )
        session.add(test_result)
        session.commit()
        
        assert test_result.is_successful() == True
        assert test_result.is_failed() == False
        
        perf_summary = test_result.get_performance_summary()
        assert perf_summary['response_time'] == 1.5
        logger.info("✅ TestResult方法测试通过")
        
        # 测试Report方法
        report = Report(
            document_id=document.id,
            name="测试报告",
            report_type=ReportType.PERFORMANCE_REPORT,
            total_test_cases=10,
            passed_count=8,
            failed_count=2
        )
        session.add(report)
        session.commit()
        
        success_rate = report.get_success_rate()
        assert success_rate == 80.0
        assert report.has_failures() == True
        logger.info("✅ Report方法测试通过")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 模型方法测试失败: {e}")
        return False
    finally:
        session.close()


def main():
    """主函数"""
    try:
        logger.info("🚀 开始核心数据模型测试...")
        
        # 测试模型定义
        if not test_model_definitions():
            sys.exit(1)
        
        # 测试模型关系
        if not test_model_relationships():
            sys.exit(1)
        
        # 测试模型方法
        if not test_model_methods():
            sys.exit(1)
        
        logger.info("🎉 所有核心数据模型测试通过！")
        
    except Exception as e:
        logger.error(f"💥 核心数据模型测试失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
