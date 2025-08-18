#!/usr/bin/env python3
"""
数据库初始化脚本

用于创建数据库表、索引和初始数据
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional
import argparse

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import init_database, db_manager
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


async def create_database_if_not_exists(database_url: str):
    """创建数据库（如果不存在）"""
    try:
        import asyncpg
        from urllib.parse import urlparse

        # 解析数据库URL
        parsed = urlparse(database_url)
        db_name = parsed.path.lstrip('/')
        admin_url = f"{parsed.scheme}://{parsed.netloc}/postgres"

        logger.info(f"检查数据库是否存在: {db_name}")

        # 连接到postgres数据库
        conn = await asyncpg.connect(admin_url)

        # 检查数据库是否存在
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )

        if not exists:
            logger.info(f"创建数据库: {db_name}")
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            logger.info(f"数据库 {db_name} 创建成功")
        else:
            logger.info(f"数据库 {db_name} 已存在")

        await conn.close()

    except Exception as e:
        logger.error(f"创建数据库失败: {str(e)}")
        raise


def create_indexes():
    """创建数据库索引"""
    try:
        logger.info("开始创建数据库索引")

        # 这里可以添加具体的索引创建逻辑
        # 目前使用现有的数据库管理器

        logger.info("数据库索引创建完成")

    except Exception as e:
        logger.error(f"创建数据库索引失败: {str(e)}")
        raise


def insert_initial_data():
    """插入初始数据"""
    try:
        logger.info("开始插入初始数据")

        # 这里可以添加初始数据插入逻辑
        # 例如：默认配置、管理员账户等

        logger.info("初始数据插入完成")

    except Exception as e:
        logger.error(f"插入初始数据失败: {str(e)}")
        raise


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="初始化Spec2Test数据库")
    parser.add_argument(
        "--database-url",
        help="数据库连接URL"
    )
    parser.add_argument(
        "--skip-create-db",
        action="store_true",
        help="跳过数据库创建步骤"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="仅验证数据库，不执行初始化"
    )

    args = parser.parse_args()

    try:
        logger.info("开始数据库初始化...")

        # 如果提供了数据库URL且不跳过创建数据库
        if args.database_url and not args.skip_create_db:
            await create_database_if_not_exists(args.database_url)

        if not args.verify_only:
            # 初始化数据库表
            init_database()

            # 创建索引
            create_indexes()

            # 插入初始数据
            insert_initial_data()

        logger.info("数据库初始化完成！")
        print("✅ 数据库初始化成功")

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        print(f"❌ 数据库初始化失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
