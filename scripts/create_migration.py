#!/usr/bin/env python3
"""
创建Alembic迁移文件脚本

生成初始数据库迁移文件，用于创建核心数据表。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


def create_initial_migration():
    """创建初始迁移文件"""
    logger.info("开始创建初始数据库迁移文件...")

    try:
        # 确保所有模型都被导入
        from app.models import Document, TestCase, TestResult, Report
        logger.info("✅ 所有模型导入成功")

        # 创建迁移文件内容
        migration_content = '''"""创建核心数据模型

Revision ID: 001_initial_tables
Revises:
Create Date: 2025-01-15 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建所有核心数据表"""

    # 创建documents表
    op.create_table('documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False, comment='文档名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='文档描述'),
        sa.Column('document_type', sa.String(length=8), nullable=False, comment='文档类型'),
        sa.Column('status', sa.String(length=12), nullable=False, comment='文档状态'),
        sa.Column('original_filename', sa.String(length=255), nullable=True, comment='原始文件名'),
        sa.Column('file_path', sa.String(length=500), nullable=True, comment='文件存储路径'),
        sa.Column('file_size', sa.Integer(), nullable=True, comment='文件大小（字节）'),
        sa.Column('file_hash', sa.String(length=64), nullable=True, comment='文件SHA256哈希值'),
        sa.Column('content', sa.Text(), nullable=True, comment='文档原始内容'),
        sa.Column('parsed_data', sa.JSON(), nullable=True, comment='解析后的结构化数据'),
        sa.Column('doc_metadata', sa.JSON(), nullable=True, comment='文档元数据'),
        sa.Column('api_version', sa.String(length=50), nullable=True, comment='API版本'),
        sa.Column('base_url', sa.String(length=500), nullable=True, comment='API基础URL'),
        sa.Column('endpoints_count', sa.Integer(), nullable=True, comment='API端点数量'),
        sa.Column('parse_error', sa.Text(), nullable=True, comment='解析错误信息'),
        sa.Column('validation_errors', sa.JSON(), nullable=True, comment='验证错误详情'),
        sa.Column('parsed_at', sa.DateTime(), nullable=True, comment='解析完成时间'),
        sa.Column('validated_at', sa.DateTime(), nullable=True, comment='验证完成时间'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='更新时间'),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False, comment='软删除标记'),
        sa.PrimaryKeyConstraint('id'),
        comment='API文档表'
    )
    
    # 创建test_cases表
    op.create_table('test_cases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False, comment='关联文档ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='测试用例名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='测试用例描述'),
        sa.Column('test_type', sa.Enum('NORMAL', 'BOUNDARY', 'EXCEPTION', 'SECURITY', 'PERFORMANCE', name='testcasetype'), nullable=False, comment='测试用例类型'),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='testcasepriority'), nullable=False, comment='测试优先级'),
        sa.Column('endpoint_path', sa.String(length=500), nullable=False, comment='API端点路径'),
        sa.Column('http_method', sa.Enum('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', name='httpmethod'), nullable=False, comment='HTTP请求方法'),
        sa.Column('request_headers', sa.JSON(), nullable=True, comment='请求头参数'),
        sa.Column('request_params', sa.JSON(), nullable=True, comment='查询参数'),
        sa.Column('request_body', sa.JSON(), nullable=True, comment='请求体数据'),
        sa.Column('path_variables', sa.JSON(), nullable=True, comment='路径变量'),
        sa.Column('auth_type', sa.String(length=50), nullable=True, comment='认证类型'),
        sa.Column('auth_data', sa.JSON(), nullable=True, comment='认证数据'),
        sa.Column('expected_status_code', sa.Integer(), nullable=True, comment='期望HTTP状态码'),
        sa.Column('expected_response_headers', sa.JSON(), nullable=True, comment='期望响应头'),
        sa.Column('expected_response_body', sa.JSON(), nullable=True, comment='期望响应体'),
        sa.Column('expected_response_schema', sa.JSON(), nullable=True, comment='期望响应Schema'),
        sa.Column('validation_rules', sa.JSON(), nullable=True, comment='自定义验证规则'),
        sa.Column('max_response_time', sa.Float(), nullable=True, comment='最大响应时间（秒）'),
        sa.Column('tags', sa.JSON(), nullable=True, comment='测试标签'),
        sa.Column('test_group', sa.String(length=100), nullable=True, comment='测试分组'),
        sa.Column('depends_on', sa.JSON(), nullable=True, comment='依赖的测试用例ID列表'),
        sa.Column('retry_count', sa.Integer(), nullable=False, comment='重试次数'),
        sa.Column('timeout', sa.Float(), nullable=True, comment='超时时间（秒）'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, comment='是否启用此测试用例'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False, comment='软删除标记'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='API测试用例表'
    )
    
    # 创建test_results表
    op.create_table('test_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('test_case_id', sa.Integer(), nullable=False, comment='关联测试用例ID'),
        sa.Column('execution_id', sa.String(length=100), nullable=True, comment='执行批次ID'),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'PASSED', 'FAILED', 'ERROR', 'SKIPPED', 'TIMEOUT', name='teststatus'), nullable=False, comment='测试状态'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, comment='开始执行时间'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='完成执行时间'),
        sa.Column('actual_request_url', sa.String(length=1000), nullable=True, comment='实际请求URL'),
        sa.Column('actual_request_headers', sa.JSON(), nullable=True, comment='实际请求头'),
        sa.Column('actual_request_body', sa.JSON(), nullable=True, comment='实际请求体'),
        sa.Column('response_status_code', sa.Integer(), nullable=True, comment='响应状态码'),
        sa.Column('response_headers', sa.JSON(), nullable=True, comment='响应头'),
        sa.Column('response_body', sa.JSON(), nullable=True, comment='响应体'),
        sa.Column('response_size', sa.Integer(), nullable=True, comment='响应大小（字节）'),
        sa.Column('response_time', sa.Float(), nullable=True, comment='响应时间（秒）'),
        sa.Column('dns_lookup_time', sa.Float(), nullable=True, comment='DNS查询时间（秒）'),
        sa.Column('tcp_connect_time', sa.Float(), nullable=True, comment='TCP连接时间（秒）'),
        sa.Column('ssl_handshake_time', sa.Float(), nullable=True, comment='SSL握手时间（秒）'),
        sa.Column('first_byte_time', sa.Float(), nullable=True, comment='首字节时间（秒）'),
        sa.Column('validation_results', sa.JSON(), nullable=True, comment='验证结果详情'),
        sa.Column('assertions_passed', sa.Integer(), nullable=True, comment='通过的断言数量'),
        sa.Column('assertions_failed', sa.Integer(), nullable=True, comment='失败的断言数量'),
        sa.Column('failure_type', sa.Enum('STATUS_CODE_MISMATCH', 'RESPONSE_BODY_MISMATCH', 'RESPONSE_SCHEMA_ERROR', 'TIMEOUT_ERROR', 'CONNECTION_ERROR', 'AUTHENTICATION_ERROR', 'VALIDATION_ERROR', 'UNKNOWN_ERROR', name='failuretype'), nullable=True, comment='失败类型'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误消息'),
        sa.Column('error_details', sa.JSON(), nullable=True, comment='错误详情'),
        sa.Column('stack_trace', sa.Text(), nullable=True, comment='错误堆栈'),
        sa.Column('retry_count', sa.Integer(), nullable=False, comment='重试次数'),
        sa.Column('is_retry', sa.Boolean(), nullable=False, comment='是否为重试执行'),
        sa.Column('environment', sa.String(length=50), nullable=True, comment='执行环境'),
        sa.Column('user_agent', sa.String(length=500), nullable=True, comment='用户代理'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False, comment='软删除标记'),
        sa.ForeignKeyConstraint(['test_case_id'], ['test_cases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='API测试结果表'
    )
    
    # 创建reports表
    op.create_table('reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False, comment='关联文档ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='报告名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='报告描述'),
        sa.Column('report_type', sa.Enum('EXECUTION_SUMMARY', 'DETAILED_ANALYSIS', 'PERFORMANCE_REPORT', 'FAILURE_ANALYSIS', 'COVERAGE_REPORT', 'TREND_ANALYSIS', name='reporttype'), nullable=False, comment='报告类型'),
        sa.Column('status', sa.Enum('GENERATING', 'COMPLETED', 'FAILED', 'ARCHIVED', name='reportstatus'), nullable=False, comment='报告状态'),
        sa.Column('format', sa.Enum('HTML', 'PDF', 'JSON', 'EXCEL', 'CSV', name='reportformat'), nullable=False, comment='报告格式'),
        sa.Column('execution_id', sa.String(length=100), nullable=True, comment='关联的执行批次ID'),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True, comment='报告生成时间'),
        sa.Column('total_test_cases', sa.Integer(), nullable=False, comment='总测试用例数'),
        sa.Column('passed_count', sa.Integer(), nullable=False, comment='通过的测试数量'),
        sa.Column('failed_count', sa.Integer(), nullable=False, comment='失败的测试数量'),
        sa.Column('error_count', sa.Integer(), nullable=False, comment='错误的测试数量'),
        sa.Column('skipped_count', sa.Integer(), nullable=False, comment='跳过的测试数量'),
        sa.Column('total_execution_time', sa.Float(), nullable=True, comment='总执行时间（秒）'),
        sa.Column('average_response_time', sa.Float(), nullable=True, comment='平均响应时间（秒）'),
        sa.Column('min_response_time', sa.Float(), nullable=True, comment='最小响应时间（秒）'),
        sa.Column('max_response_time', sa.Float(), nullable=True, comment='最大响应时间（秒）'),
        sa.Column('endpoint_coverage', sa.Float(), nullable=True, comment='端点覆盖率（百分比）'),
        sa.Column('method_coverage', sa.Float(), nullable=True, comment='HTTP方法覆盖率（百分比）'),
        sa.Column('status_code_coverage', sa.Float(), nullable=True, comment='状态码覆盖率（百分比）'),
        sa.Column('test_results_summary', sa.JSON(), nullable=True, comment='测试结果摘要'),
        sa.Column('performance_metrics', sa.JSON(), nullable=True, comment='性能指标详情'),
        sa.Column('failure_analysis', sa.JSON(), nullable=True, comment='失败分析数据'),
        sa.Column('coverage_details', sa.JSON(), nullable=True, comment='覆盖率详情'),
        sa.Column('charts_data', sa.JSON(), nullable=True, comment='图表数据'),
        sa.Column('recommendations', sa.JSON(), nullable=True, comment='改进建议'),
        sa.Column('issues_found', sa.JSON(), nullable=True, comment='发现的问题'),
        sa.Column('file_path', sa.String(length=500), nullable=True, comment='报告文件路径'),
        sa.Column('file_size', sa.Integer(), nullable=True, comment='报告文件大小（字节）'),
        sa.Column('generation_config', sa.JSON(), nullable=True, comment='报告生成配置'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False, comment='软删除标记'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='测试报告表'
    )
    
    # 创建索引
    op.create_index('idx_documents_type_status', 'documents', ['document_type', 'status'])
    op.create_index('idx_test_cases_document_id', 'test_cases', ['document_id'])
    op.create_index('idx_test_cases_type_priority', 'test_cases', ['test_type', 'priority'])
    op.create_index('idx_test_results_test_case_id', 'test_results', ['test_case_id'])
    op.create_index('idx_test_results_execution_id', 'test_results', ['execution_id'])
    op.create_index('idx_test_results_status', 'test_results', ['status'])
    op.create_index('idx_reports_document_id', 'reports', ['document_id'])
    op.create_index('idx_reports_type_status', 'reports', ['report_type', 'status'])


def downgrade() -> None:
    """删除所有核心数据表"""
    
    # 删除索引
    op.drop_index('idx_reports_type_status', table_name='reports')
    op.drop_index('idx_reports_document_id', table_name='reports')
    op.drop_index('idx_test_results_status', table_name='test_results')
    op.drop_index('idx_test_results_execution_id', table_name='test_results')
    op.drop_index('idx_test_results_test_case_id', table_name='test_results')
    op.drop_index('idx_test_cases_type_priority', table_name='test_cases')
    op.drop_index('idx_test_cases_document_id', table_name='test_cases')
    op.drop_index('idx_documents_type_status', table_name='documents')
    
    # 删除表
    op.drop_table('reports')
    op.drop_table('test_results')
    op.drop_table('test_cases')
    op.drop_table('documents')
    
    # 删除枚举类型
    op.execute('DROP TYPE IF EXISTS reportformat')
    op.execute('DROP TYPE IF EXISTS reportstatus')
    op.execute('DROP TYPE IF EXISTS reporttype')
    op.execute('DROP TYPE IF EXISTS failuretype')
    op.execute('DROP TYPE IF EXISTS teststatus')
    op.execute('DROP TYPE IF EXISTS httpmethod')
    op.execute('DROP TYPE IF EXISTS testcasepriority')
    op.execute('DROP TYPE IF EXISTS testcasetype')
    op.execute('DROP TYPE IF EXISTS documentstatus')
    op.execute('DROP TYPE IF EXISTS documenttype')
'''
        
        # 创建迁移文件目录
        migrations_dir = project_root / "alembic" / "versions"
        migrations_dir.mkdir(exist_ok=True)
        
        # 写入迁移文件
        migration_file = migrations_dir / "001_initial_tables.py"
        migration_file.write_text(migration_content, encoding='utf-8')
        
        logger.info(f"✅ 迁移文件创建成功: {migration_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 创建迁移文件失败: {e}")
        return False


def main():
    """主函数"""
    try:
        logger.info("🚀 开始创建数据库迁移文件...")
        
        if create_initial_migration():
            logger.info("🎉 数据库迁移文件创建成功！")
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 创建迁移文件失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
