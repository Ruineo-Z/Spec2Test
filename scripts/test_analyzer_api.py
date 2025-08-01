#!/usr/bin/env python3
"""测试AI文档分析API

演示如何通过HTTP接口调用Gemini文档分析功能。
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class AnalyzerAPITester:
    """AI分析API测试器"""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1/analyzer"

    async def test_health_check(self):
        """测试健康检查"""
        print("🔍 测试健康检查...")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.api_base}/health")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 健康检查成功")
                    print(f"   Gemini可用: {data['gemini_available']}")
                    print(f"   模型名称: {data['model_name']}")
                    if data.get("test_response"):
                        print(f"   测试响应: {data['test_response']}")
                    return True
                else:
                    print(f"❌ 健康检查失败: {response.status_code}")
                    print(f"   响应: {response.text}")
                    return False

            except Exception as e:
                print(f"❌ 健康检查异常: {e}")
                return False

    async def get_demo_spec(self):
        """获取演示文档"""
        print("\n📄 获取演示OpenAPI文档...")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.api_base}/demo-spec")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 获取演示文档成功")
                    spec = data["spec"]
                    print(f"   文档标题: {spec['info']['title']}")
                    print(f"   文档版本: {spec['info']['version']}")
                    print(f"   端点数量: {len(spec['paths'])}")
                    return spec
                else:
                    print(f"❌ 获取演示文档失败: {response.status_code}")
                    return None

            except Exception as e:
                print(f"❌ 获取演示文档异常: {e}")
                return None

    async def test_analyze_document(self, openapi_spec: dict):
        """测试文档分析"""
        print("\n🤖 测试AI文档分析...")

        request_data = {
            "openapi_spec": openapi_spec,
            "analysis_type": "quick",
            "custom_requirements": "请特别关注API的可测试性和文档完整性",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                print("   正在调用分析API...")
                response = await client.post(
                    f"{self.api_base}/analyze", json=request_data
                )

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 文档分析成功")
                    print(f"   分析耗时: {data['analysis_time_seconds']:.2f}秒")
                    print(f"   端点数量: {data['endpoint_count']}")
                    print(f"   复杂度评分: {data['complexity_score']:.2f}")
                    print(f"   有质量问题: {'是' if data['has_quality_issues'] else '否'}")
                    print(
                        f"   需要详细分析: {'是' if data['needs_detailed_analysis'] else '否'}"
                    )
                    print(f"   整体印象: {data['overall_impression']}")
                    print(f"   使用模型: {data['gemini_model']}")

                    if data["quick_issues"]:
                        print(f"   发现的问题:")
                        for issue in data["quick_issues"]:
                            print(f"     - {issue}")

                    return data
                else:
                    print(f"❌ 文档分析失败: {response.status_code}")
                    print(f"   错误信息: {response.text}")
                    return None

            except Exception as e:
                print(f"❌ 文档分析异常: {e}")
                return None

    async def test_api_info(self):
        """测试API信息"""
        print("\n📋 测试API信息...")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/v1/info")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ API信息获取成功")
                    print(f"   版本: {data['version']}")
                    print(f"   描述: {data['description']}")
                    print(f"   可用端点:")
                    for endpoint, desc in data["endpoints"].items():
                        print(f"     - {endpoint}: {desc}")
                    return True
                else:
                    print(f"❌ API信息获取失败: {response.status_code}")
                    return False

            except Exception as e:
                print(f"❌ API信息获取异常: {e}")
                return False

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始API测试...")
        print("=" * 60)

        # 1. 测试API信息
        await self.test_api_info()

        # 2. 测试健康检查
        health_ok = await self.test_health_check()
        if not health_ok:
            print("\n❌ 健康检查失败，跳过后续测试")
            return

        # 3. 获取演示文档
        demo_spec = await self.get_demo_spec()
        if not demo_spec:
            print("\n❌ 无法获取演示文档，跳过分析测试")
            return

        # 4. 测试文档分析
        analysis_result = await self.test_analyze_document(demo_spec)

        print("\n" + "=" * 60)
        if analysis_result:
            print("🎉 所有测试完成！AI文档分析功能正常工作")
            print("\n💡 你可以通过以下方式使用API:")
            print(f"   1. 健康检查: GET {self.api_base}/health")
            print(f"   2. 获取演示文档: GET {self.api_base}/demo-spec")
            print(f"   3. 分析文档: POST {self.api_base}/analyze")
            print(f"   4. 分析文件: POST {self.api_base}/analyze-file")
            print(f"   5. API文档: {self.base_url}/docs")
        else:
            print("❌ 测试失败，请检查配置和日志")


async def main():
    """主函数"""
    print("🤖 AI文档分析API测试工具")
    print("=" * 60)

    # 检查环境变量
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  警告: 未设置GEMINI_API_KEY环境变量")
        print("   某些功能可能无法正常工作")
        print("   请设置: export GEMINI_API_KEY=your_api_key")
        print()

    # 创建测试器并运行测试
    tester = AnalyzerAPITester()

    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
