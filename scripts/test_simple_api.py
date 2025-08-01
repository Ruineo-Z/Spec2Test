#!/usr/bin/env python3
"""测试简化的API接口

只测试核心功能：
1. 上传文档
2. 分析文档
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


class SimpleAPITester:
    """简化API测试器"""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"

    async def test_upload_document(self):
        """测试文档上传"""
        print("📤 测试文档上传...")

        # 创建测试文件
        test_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "简单测试API",
                "version": "1.0.0",
                "description": "用于测试的简单API",
            },
            "paths": {
                "/users": {
                    "get": {
                        "summary": "获取用户列表",
                        "responses": {
                            "200": {
                                "description": "成功返回用户列表",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "integer"},
                                                    "name": {"type": "string"},
                                                },
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    },
                    "post": {
                        "summary": "创建用户",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["name"],
                                        "properties": {"name": {"type": "string"}},
                                    }
                                }
                            },
                        },
                        "responses": {"201": {"description": "用户创建成功"}},
                    },
                }
            },
        }

        # 创建临时文件
        test_file_path = Path("/tmp/test_api.json")
        with open(test_file_path, "w", encoding="utf-8") as f:
            json.dump(test_spec, f, ensure_ascii=False, indent=2)

        async with httpx.AsyncClient() as client:
            try:
                # 上传文件
                with open(test_file_path, "rb") as f:
                    files = {"file": ("test_api.json", f, "application/json")}
                    response = await client.post(
                        f"{self.api_base}/documents/upload", files=files
                    )

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 文档上传成功")
                    print(f"   文档ID: {data['document_id']}")
                    print(f"   文档标题: {data['document_info']['title']}")
                    print(f"   端点数量: {data['document_info']['endpoint_count']}")
                    print(f"   复杂度: {data['document_info']['estimated_complexity']}")
                    print(f"   文件大小: {data['upload_info']['file_size']} bytes")

                    # 清理临时文件
                    test_file_path.unlink()

                    return data["document_id"]
                else:
                    print(f"❌ 文档上传失败: {response.status_code}")
                    print(f"   错误: {response.text}")
                    return None

            except Exception as e:
                print(f"❌ 文档上传异常: {e}")
                return None
            finally:
                # 确保清理临时文件
                if test_file_path.exists():
                    test_file_path.unlink()

    async def test_analyze_document(self, document_id: str):
        """测试文档分析"""
        print(f"\n🔍 测试文档分析 (文档ID: {document_id})...")

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.api_base}/analyses/{document_id}/analyze"
                )

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 文档分析成功")
                    print(f"   分析ID: {data['analysis_id']}")
                    print(f"   分析耗时: {data['analysis_time']:.2f}秒")
                    print(f"   质量评分: {data['analysis']['quality_score']}")
                    print(f"   质量等级: {data['analysis']['quality_level']}")

                    if data["analysis"]["issues"]:
                        print(f"   发现问题: {len(data['analysis']['issues'])}个")
                        for issue in data["analysis"]["issues"][:3]:
                            print(f"     - {issue['message']}")

                    return data["analysis_id"]
                else:
                    print(f"❌ 文档分析失败: {response.status_code}")
                    print(f"   错误: {response.text}")
                    return None

            except Exception as e:
                print(f"❌ 文档分析异常: {e}")
                return None

    async def test_query_document(self, document_id: str):
        """测试文档查询"""
        print(f"\n📋 测试文档查询 (文档ID: {document_id})...")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.api_base}/documents/{document_id}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 文档查询成功")
                    print(f"   文件名: {data['filename']}")
                    print(f"   文件大小: {data['file_size']} bytes")
                    print(f"   端点数量: {data['endpoint_count']}")
                    print(f"   状态: {data['status']}")
                    print(f"   可用操作: {data['available_actions']}")
                    return True
                else:
                    print(f"❌ 文档查询失败: {response.status_code}")
                    return False

            except Exception as e:
                print(f"❌ 文档查询异常: {e}")
                return False

    async def test_api_info(self):
        """测试API基本信息"""
        print("📋 测试API基本信息...")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.api_base}/info")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ API信息获取成功")
                    print(f"   版本: {data['version']}")
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

    async def run_simple_test(self):
        """运行简化测试"""
        print("🚀 开始简化API测试...")
        print("=" * 50)

        # 1. 测试API信息
        api_ok = await self.test_api_info()
        if not api_ok:
            print("\n❌ API基础信息获取失败，停止测试")
            return

        # 2. 测试文档上传
        document_id = await self.test_upload_document()
        if not document_id:
            print("\n❌ 文档上传失败，停止测试")
            return

        # 3. 测试文档查询
        await self.test_query_document(document_id)

        # 4. 测试文档分析（需要API密钥）
        if os.getenv("GEMINI_API_KEY"):
            analysis_id = await self.test_analyze_document(document_id)
            if analysis_id:
                print(f"\n✅ 完整流程测试成功！")
            else:
                print(f"\n⚠️  分析失败，但上传和查询正常")
        else:
            print("\n⚠️  未设置GEMINI_API_KEY，跳过文档分析测试")

        print("\n" + "=" * 50)
        print("🎉 简化API测试完成！")
        print("\n💡 核心接口:")
        print(f"   📤 上传文档: POST {self.api_base}/documents/upload")
        print(f"   🔍 分析文档: POST {self.api_base}/analyses/{{document_id}}/analyze")
        print(f"   📋 查询文档: GET {self.api_base}/documents/{{document_id}}")
        print(f"   📚 API文档: {self.base_url}/docs")


async def main():
    """主函数"""
    print("🤖 简化API测试工具")
    print("=" * 50)

    # 检查环境变量
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  提示: 未设置GEMINI_API_KEY环境变量")
        print("   文档分析功能将跳过")
        print("   如需测试分析功能，请设置: export GEMINI_API_KEY=your_api_key")
        print()

    # 创建测试器并运行测试
    tester = SimpleAPITester()

    try:
        await tester.run_simple_test()
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
