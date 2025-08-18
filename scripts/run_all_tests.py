#!/usr/bin/env python3
"""
运行所有测试的脚本

包括单元测试、集成测试和测试覆盖率报告
"""

import subprocess
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(command, description):
    """运行命令并处理结果"""
    print(f"\n🔄 {description}")
    print(f"执行命令: {command}")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.stdout:
            print(result.stdout)
        
        print(f"✅ {description} - 成功")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - 失败")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    """主函数"""
    print("🚀 开始运行Spec2Test项目的完整测试套件")
    print("=" * 60)
    
    # 检查pytest是否安装
    try:
        import pytest
        print(f"✅ pytest版本: {pytest.__version__}")
    except ImportError:
        print("❌ pytest未安装，请运行: pip install pytest pytest-asyncio pytest-cov")
        return False
    
    success_count = 0
    total_tests = 0
    
    # 1. 运行单元测试
    print("\n📋 第1步: 运行单元测试")
    
    # 1.1 文档分析模块测试
    if run_command(
        "python -m pytest tests/unit/test_document_analyzer/ -v --tb=short",
        "文档分析模块单元测试"
    ):
        success_count += 1
    total_tests += 1
    
    # 1.2 测试生成模块测试
    if run_command(
        "python -m pytest tests/unit/test_test_generator/ -v --tb=short",
        "测试生成模块单元测试"
    ):
        success_count += 1
    total_tests += 1
    
    # 1.3 测试执行模块测试
    if run_command(
        "python -m pytest tests/unit/test_test_executor/ -v --tb=short",
        "测试执行模块单元测试"
    ):
        success_count += 1
    total_tests += 1
    
    # 1.4 结果分析模块测试
    if run_command(
        "python -m pytest tests/unit/test_report_analyzer/ -v --tb=short",
        "结果分析模块单元测试"
    ):
        success_count += 1
    total_tests += 1
    
    # 1.5 任务系统测试
    if run_command(
        "python -m pytest tests/test_tasks/ -v --tb=short",
        "异步任务系统单元测试"
    ):
        success_count += 1
    total_tests += 1
    
    # 2. 运行集成测试
    print("\n🔗 第2步: 运行集成测试")
    
    # 2.1 API集成测试
    if run_command(
        "python -m pytest tests/integration/test_api/ -v --tb=short",
        "API集成测试"
    ):
        success_count += 1
    total_tests += 1
    
    # 2.2 完整流程测试
    if run_command(
        "python -m pytest tests/integration/test_workflows/ -v --tb=short",
        "完整流程集成测试"
    ):
        success_count += 1
    total_tests += 1
    
    # 3. 运行所有测试并生成覆盖率报告
    print("\n📊 第3步: 生成测试覆盖率报告")
    
    if run_command(
        "python -m pytest --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml",
        "生成测试覆盖率报告"
    ):
        success_count += 1
        print("\n📈 覆盖率报告已生成:")
        print("  - HTML报告: htmlcov/index.html")
        print("  - XML报告: coverage.xml")
    total_tests += 1
    
    # 4. 运行性能测试（如果存在）
    print("\n⚡ 第4步: 运行性能测试")
    
    if os.path.exists("tests/performance"):
        if run_command(
            "python -m pytest tests/performance/ -v --tb=short",
            "性能测试"
        ):
            success_count += 1
        total_tests += 1
    else:
        print("ℹ️ 未找到性能测试目录，跳过性能测试")
    
    # 5. 代码质量检查
    print("\n🔍 第5步: 代码质量检查")
    
    # 检查是否安装了flake8
    try:
        import flake8
        if run_command(
            "python -m flake8 app/ --max-line-length=120 --ignore=E203,W503",
            "代码风格检查 (flake8)"
        ):
            success_count += 1
        total_tests += 1
    except ImportError:
        print("ℹ️ flake8未安装，跳过代码风格检查")
    
    # 检查是否安装了mypy
    try:
        import mypy
        if run_command(
            "python -m mypy app/ --ignore-missing-imports",
            "类型检查 (mypy)"
        ):
            success_count += 1
        total_tests += 1
    except ImportError:
        print("ℹ️ mypy未安装，跳过类型检查")
    
    # 6. 安全检查
    print("\n🔒 第6步: 安全检查")
    
    try:
        import bandit
        if run_command(
            "python -m bandit -r app/ -f json -o bandit-report.json",
            "安全漏洞检查 (bandit)"
        ):
            success_count += 1
            print("📄 安全检查报告: bandit-report.json")
        total_tests += 1
    except ImportError:
        print("ℹ️ bandit未安装，跳过安全检查")
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    print(f"✅ 成功: {success_count}/{total_tests}")
    print(f"❌ 失败: {total_tests - success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("\n🎉 所有测试都通过了！项目质量良好。")
        success_rate = 100.0
    else:
        success_rate = (success_count / total_tests) * 100
        print(f"\n⚠️ 成功率: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("✅ 项目质量良好，但还有改进空间。")
        elif success_rate >= 60:
            print("⚠️ 项目质量一般，建议修复失败的测试。")
        else:
            print("❌ 项目质量需要改进，请优先修复测试问题。")
    
    # 生成测试报告
    print("\n📋 测试报告:")
    print(f"  - 项目根目录: {project_root}")
    print(f"  - 测试目录: {project_root}/tests/")
    print(f"  - 覆盖率报告: {project_root}/htmlcov/index.html")
    
    # 推荐的后续步骤
    if success_count < total_tests:
        print("\n🔧 建议的修复步骤:")
        print("1. 查看失败测试的详细输出")
        print("2. 修复代码或测试中的问题")
        print("3. 重新运行失败的测试")
        print("4. 确保所有依赖都已正确安装")
    
    return success_count == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
