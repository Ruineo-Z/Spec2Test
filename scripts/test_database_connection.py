#!/usr/bin/env python3
"""
数据库连接测试脚本

测试数据库连接和基本操作功能。
"""

import sys
import tempfile
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.database import DatabaseManager
from app.config import get_settings
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


def test_sqlite_connection():
    """测试SQLite连接"""
    logger.info("测试SQLite数据库连接...")
    
    # 创建临时SQLite数据库
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    try:
        db_url = f"sqlite:///{temp_file.name}"
        engine = create_engine(db_url)
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            
            if test_value == 1:
                logger.info("✅ SQLite数据库连接成功")
                return True
            else:
                logger.error("❌ SQLite数据库连接测试失败")
                return False
                
    except Exception as e:
        logger.error(f"❌ SQLite数据库连接失败: {e}")
        return False
    finally:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


def test_database_manager():
    """测试数据库管理器"""
    logger.info("测试数据库管理器...")
    
    try:
        # 创建数据库管理器实例
        db_manager = DatabaseManager()
        logger.info("✅ 数据库管理器创建成功")
        
        # 测试配置获取
        settings = get_settings()
        logger.info(f"✅ 数据库配置获取成功: {settings.database.url}")
        
        # 测试引擎创建
        engine = db_manager.engine
        logger.info("✅ 数据库引擎创建成功")

        # 测试会话工厂
        session_factory = db_manager.session_factory
        logger.info("✅ 会话工厂创建成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库管理器测试失败: {e}")
        return False


def test_alembic_configuration():
    """测试Alembic配置"""
    logger.info("测试Alembic配置...")
    
    try:
        # 检查alembic.ini文件
        alembic_ini = project_root / "alembic.ini"
        if not alembic_ini.exists():
            logger.error("❌ alembic.ini文件不存在")
            return False
        
        logger.info("✅ alembic.ini文件存在")
        
        # 检查alembic目录
        alembic_dir = project_root / "alembic"
        if not alembic_dir.exists():
            logger.error("❌ alembic目录不存在")
            return False
        
        logger.info("✅ alembic目录存在")
        
        # 检查env.py文件
        env_py = alembic_dir / "env.py"
        if not env_py.exists():
            logger.error("❌ alembic/env.py文件不存在")
            return False
        
        logger.info("✅ alembic/env.py文件存在")
        
        # 检查versions目录
        versions_dir = alembic_dir / "versions"
        if not versions_dir.exists():
            logger.error("❌ alembic/versions目录不存在")
            return False
        
        logger.info("✅ alembic/versions目录存在")
        
        # 检查迁移文件
        migration_files = list(versions_dir.glob("*.py"))
        if not migration_files:
            logger.warning("⚠️ 没有发现迁移文件")
        else:
            logger.info(f"✅ 发现迁移文件: {len(migration_files)}个")
            for migration_file in migration_files:
                logger.info(f"  - {migration_file.name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Alembic配置测试失败: {e}")
        return False


def test_model_imports():
    """测试模型导入"""
    logger.info("测试模型导入...")
    
    try:
        # 测试基础模型导入
        from app.models.base import BaseModel
        logger.info("✅ 基础模型导入成功")
        
        # 测试核心模型导入
        from app.models import Document, TestCase, TestResult, Report
        logger.info("✅ 核心模型导入成功")
        
        # 测试枚举导入
        from app.models import (
            DocumentType, DocumentStatus,
            TestCaseType, HTTPMethod, TestCasePriority,
            TestStatus, FailureType,
            ReportType, ReportStatus, ReportFormat
        )
        logger.info("✅ 枚举类型导入成功")
        
        # 检查metadata中的表
        tables = list(BaseModel.metadata.tables.keys())
        logger.info(f"✅ 发现数据表: {tables}")
        
        expected_tables = ['documents', 'test_cases', 'test_results', 'reports']
        for table in expected_tables:
            if table in tables:
                logger.info(f"✅ 表 {table} 已注册")
            else:
                logger.error(f"❌ 表 {table} 未注册")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 模型导入测试失败: {e}")
        return False


def test_configuration():
    """测试配置"""
    logger.info("测试应用配置...")
    
    try:
        # 测试配置获取
        settings = get_settings()
        logger.info("✅ 配置获取成功")
        
        # 测试数据库配置
        db_config = settings.database
        logger.info(f"✅ 数据库配置: {db_config.url}")
        
        # 测试应用配置
        logger.info(f"✅ 应用名称: {settings.app_name}")
        logger.info(f"✅ 调试模式: {settings.debug}")
        logger.info(f"✅ 环境: {settings.environment}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 配置测试失败: {e}")
        return False


def main():
    """主函数"""
    try:
        logger.info("🚀 开始数据库连接和配置测试...")
        
        # 测试配置
        if not test_configuration():
            sys.exit(1)
        
        # 测试模型导入
        if not test_model_imports():
            sys.exit(1)
        
        # 测试SQLite连接
        if not test_sqlite_connection():
            sys.exit(1)
        
        # 测试数据库管理器
        if not test_database_manager():
            sys.exit(1)
        
        # 测试Alembic配置
        if not test_alembic_configuration():
            sys.exit(1)
        
        logger.info("🎉 所有数据库连接和配置测试通过！")
        
    except Exception as e:
        logger.error(f"💥 数据库测试失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
