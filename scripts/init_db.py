#!/usr/bin/env python3
"""
数据库初始化脚本

用于创建数据库表和初始化数据。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import init_database, db_manager
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """主函数"""
    try:
        logger.info("开始数据库初始化...")
        
        # 初始化数据库
        init_database()
        
        logger.info("数据库初始化完成！")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
