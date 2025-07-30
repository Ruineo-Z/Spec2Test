#!/usr/bin/env python3
"""
测试执行总结脚本
用于生成测试报告和问题分析
"""

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class TestSummaryGenerator:
    """测试总结生成器"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.reports_dir = self.project_root / "reports"
        self.test_results = {}
        self.coverage_data = {}
        self.issues_found = []
        self.recommendations = []

    def ensure_reports_dir(self):
        """确保报告目录存在"""
        self.reports_dir.mkdir(exist_ok=True)

    def run_test_suite(self) -> Dict[str, Any]:
        """运行测试套件并收集结果"""
        print("🚀 开始运行测试套件...")

        test_commands = {
            "unit": ["python", "run_tests.py", "unit"],
            "integration": ["python", "run_tests.py", "integration"],
            "api": ["python", "run_tests.py", "api"],
            "compatibility": ["python", "run_tests.py", "compatibility"],
            "error_handling": ["python", "run_tests.py", "error"],
            "yaml_specific": ["python", "run_tests.py", "yaml"],
        }

        results = {}

        for test_type, cmd in test_commands.items():
            print(f"\n📋 运行 {test_type} 测试...")
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=300
                )
                results[test_type] = {
                    "success": result.returncode == 0,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }

                if result.returncode == 0:
                    print(f"✅ {test_type} 测试通过")
                else:
                    print(f"❌ {test_type} 测试失败")
                    self.issues_found.append(
                        {
                            "type": "test_failure",
                            "category": test_type,
                            "message": f"{test_type} 测试失败",
                            "details": result.stderr,
                        }
                    )

            except subprocess.TimeoutExpired:
                print(f"⏰ {test_type} 测试超时")
                results[test_type] = {
                    "success": False,
                    "returncode": -1,
                    "stdout": "",
                    "stderr": "测试超时",
                }
                self.issues_found.append(
                    {
                        "type": "test_timeout",
                        "category": test_type,
                        "message": f"{test_type} 测试超时",
                        "details": "测试执行超过5分钟",
                    }
                )
            except Exception as e:
                print(f"💥 {test_type} 测试出错: {e}")
                results[test_type] = {
                    "success": False,
                    "returncode": -2,
                    "stdout": "",
                    "stderr": str(e),
                }
                self.issues_found.append(
                    {
                        "type": "test_error",
                        "category": test_type,
                        "message": f"{test_type} 测试出错",
                        "details": str(e),
                    }
                )

        self.test_results = results
        return results

    def run_coverage_analysis(self) -> Dict[str, Any]:
        """运行覆盖率分析"""
        print("\n📊 运行覆盖率分析...")

        try:
            result = subprocess.run(
                ["python", "run_tests.py", "coverage"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            coverage_data = {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

            # 尝试解析覆盖率数据
            if result.returncode == 0:
                coverage_data["report_available"] = True
                print("✅ 覆盖率分析完成")
            else:
                coverage_data["report_available"] = False
                print("❌ 覆盖率分析失败")
                self.issues_found.append(
                    {
                        "type": "coverage_failure",
                        "category": "coverage",
                        "message": "覆盖率分析失败",
                        "details": result.stderr,
                    }
                )

            self.coverage_data = coverage_data
            return coverage_data

        except Exception as e:
            print(f"💥 覆盖率分析出错: {e}")
            coverage_data = {
                "success": False,
                "report_available": False,
                "error": str(e),
            }
            self.coverage_data = coverage_data
            return coverage_data

    def analyze_test_yaml(self) -> Dict[str, Any]:
        """分析test.yaml文件"""
        print("\n📄 分析 test.yaml 文件...")

        test_yaml_path = self.project_root / "test.yaml"
        analysis = {
            "file_exists": test_yaml_path.exists(),
            "file_size": 0,
            "endpoints_count": 0,
            "issues": [],
        }

        if test_yaml_path.exists():
            analysis["file_size"] = test_yaml_path.stat().st_size
            print(f"✅ test.yaml 文件存在 ({analysis['file_size']} bytes)")

            try:
                import yaml

                with open(test_yaml_path, "r", encoding="utf-8") as f:
                    yaml_content = yaml.safe_load(f)

                # 分析OpenAPI结构
                if "paths" in yaml_content:
                    analysis["endpoints_count"] = len(yaml_content["paths"])
                    print(f"📋 发现 {analysis['endpoints_count']} 个API端点")

                if "openapi" in yaml_content:
                    analysis["openapi_version"] = yaml_content["openapi"]
                    print(f"📝 OpenAPI版本: {analysis['openapi_version']}")

                if "info" in yaml_content:
                    analysis["api_info"] = yaml_content["info"]
                    print(f"ℹ️ API信息: {yaml_content['info'].get('title', 'N/A')}")

                analysis["valid_yaml"] = True

            except Exception as e:
                print(f"❌ test.yaml 解析失败: {e}")
                analysis["valid_yaml"] = False
                analysis["issues"].append(f"YAML解析错误: {e}")
                self.issues_found.append(
                    {
                        "type": "yaml_parse_error",
                        "category": "test_yaml",
                        "message": "test.yaml解析失败",
                        "details": str(e),
                    }
                )
        else:
            print("❌ test.yaml 文件不存在")
            analysis["issues"].append("test.yaml文件不存在")
            self.issues_found.append(
                {
                    "type": "missing_file",
                    "category": "test_yaml",
                    "message": "test.yaml文件不存在",
                    "details": "项目根目录下未找到test.yaml文件",
                }
            )

        return analysis

    def check_project_structure(self) -> Dict[str, Any]:
        """检查项目结构"""
        print("\n🏗️ 检查项目结构...")

        required_files = [
            "app/main.py",
            "app/api/parser.py",
            "app/config/settings.py",
            "tests/conftest.py",
            "pytest.ini",
            "pyproject.toml",
        ]

        required_dirs = [
            "app",
            "tests",
            "tests/unit",
            "tests/integration",
            "tests/compatibility",
            "tests/performance",
        ]

        structure_check = {
            "missing_files": [],
            "missing_dirs": [],
            "extra_files": [],
            "structure_score": 0,
        }

        # 检查必需文件
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                structure_check["missing_files"].append(file_path)
                print(f"❌ 缺少文件: {file_path}")
            else:
                print(f"✅ 文件存在: {file_path}")

        # 检查必需目录
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                structure_check["missing_dirs"].append(dir_path)
                print(f"❌ 缺少目录: {dir_path}")
            else:
                print(f"✅ 目录存在: {dir_path}")

        # 计算结构得分
        total_items = len(required_files) + len(required_dirs)
        missing_items = len(structure_check["missing_files"]) + len(
            structure_check["missing_dirs"]
        )
        structure_check["structure_score"] = (
            (total_items - missing_items) / total_items
        ) * 100

        print(f"📊 项目结构得分: {structure_check['structure_score']:.1f}%")

        return structure_check

    def generate_recommendations(self):
        """生成改进建议"""
        print("\n💡 生成改进建议...")

        # 基于测试结果生成建议
        failed_tests = [
            k for k, v in self.test_results.items() if not v.get("success", False)
        ]

        if failed_tests:
            self.recommendations.append(
                {
                    "priority": "high",
                    "category": "test_failures",
                    "title": "修复失败的测试",
                    "description": f"以下测试失败: {', '.join(failed_tests)}",
                    "action": "检查测试日志，修复相关代码问题",
                }
            )

        # 基于覆盖率生成建议
        if not self.coverage_data.get("success", False):
            self.recommendations.append(
                {
                    "priority": "medium",
                    "category": "coverage",
                    "title": "改善测试覆盖率",
                    "description": "覆盖率分析失败或覆盖率不足",
                    "action": "添加更多测试用例，提高代码覆盖率",
                }
            )

        # 基于问题生成建议
        if self.issues_found:
            issue_types = set(issue["type"] for issue in self.issues_found)
            for issue_type in issue_types:
                if issue_type == "yaml_parse_error":
                    self.recommendations.append(
                        {
                            "priority": "high",
                            "category": "yaml",
                            "title": "修复YAML格式问题",
                            "description": "test.yaml文件存在格式错误",
                            "action": "检查YAML语法，确保文件格式正确",
                        }
                    )
                elif issue_type == "missing_file":
                    self.recommendations.append(
                        {
                            "priority": "high",
                            "category": "files",
                            "title": "添加缺失文件",
                            "description": "项目缺少必要的文件",
                            "action": "创建缺失的文件，完善项目结构",
                        }
                    )

        # 通用建议
        self.recommendations.extend(
            [
                {
                    "priority": "medium",
                    "category": "documentation",
                    "title": "完善文档",
                    "description": "确保API文档与实际实现一致",
                    "action": "定期更新OpenAPI规范，保持文档同步",
                },
                {
                    "priority": "low",
                    "category": "automation",
                    "title": "设置CI/CD",
                    "description": "自动化测试和部署流程",
                    "action": "配置GitHub Actions或其他CI/CD工具",
                },
            ]
        )

    def generate_report(self) -> Dict[str, Any]:
        """生成完整报告"""
        print("\n📋 生成测试报告...")

        # 运行所有分析
        test_results = self.run_test_suite()
        coverage_data = self.run_coverage_analysis()
        yaml_analysis = self.analyze_test_yaml()
        structure_check = self.check_project_structure()

        # 生成建议
        self.generate_recommendations()

        # 计算总体得分
        total_tests = len(test_results)
        passed_tests = sum(
            1 for result in test_results.values() if result.get("success", False)
        )
        test_pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        overall_score = (
            test_pass_rate * 0.4
            + structure_check["structure_score"] * 0.3  # 测试通过率权重40%
            + (  # 项目结构权重30%
                100
                if yaml_analysis["file_exists"]
                and yaml_analysis.get("valid_yaml", False)
                else 0
            )
            * 0.3  # YAML有效性权重30%
        )

        report = {
            "timestamp": datetime.now().isoformat(),
            "project_name": "Spec2Test",
            "overall_score": round(overall_score, 1),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "test_pass_rate": round(test_pass_rate, 1),
                "issues_found": len(self.issues_found),
                "recommendations_count": len(self.recommendations),
            },
            "test_results": test_results,
            "coverage_data": coverage_data,
            "yaml_analysis": yaml_analysis,
            "structure_check": structure_check,
            "issues_found": self.issues_found,
            "recommendations": self.recommendations,
        }

        return report

    def save_report(self, report: Dict[str, Any]):
        """保存报告到文件"""
        self.ensure_reports_dir()

        # 保存JSON报告
        json_path = self.reports_dir / "test_summary.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # 生成Markdown报告
        md_path = self.reports_dir / "test_summary.md"
        self.generate_markdown_report(report, md_path)

        print(f"\n📄 报告已保存:")
        print(f"  JSON: {json_path}")
        print(f"  Markdown: {md_path}")

    def generate_markdown_report(self, report: Dict[str, Any], output_path: Path):
        """生成Markdown格式的报告"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# Spec2Test 测试报告\n\n")
            f.write(f"**生成时间**: {report['timestamp']}\n\n")
            f.write(f"**总体得分**: {report['overall_score']}/100\n\n")

            # 摘要
            summary = report["summary"]
            f.write("## 📊 测试摘要\n\n")
            f.write(f"- **总测试数**: {summary['total_tests']}\n")
            f.write(f"- **通过测试**: {summary['passed_tests']}\n")
            f.write(f"- **失败测试**: {summary['failed_tests']}\n")
            f.write(f"- **通过率**: {summary['test_pass_rate']}%\n")
            f.write(f"- **发现问题**: {summary['issues_found']}\n")
            f.write(f"- **改进建议**: {summary['recommendations_count']}\n\n")

            # 测试结果详情
            f.write("## 🧪 测试结果详情\n\n")
            for test_type, result in report["test_results"].items():
                status = "✅ 通过" if result["success"] else "❌ 失败"
                f.write(f"### {test_type}\n")
                f.write(f"**状态**: {status}\n\n")
                if not result["success"] and result.get("stderr"):
                    f.write(f"**错误信息**:\n```\n{result['stderr']}\n```\n\n")

            # YAML分析
            yaml_analysis = report["yaml_analysis"]
            f.write("## 📄 test.yaml 分析\n\n")
            f.write(f"- **文件存在**: {'是' if yaml_analysis['file_exists'] else '否'}\n")
            if yaml_analysis["file_exists"]:
                f.write(f"- **文件大小**: {yaml_analysis['file_size']} bytes\n")
                f.write(
                    f"- **API端点数**: {yaml_analysis.get('endpoints_count', 'N/A')}\n"
                )
                f.write(
                    f"- **OpenAPI版本**: {yaml_analysis.get('openapi_version', 'N/A')}\n"
                )
                f.write(
                    f"- **YAML有效**: {'是' if yaml_analysis.get('valid_yaml', False) else '否'}\n"
                )
            f.write("\n")

            # 发现的问题
            if report["issues_found"]:
                f.write("## ⚠️ 发现的问题\n\n")
                for i, issue in enumerate(report["issues_found"], 1):
                    f.write(f"### {i}. {issue['message']}\n")
                    f.write(f"**类型**: {issue['type']}\n")
                    f.write(f"**分类**: {issue['category']}\n")
                    f.write(f"**详情**: {issue['details']}\n\n")

            # 改进建议
            if report["recommendations"]:
                f.write("## 💡 改进建议\n\n")
                high_priority = [
                    r for r in report["recommendations"] if r["priority"] == "high"
                ]
                medium_priority = [
                    r for r in report["recommendations"] if r["priority"] == "medium"
                ]
                low_priority = [
                    r for r in report["recommendations"] if r["priority"] == "low"
                ]

                if high_priority:
                    f.write("### 🔴 高优先级\n\n")
                    for rec in high_priority:
                        f.write(f"**{rec['title']}**\n")
                        f.write(f"- {rec['description']}\n")
                        f.write(f"- 行动: {rec['action']}\n\n")

                if medium_priority:
                    f.write("### 🟡 中优先级\n\n")
                    for rec in medium_priority:
                        f.write(f"**{rec['title']}**\n")
                        f.write(f"- {rec['description']}\n")
                        f.write(f"- 行动: {rec['action']}\n\n")

                if low_priority:
                    f.write("### 🟢 低优先级\n\n")
                    for rec in low_priority:
                        f.write(f"**{rec['title']}**\n")
                        f.write(f"- {rec['description']}\n")
                        f.write(f"- 行动: {rec['action']}\n\n")

    def print_summary(self, report: Dict[str, Any]):
        """打印报告摘要"""
        print("\n" + "=" * 60)
        print("🎯 Spec2Test 测试总结")
        print("=" * 60)

        summary = report["summary"]
        print(f"\n📊 总体得分: {report['overall_score']}/100")
        print(f"\n🧪 测试结果:")
        print(f"   总数: {summary['total_tests']}")
        print(f"   通过: {summary['passed_tests']} ({summary['test_pass_rate']}%)")
        print(f"   失败: {summary['failed_tests']}")

        if report["issues_found"]:
            print(f"\n⚠️  发现 {len(report['issues_found'])} 个问题")
            for issue in report["issues_found"][:3]:  # 只显示前3个问题
                print(f"   - {issue['message']}")
            if len(report["issues_found"]) > 3:
                print(f"   - ... 还有 {len(report['issues_found']) - 3} 个问题")

        if report["recommendations"]:
            high_priority = [
                r for r in report["recommendations"] if r["priority"] == "high"
            ]
            if high_priority:
                print(f"\n💡 高优先级建议:")
                for rec in high_priority[:2]:  # 只显示前2个建议
                    print(f"   - {rec['title']}")

        print(f"\n📄 详细报告: reports/test_summary.md")
        print("=" * 60)


def main():
    """主函数"""
    generator = TestSummaryGenerator()

    try:
        # 生成报告
        report = generator.generate_report()

        # 保存报告
        generator.save_report(report)

        # 打印摘要
        generator.print_summary(report)

        # 根据结果设置退出码
        if report["overall_score"] >= 80:
            print("\n🎉 测试结果良好！")
            sys.exit(0)
        elif report["overall_score"] >= 60:
            print("\n⚠️ 测试结果一般，需要改进")
            sys.exit(1)
        else:
            print("\n💥 测试结果较差，需要重点关注")
            sys.exit(2)

    except Exception as e:
        print(f"\n💥 生成测试报告时出错: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
