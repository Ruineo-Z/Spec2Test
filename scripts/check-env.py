#!/usr/bin/env python3
"""
环境变量配置检查脚本

检查 .env 文件中的配置是否正确，并提供配置建议。
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from app.config.settings import settings
except ImportError as e:
    print(f"❌ 无法导入配置模块: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)
except Exception as e:
    print(f"❌ 配置加载失败: {e}")
    print("请检查 .env 文件中的配置格式")
    print("常见问题:")
    print('  - JSON格式的列表应使用双引号，如: ["item1","item2"]')
    print("  - 布尔值应使用小写: true/false")
    print("  - 数字不需要引号")
    sys.exit(1)


def check_env_file() -> bool:
    """检查 .env 文件是否存在"""
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    if not env_file.exists():
        print("❌ .env 文件不存在")
        if env_example.exists():
            print("💡 建议运行: cp .env.example .env")
        else:
            print("❌ .env.example 文件也不存在，请检查项目完整性")
        return False

    print("✅ .env 文件存在")
    return True


def check_required_vars() -> Tuple[List[str], List[str]]:
    """检查必需的环境变量"""
    required_vars = {
        "LLM_PROVIDER": "LLM服务提供商",
        "SECRET_KEY": "应用密钥",
    }

    conditional_vars = {
        "OPENAI_API_KEY": "OpenAI API密钥 (当LLM_PROVIDER=openai时必需)",
        "GEMINI_API_KEY": "Gemini API密钥 (当LLM_PROVIDER=gemini时必需)",
    }

    missing = []
    warnings = []

    # 检查必需变量
    for var, desc in required_vars.items():
        if var == "LLM_PROVIDER":
            value = getattr(settings.llm, "provider", None)
        elif var == "SECRET_KEY":
            value = getattr(settings, "secret_key", None)
        else:
            value = getattr(settings, var.lower(), None)

        if not value or (isinstance(value, str) and value.strip() == ""):
            missing.append(f"{var}: {desc}")
        else:
            print(f"✅ {var}: 已配置")

    # 检查条件变量
    llm_provider = getattr(settings.llm, "provider", "").lower()

    if llm_provider == "openai":
        if not settings.llm.openai_api_key or settings.llm.openai_api_key.strip() == "":
            missing.append("OPENAI_API_KEY: OpenAI API密钥 (当前LLM_PROVIDER=openai)")
        else:
            print("✅ OPENAI_API_KEY: 已配置")
    elif llm_provider == "gemini":
        if not settings.llm.gemini_api_key or settings.llm.gemini_api_key.strip() == "":
            missing.append("GEMINI_API_KEY: Gemini API密钥 (当前LLM_PROVIDER=gemini)")
        else:
            print("✅ GEMINI_API_KEY: 已配置")
    else:
        warnings.append(f"LLM_PROVIDER 值 '{llm_provider}' 不是有效选项 (openai/gemini)")

    # 检查安全配置
    if settings.secret_key == "dev-secret-key-change-in-production":
        warnings.append("SECRET_KEY 使用默认值，生产环境请更改")

    return missing, warnings


def check_database_config() -> List[str]:
    """检查数据库配置"""
    warnings = []

    if settings.database.driver == "sqlite":
        db_path = Path(settings.database.name)
        if not db_path.parent.exists():
            warnings.append(f"数据库目录不存在: {db_path.parent}")
        print("✅ 数据库配置: SQLite (开发环境)")
    else:
        if not settings.database.host:
            warnings.append("数据库主机未配置")
        if not settings.database.user:
            warnings.append("数据库用户未配置")
        print(f"✅ 数据库配置: {settings.database.driver}")

    return warnings


def check_directories() -> List[str]:
    """检查必需目录"""
    warnings = []

    directories = [
        settings.work_dir,
        settings.temp_dir,
        settings.test.output_dir,
        settings.log.file_path.parent,
    ]

    for directory in directories:
        if not directory.exists():
            try:
                directory.mkdir(parents=True, exist_ok=True)
                print(f"✅ 创建目录: {directory}")
            except Exception as e:
                warnings.append(f"无法创建目录 {directory}: {e}")
        else:
            print(f"✅ 目录存在: {directory}")

    return warnings


def print_configuration_summary():
    """打印配置摘要"""
    print("\n" + "=" * 50)
    print("📋 当前配置摘要")
    print("=" * 50)

    config_items = [
        ("应用名称", settings.app_name),
        ("应用版本", settings.app_version),
        ("调试模式", settings.debug),
        ("API地址", f"{settings.api_host}:{settings.api_port}"),
        ("LLM提供商", settings.llm.provider),
        ("数据库类型", settings.database.driver),
        ("日志级别", settings.log.level),
        ("工作目录", settings.work_dir),
        ("测试输出目录", settings.test.output_dir),
    ]

    for name, value in config_items:
        print(f"{name:12}: {value}")


def main():
    """主函数"""
    print("🔍 检查环境变量配置...\n")

    # 检查 .env 文件
    if not check_env_file():
        sys.exit(1)

    print()

    # 检查必需变量
    missing, warnings = check_required_vars()

    print()

    # 检查数据库配置
    db_warnings = check_database_config()
    warnings.extend(db_warnings)

    print()

    # 检查目录
    dir_warnings = check_directories()
    warnings.extend(dir_warnings)

    # 打印结果
    print("\n" + "=" * 50)
    print("📊 检查结果")
    print("=" * 50)

    if missing:
        print("\n❌ 缺少必需配置:")
        for item in missing:
            print(f"  - {item}")

    if warnings:
        print("\n⚠️  配置警告:")
        for warning in warnings:
            print(f"  - {warning}")

    if not missing and not warnings:
        print("\n🎉 所有配置检查通过！")

    # 打印配置摘要
    print_configuration_summary()

    # 提供建议
    print("\n" + "=" * 50)
    print("💡 建议")
    print("=" * 50)

    if missing:
        print("1. 请在 .env 文件中配置缺少的环境变量")
        print("2. 参考 .env.example 文件了解配置格式")
        print("3. 查看 docs/ENVIRONMENT_SETUP.md 获取详细说明")

    if settings.debug:
        print("4. 生产环境请设置 DEBUG=false")

    print("5. 定期更新 API 密钥以确保安全")
    print("6. 使用 python -m app.cli config --validate 验证完整配置")

    # 返回退出码
    if missing:
        sys.exit(1)
    elif warnings:
        sys.exit(2)  # 有警告但可以运行
    else:
        sys.exit(0)  # 完全正常


if __name__ == "__main__":
    main()
