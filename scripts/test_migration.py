#!/usr/bin/env python3
"""
数据库迁移测试脚本

使用SQLite测试数据库迁移功能，验证表结构创建。
"""

import sys
import tempfile
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.base import BaseModel
from app.models import Document, TestCase, TestResult, Report
from app.models import DocumentType, DocumentStatus, TestCaseType, HTTPMethod, TestStatus, ReportType
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


def test_database_migration():
    """测试数据库迁移功能"""
    logger.info("开始测试数据库迁移...")
    
    # 创建临时SQLite数据库
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    try:
        db_url = f"sqlite:///{temp_file.name}"
        engine = create_engine(db_url, echo=True)
        
        # 创建所有表（模拟迁移）
        logger.info("创建数据库表结构...")
        BaseModel.metadata.create_all(engine)
        logger.info("✅ 数据库表创建成功")
        
        # 验证表是否创建
        with engine.connect() as conn:
            # 检查表是否存在
            tables_query = text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            
            result = conn.execute(tables_query)
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = ['documents', 'test_cases', 'test_results', 'reports']
            
            logger.info(f"发现的表: {tables}")
            
            for table in expected_tables:
                if table in tables:
                    logger.info(f"✅ 表 {table} 创建成功")
                else:
                    logger.error(f"❌ 表 {table} 创建失败")
                    return False
        
        # 测试数据操作
        logger.info("测试数据库操作...")
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # 创建测试数据
            document = Document(
                name="测试API文档",
                description="迁移测试文档",
                document_type=DocumentType.OPENAPI,
                status=DocumentStatus.UPLOADED
            )
            session.add(document)
            session.commit()
            logger.info(f"✅ 文档创建成功: ID={document.id}")
            
            # 创建测试用例
            test_case = TestCase(
                document_id=document.id,
                name="迁移测试用例",
                endpoint_path="/api/test",
                http_method=HTTPMethod.GET,
                test_type=TestCaseType.NORMAL,
                expected_status_code=200
            )
            session.add(test_case)
            session.commit()
            logger.info(f"✅ 测试用例创建成功: ID={test_case.id}")
            
            # 创建测试结果
            test_result = TestResult(
                test_case_id=test_case.id,
                status=TestStatus.PASSED,
                response_status_code=200,
                response_time=0.5
            )
            session.add(test_result)
            session.commit()
            logger.info(f"✅ 测试结果创建成功: ID={test_result.id}")
            
            # 创建报告
            report = Report(
                document_id=document.id,
                name="迁移测试报告",
                report_type=ReportType.EXECUTION_SUMMARY,
                total_test_cases=1,
                passed_count=1
            )
            session.add(report)
            session.commit()
            logger.info(f"✅ 报告创建成功: ID={report.id}")
            
            # 测试关系查询
            doc_test_cases = document.test_cases.count()
            doc_reports = document.reports.count()
            case_results = test_case.test_results.count()
            
            logger.info(f"✅ 关系查询测试:")
            logger.info(f"  - 文档关联测试用例数: {doc_test_cases}")
            logger.info(f"  - 文档关联报告数: {doc_reports}")
            logger.info(f"  - 测试用例关联结果数: {case_results}")
            
            # 测试模型方法
            logger.info(f"✅ 模型方法测试:")
            logger.info(f"  - 文档是否已解析: {document.is_parsed()}")
            logger.info(f"  - 测试用例完整URL: {test_case.get_full_url('https://api.example.com')}")
            logger.info(f"  - 测试结果是否成功: {test_result.is_successful()}")
            logger.info(f"  - 报告成功率: {report.get_success_rate()}%")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 数据操作测试失败: {e}")
            return False
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"❌ 数据库迁移测试失败: {e}")
        return False
    finally:
        # 清理临时文件
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


def test_table_structure():
    """测试表结构"""
    logger.info("开始测试表结构...")
    
    # 创建临时SQLite数据库
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    try:
        db_url = f"sqlite:///{temp_file.name}"
        engine = create_engine(db_url)
        
        # 创建表
        BaseModel.metadata.create_all(engine)
        
        with engine.connect() as conn:
            # 检查documents表结构
            result = conn.execute(text("PRAGMA table_info(documents)"))
            columns = {row[1]: row[2] for row in result.fetchall()}
            
            expected_columns = {
                'id': 'INTEGER',
                'name': 'VARCHAR(255)',
                'description': 'TEXT',
                'document_type': 'VARCHAR(8)',
                'status': 'VARCHAR(13)',
                'created_at': 'DATETIME',
                'updated_at': 'DATETIME',
                'is_deleted': 'BOOLEAN'
            }
            
            logger.info("documents表结构验证:")
            for col_name, col_type in expected_columns.items():
                if col_name in columns:
                    logger.info(f"✅ 字段 {col_name}: {columns[col_name]}")
                else:
                    logger.error(f"❌ 缺少字段 {col_name}")
            
            # 检查外键约束
            result = conn.execute(text("PRAGMA foreign_key_list(test_cases)"))
            foreign_keys = list(result.fetchall())
            
            if foreign_keys:
                logger.info(f"✅ test_cases表外键约束: {len(foreign_keys)}个")
            else:
                logger.warning("⚠️ test_cases表未发现外键约束")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 表结构测试失败: {e}")
        return False
    finally:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


def main():
    """主函数"""
    try:
        logger.info("🚀 开始数据库迁移测试...")
        
        # 测试数据库迁移
        if not test_database_migration():
            sys.exit(1)
        
        # 测试表结构
        if not test_table_structure():
            sys.exit(1)
        
        logger.info("🎉 数据库迁移测试全部通过！")
        
    except Exception as e:
        logger.error(f"💥 数据库迁移测试失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
