#!/usr/bin/env python3
"""
数据库基础功能测试脚本

测试基础模型和数据库管理器的核心功能。
使用SQLite内存数据库进行测试。
"""

import sys
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import BaseModel
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


# 测试模型
class TestUser(BaseModel):
    """测试用户模型"""
    __tablename__ = "test_users"


def test_basic_model_functionality():
    """测试基础模型功能"""
    logger.info("开始测试基础模型功能...")
    
    # 创建内存SQLite数据库
    engine = create_engine("sqlite:///:memory:", echo=True)
    
    # 创建所有表
    BaseModel.metadata.create_all(engine)
    logger.info("数据表创建成功")
    
    # 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 测试模型创建
        user = TestUser()
        session.add(user)
        session.commit()
        
        logger.info(f"用户创建成功: {user}")
        logger.info(f"用户ID: {user.id}")
        logger.info(f"创建时间: {user.created_at}")
        logger.info(f"更新时间: {user.updated_at}")
        logger.info(f"删除标记: {user.is_deleted}")
        
        # 测试to_dict方法
        user_dict = user.to_dict()
        logger.info(f"用户字典: {user_dict}")
        
        # 测试软删除
        user.soft_delete()
        session.commit()
        logger.info(f"软删除后: is_deleted={user.is_deleted}")
        
        # 测试恢复
        user.restore()
        session.commit()
        logger.info(f"恢复后: is_deleted={user.is_deleted}")
        
        # 测试update_from_dict
        update_data = {"is_deleted": True}
        user.update_from_dict(update_data)
        session.commit()
        logger.info(f"字典更新后: is_deleted={user.is_deleted}")
        
        logger.info("✅ 基础模型功能测试通过！")
        
    except Exception as e:
        logger.error(f"❌ 基础模型功能测试失败: {e}")
        raise
    finally:
        session.close()


def test_table_name_generation():
    """测试表名自动生成"""
    logger.info("开始测试表名自动生成...")
    
    class UserProfile(BaseModel):
        pass
    
    class APIKey(BaseModel):
        pass
    
    class TestModelName(BaseModel):
        pass
    
    assert UserProfile.__tablename__ == "user_profile"
    assert APIKey.__tablename__ == "a_p_i_key"
    assert TestModelName.__tablename__ == "test_model_name"
    
    logger.info("✅ 表名自动生成测试通过！")


def main():
    """主函数"""
    try:
        logger.info("🚀 开始数据库基础功能测试...")
        
        # 测试表名生成
        test_table_name_generation()
        
        # 测试基础模型功能
        test_basic_model_functionality()
        
        logger.info("🎉 所有数据库基础功能测试通过！")
        
    except Exception as e:
        logger.error(f"💥 数据库基础功能测试失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
