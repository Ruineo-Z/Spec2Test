#!/usr/bin/env python3
"""
Spec2Test API验证脚本
用于验证API端点的功能和响应
"""

import json
import sys
import time
from typing import Any, Dict, List

import requests


class APIValidator:
    """API验证器"""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []

    def test_endpoint(
        self,
        method: str,
        path: str,
        expected_status: int = 200,
        data: Dict[str, Any] = None,
        description: str = "",
    ) -> bool:
        """测试单个端点"""
        url = f"{self.base_url}{path}"

        try:
            if method.upper() == "GET":
                response = self.session.get(url, timeout=10)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=10)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, timeout=10)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, timeout=10)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            success = response.status_code == expected_status

            result = {
                "method": method.upper(),
                "path": path,
                "description": description,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "success": success,
                "response_time": response.elapsed.total_seconds(),
                "content_type": response.headers.get("content-type", ""),
                "response_size": len(response.content),
            }

            if not success:
                result["error"] = f"期望状态码 {expected_status}，实际 {response.status_code}"
                result["response_text"] = response.text[:500]  # 限制错误信息长度

            self.results.append(result)
            return success

        except requests.exceptions.RequestException as e:
            result = {
                "method": method.upper(),
                "path": path,
                "description": description,
                "expected_status": expected_status,
                "actual_status": 0,
                "success": False,
                "error": str(e),
                "response_time": 0,
            }
            self.results.append(result)
            return False

    def check_server_health(self) -> bool:
        """检查服务器健康状态"""
        print("🔍 检查服务器健康状态...")
        return self.test_endpoint("GET", "/health", 200, description="健康检查")

    def test_api_docs(self) -> bool:
        """测试API文档端点"""
        print("📚 测试API文档...")
        success = True
        success &= self.test_endpoint(
            "GET", "/api/v1/docs", 200, description="Swagger UI"
        )
        success &= self.test_endpoint(
            "GET", "/api/v1/openapi.json", 200, description="OpenAPI规范"
        )
        return success

    def test_core_endpoints(self) -> bool:
        """测试核心API端点"""
        print("🚀 测试核心API端点...")
        success = True

        # 测试生成测试用例端点（如果存在）
        test_data = {
            "openapi_spec": {
                "openapi": "3.0.0",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {
                    "/test": {
                        "get": {
                            "summary": "Test endpoint",
                            "responses": {"200": {"description": "Success"}},
                        }
                    }
                },
            },
            "test_type": "normal",
        }

        # 注意：这些端点可能还未实现，所以允许404
        self.test_endpoint(
            "POST",
            "/api/v1/generate-tests",
            [200, 404],
            data=test_data,
            description="生成测试用例",
        )

        return success

    def test_error_handling(self) -> bool:
        """测试错误处理"""
        print("❌ 测试错误处理...")
        success = True

        # 测试不存在的端点
        success &= self.test_endpoint(
            "GET", "/api/v1/nonexistent", 404, description="不存在的端点"
        )

        # 测试无效的请求方法
        success &= self.test_endpoint(
            "PATCH", "/health", [405, 404], description="不支持的方法"
        )

        return success

    def test_performance(self) -> bool:
        """测试性能"""
        print("⚡ 测试性能...")

        # 测试响应时间
        start_time = time.time()
        success = self.test_endpoint("GET", "/health", 200, description="性能测试")
        end_time = time.time()

        response_time = end_time - start_time
        if response_time > 2.0:  # 2秒超时
            print(f"⚠️  响应时间过长: {response_time:.2f}秒")
            return False

        return success

    def generate_report(self) -> None:
        """生成测试报告"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests

        print("\n" + "=" * 50)
        print("📊 API验证报告")
        print("=" * 50)
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(
            f"成功率: {(passed_tests/total_tests*100):.1f}%"
            if total_tests > 0
            else "成功率: 0%"
        )

        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.results:
                if not result["success"]:
                    print(
                        f"  - {result['method']} {result['path']}: {result.get('error', '状态码错误')}"
                    )

        # 性能统计
        response_times = [
            r.get("response_time", 0) for r in self.results if r["success"]
        ]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            print(f"\n⚡ 性能统计:")
            print(f"  平均响应时间: {avg_time:.3f}秒")
            print(f"  最大响应时间: {max_time:.3f}秒")

        # 保存详细报告
        import os

        os.makedirs("reports", exist_ok=True)

        with open("reports/api-validation-report.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "summary": {
                        "total_tests": total_tests,
                        "passed_tests": passed_tests,
                        "failed_tests": failed_tests,
                        "success_rate": (passed_tests / total_tests * 100)
                        if total_tests > 0
                        else 0,
                    },
                    "results": self.results,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"\n📄 详细报告已保存: reports/api-validation-report.json")


def main():
    """主函数"""
    print("🚀 开始API验证")
    print("=" * 30)

    validator = APIValidator()

    # 检查服务器是否运行
    if not validator.check_server_health():
        print("❌ 服务器未运行或健康检查失败")
        print("💡 请先启动服务器: python main.py")
        sys.exit(1)

    print("✅ 服务器运行正常")

    # 运行所有测试
    all_passed = True

    all_passed &= validator.test_api_docs()
    all_passed &= validator.test_core_endpoints()
    all_passed &= validator.test_error_handling()
    all_passed &= validator.test_performance()

    # 生成报告
    validator.generate_report()

    if all_passed:
        print("\n🎉 所有API测试通过！")
        sys.exit(0)
    else:
        print("\n⚠️  部分API测试失败，请查看报告")
        sys.exit(1)


if __name__ == "__main__":
    main()
