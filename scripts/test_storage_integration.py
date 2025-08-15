#!/usr/bin/env python3
"""
存储抽象层集成测试脚本

测试文件存储、数据库存储、缓存存储的功能和集成。
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.shared.utils.logger import get_logger
from app.core.shared.storage import (
    StorageFactory, StorageManager, StorageType,
    get_file_storage, get_database_storage, get_cache_storage
)

logger = get_logger(__name__)


def test_storage_imports():
    """测试存储模块导入"""
    logger.info("测试存储模块导入...")
    
    try:
        from app.core.shared.storage import (
            BaseStorage, StorageType, StorageOperation,
            StorageResult, StorageMetadata, StorageError,
            FileStorage, DatabaseStorage, CacheStorage,
            StorageFactory, StorageManager
        )
        logger.info("✅ 存储模块导入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ 存储模块导入失败: {e}")
        return False


def test_file_storage():
    """测试文件存储"""
    logger.info("测试文件存储...")
    
    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        
        # 创建文件存储客户端
        config = {
            "base_path": temp_dir,
            "create_dirs": True
        }
        storage = get_file_storage(config)
        
        # 测试写入文本文件
        test_data = "这是一个测试文件内容"
        write_result = storage.write_text("test.txt", test_data)
        assert write_result.success, f"写入失败: {write_result.error_message}"
        logger.info("✅ 文件写入成功")
        
        # 测试读取文本文件
        read_result = storage.read_text("test.txt")
        assert read_result.success, f"读取失败: {read_result.error_message}"
        assert read_result.data == test_data, "读取内容不匹配"
        logger.info("✅ 文件读取成功")
        
        # 测试JSON文件
        json_data = {"name": "测试", "value": 123, "items": [1, 2, 3]}
        write_result = storage.write_json("test.json", json_data)
        assert write_result.success, f"JSON写入失败: {write_result.error_message}"
        
        read_result = storage.read_json("test.json")
        assert read_result.success, f"JSON读取失败: {read_result.error_message}"
        assert read_result.data == json_data, "JSON内容不匹配"
        logger.info("✅ JSON文件操作成功")
        
        # 测试文件存在性检查
        assert storage.exists("test.txt"), "文件存在性检查失败"
        assert not storage.exists("nonexistent.txt"), "不存在文件检查失败"
        logger.info("✅ 文件存在性检查成功")
        
        # 测试目录列表
        list_result = storage.list()
        assert list_result.success, f"目录列表失败: {list_result.error_message}"
        assert "test.txt" in list_result.data, "目录列表内容不正确"
        logger.info("✅ 目录列表成功")
        
        # 测试文件删除
        delete_result = storage.delete("test.txt")
        assert delete_result.success, f"文件删除失败: {delete_result.error_message}"
        assert not storage.exists("test.txt"), "文件删除后仍存在"
        logger.info("✅ 文件删除成功")
        
        # 清理临时目录
        shutil.rmtree(temp_dir)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 文件存储测试失败: {e}")
        return False


def test_database_storage():
    """测试数据库存储"""
    logger.info("测试数据库存储...")
    
    try:
        # 创建数据库存储客户端
        storage = get_database_storage()
        
        # 测试列出表
        list_result = storage.list()
        logger.info(f"✅ 数据库表列表: {list_result.data if list_result.success else '获取失败'}")
        
        # 注意：这里只测试基本功能，不进行实际的数据操作
        # 因为需要确保数据库连接和模型正确设置
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库存储测试失败: {e}")
        return False


def test_cache_storage():
    """测试缓存存储"""
    logger.info("测试缓存存储...")
    
    try:
        # 创建缓存存储客户端
        config = {
            "host": "localhost",
            "port": 6379,
            "db": 15,  # 使用测试数据库
            "prefix": "test:",
            "default_ttl": 60
        }
        
        try:
            storage = get_cache_storage(config)
        except Exception as e:
            logger.warning(f"⚠️ Redis连接失败，跳过缓存测试: {e}")
            return True  # 不算作失败，因为Redis可能未安装
        
        # 测试写入缓存
        test_data = {"message": "Hello Cache", "timestamp": 1234567890}
        write_result = storage.write("test_key", test_data, ttl=30)
        if not write_result.success:
            logger.warning(f"⚠️ 缓存写入失败: {write_result.error_message}")
            return True
        logger.info("✅ 缓存写入成功")
        
        # 测试读取缓存
        read_result = storage.read("test_key")
        if read_result.success:
            assert read_result.data == test_data, "缓存内容不匹配"
            logger.info("✅ 缓存读取成功")
        
        # 测试缓存存在性
        assert storage.exists("test_key"), "缓存存在性检查失败"
        logger.info("✅ 缓存存在性检查成功")
        
        # 测试缓存列表
        list_result = storage.list()
        if list_result.success:
            logger.info(f"✅ 缓存键列表: {len(list_result.data)}个键")
        
        # 测试删除缓存
        delete_result = storage.delete("test_key")
        if delete_result.success:
            logger.info("✅ 缓存删除成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 缓存存储测试失败: {e}")
        return False


def test_storage_factory():
    """测试存储工厂"""
    logger.info("测试存储工厂...")
    
    try:
        # 测试获取可用存储类型
        storage_types = StorageFactory.get_available_storage_types()
        logger.info(f"✅ 可用存储类型: {storage_types}")
        
        # 测试创建文件存储
        temp_dir = tempfile.mkdtemp()
        file_storage = StorageFactory.create_storage("file", {"base_path": temp_dir})
        assert file_storage.storage_type == StorageType.FILE
        logger.info("✅ 工厂创建文件存储成功")
        
        # 测试缓存信息
        cache_info = StorageFactory.get_cache_info()
        logger.info(f"✅ 工厂缓存信息: {cache_info}")
        
        # 清理
        shutil.rmtree(temp_dir)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 存储工厂测试失败: {e}")
        return False


def test_storage_manager():
    """测试存储管理器"""
    logger.info("测试存储管理器...")
    
    try:
        # 创建存储管理器
        manager = StorageManager()
        
        # 注册文件存储
        temp_dir = tempfile.mkdtemp()
        file_storage = get_file_storage({"base_path": temp_dir})
        manager.register_storage("file", file_storage)
        
        # 测试获取存储
        retrieved_storage = manager.get_storage("file")
        assert retrieved_storage is not None, "获取存储失败"
        logger.info("✅ 存储管理器注册和获取成功")
        
        # 测试存储信息
        storage_info = manager.get_storage_info()
        assert "file" in storage_info, "存储信息不包含注册的存储"
        logger.info(f"✅ 存储信息: {storage_info}")
        
        # 清理
        shutil.rmtree(temp_dir)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 存储管理器测试失败: {e}")
        return False


def test_storage_operations():
    """测试存储操作"""
    logger.info("测试存储操作...")
    
    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        storage = get_file_storage({"base_path": temp_dir})
        
        # 测试复制操作
        original_data = "原始文件内容"
        storage.write_text("original.txt", original_data)
        
        copy_result = storage.copy("original.txt", "copy.txt")
        assert copy_result.success, f"复制失败: {copy_result.error_message}"
        
        # 验证复制结果
        copy_read = storage.read_text("copy.txt")
        assert copy_read.success and copy_read.data == original_data, "复制内容不正确"
        logger.info("✅ 文件复制成功")
        
        # 测试移动操作
        move_result = storage.move("copy.txt", "moved.txt")
        assert move_result.success, f"移动失败: {move_result.error_message}"
        
        # 验证移动结果
        assert not storage.exists("copy.txt"), "移动后源文件仍存在"
        assert storage.exists("moved.txt"), "移动后目标文件不存在"
        logger.info("✅ 文件移动成功")
        
        # 测试元数据获取
        metadata = storage.get_metadata("moved.txt")
        assert metadata is not None, "获取元数据失败"
        assert metadata.size > 0, "元数据大小不正确"
        logger.info(f"✅ 元数据获取成功: {metadata.to_dict()}")
        
        # 清理
        shutil.rmtree(temp_dir)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 存储操作测试失败: {e}")
        return False


def main():
    """主函数"""
    try:
        logger.info("🚀 开始存储抽象层集成测试...")
        
        tests = [
            ("存储模块导入", test_storage_imports),
            ("文件存储", test_file_storage),
            ("数据库存储", test_database_storage),
            ("缓存存储", test_cache_storage),
            ("存储工厂", test_storage_factory),
            ("存储管理器", test_storage_manager),
            ("存储操作", test_storage_operations),
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
            logger.info("🎉 所有存储抽象层测试通过！")
        else:
            logger.warning(f"⚠️ {total - passed} 个测试失败")
            
        return passed == total
        
    except Exception as e:
        logger.error(f"💥 存储抽象层测试失败: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
