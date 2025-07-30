#!/usr/bin/env python3
"""
测试运行脚本
用于执行不同类型的测试并生成报告
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def run_command(cmd: List[str], description: str) -> bool:
    """运行命令并返回是否成功"""
    print(f"\n{'='*60}")
    print(f"执行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} - 成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - 失败 (退出码: {e.returncode})")
        return False
    except Exception as e:
        print(f"❌ {description} - 错误: {e}")
        return False


def ensure_reports_dir():
    """确保报告目录存在"""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


def run_unit_tests() -> bool:
    """运行单元测试"""
    cmd = ["python", "-m", "pytest", "-m", "unit", "--tb=short", "-v"]
    return run_command(cmd, "单元测试")


def run_integration_tests() -> bool:
    """运行集成测试"""
    cmd = ["python", "-m", "pytest", "-m", "integration", "--tb=short", "-v"]
    return run_command(cmd, "集成测试")


def run_api_tests() -> bool:
    """运行API测试"""
    cmd = ["python", "-m", "pytest", "-m", "api", "--tb=short", "-v"]
    return run_command(cmd, "API测试")


def run_compatibility_tests() -> bool:
    """运行兼容性测试"""
    cmd = ["python", "-m", "pytest", "-m", "compatibility", "--tb=short", "-v"]
    return run_command(cmd, "兼容性测试")


def run_error_handling_tests() -> bool:
    """运行错误处理测试"""
    cmd = ["python", "-m", "pytest", "-m", "error_handling", "--tb=short", "-v"]
    return run_command(cmd, "错误处理测试")


def run_performance_tests() -> bool:
    """运行性能测试"""
    cmd = [
        "python",
        "-m",
        "pytest",
        "-m",
        "performance",
        "--tb=short",
        "-v",
        "--durations=0",
    ]
    return run_command(cmd, "性能测试")


def run_all_tests() -> bool:
    """运行所有测试（除了慢速测试）"""
    cmd = ["python", "-m", "pytest", "-m", "not slow", "--tb=short", "-v"]
    return run_command(cmd, "所有测试（除慢速测试）")


def run_full_test_suite() -> bool:
    """运行完整测试套件（包括慢速测试）"""
    cmd = ["python", "-m", "pytest", "--tb=short", "-v", "--durations=10"]
    return run_command(cmd, "完整测试套件")


def run_coverage_report() -> bool:
    """生成覆盖率报告"""
    cmd = [
        "python",
        "-m",
        "pytest",
        "--cov=app",
        "--cov-report=html:reports/coverage",
        "--cov-report=term-missing",
        "--cov-report=xml:reports/coverage.xml",
        "-m",
        "not slow",
    ]
    return run_command(cmd, "覆盖率报告生成")


def run_test_with_yaml() -> bool:
    """使用test.yaml文件运行特定测试"""
    # 首先检查test.yaml文件是否存在
    test_yaml_path = Path("test.yaml")
    if not test_yaml_path.exists():
        print(f"❌ 测试文件 {test_yaml_path} 不存在")
        return False

    print(f"✅ 找到测试文件: {test_yaml_path}")

    # 运行文档上传和分析相关的测试
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/integration/test_document_upload.py",
        "tests/integration/test_error_scenarios.py",
        "tests/compatibility/test_api_compatibility.py",
        "-v",
        "--tb=short",
    ]
    return run_command(cmd, "test.yaml相关测试")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行测试套件")
    parser.add_argument(
        "test_type",
        choices=[
            "unit",
            "integration",
            "api",
            "compatibility",
            "error",
            "performance",
            "all",
            "full",
            "coverage",
            "yaml",
        ],
        help="要运行的测试类型",
    )

    args = parser.parse_args()

    # 确保报告目录存在
    ensure_reports_dir()

    # 根据参数运行相应的测试
    test_functions = {
        "unit": run_unit_tests,
        "integration": run_integration_tests,
        "api": run_api_tests,
        "compatibility": run_compatibility_tests,
        "error": run_error_handling_tests,
        "performance": run_performance_tests,
        "all": run_all_tests,
        "full": run_full_test_suite,
        "coverage": run_coverage_report,
        "yaml": run_test_with_yaml,
    }

    success = test_functions[args.test_type]()

    if success:
        print(f"\n🎉 {args.test_type} 测试完成！")
        if args.test_type == "coverage":
            print("📊 覆盖率报告已生成在 reports/coverage/index.html")
        sys.exit(0)
    else:
        print(f"\n💥 {args.test_type} 测试失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
