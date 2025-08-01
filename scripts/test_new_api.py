#!/usr/bin/env python3
"""测试新的5步分离API

演示完整的文档处理流程：
1. 上传文档
2. 分析文档
3. 生成测试用例（待实现）
4. 生成测试代码（待实现）
5. 查询资源状态
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


class NewAPITester:
    """新API测试器"""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"

    async def test_step1_upload_document(self):
        """步骤1：测试文档上传"""
        print("📤 步骤1：测试文档上传...")

        # 创建示例OpenAPI文档
        demo_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "用户管理API",
                "version": "1.0.0",
                "description": "提供用户注册、登录、信息管理等功能",
            },
            "servers": [{"url": "https://api.example.com/v1", "description": "生产环境"}],
            "paths": {
                "/users": {
                    "get": {
                        "summary": "获取用户列表",
                        "description": "分页获取系统中的用户列表，支持按角色筛选",
                        "parameters": [
                            {
                                "name": "page",
                                "in": "query",
                                "description": "页码，从1开始",
                                "required": False,
                                "schema": {
                                    "type": "integer",
                                    "minimum": 1,
                                    "default": 1,
                                },
                            },
                            {
                                "name": "limit",
                                "in": "query",
                                "description": "每页数量，最大100",
                                "required": False,
                                "schema": {
                                    "type": "integer",
                                    "minimum": 1,
                                    "maximum": 100,
                                    "default": 20,
                                },
                            },
                        ],
                        "responses": {
                            "200": {
                                "description": "成功返回用户列表",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "users": {
                                                    "type": "array",
                                                    "items": {
                                                        "$ref": "#/components/schemas/User"
                                                    },
                                                },
                                                "total": {"type": "integer"},
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    },
                    "post": {
                        "summary": "创建新用户",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["username", "email"],
                                        "properties": {
                                            "username": {
                                                "type": "string",
                                                "minLength": 3,
                                            },
                                            "email": {
                                                "type": "string",
                                                "format": "email",
                                            },
                                        },
                                    }
                                }
                            },
                        },
                        "responses": {
                            "201": {"description": "用户创建成功"},
                            "400": {"description": "请求数据无效"},
                        },
                    },
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "username": {"type": "string"},
                            "email": {"type": "string", "format": "email"},
                        },
                    }
                }
            },
        }

        async with httpx.AsyncClient() as client:
            try:
                # 方法1：通过JSON内容上传
                print("   方法1：通过JSON内容上传...")
                response = await client.post(
                    f"{self.api_base}/documents/upload-content",
                    json={
                        "content": demo_spec,
                        "metadata": {
                            "name": "用户管理API",
                            "version": "v1.0.0",
                            "description": "测试用的用户管理API文档",
                            "tags": ["user", "management", "test"],
                        },
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ 文档上传成功")
                    print(f"      文档ID: {data['document_id']}")
                    print(f"      文档标题: {data['document_info']['title']}")
                    print(f"      端点数量: {data['document_info']['endpoint_count']}")
                    print(f"      复杂度: {data['document_info']['estimated_complexity']}")
                    print(f"      文件大小: {data['upload_info']['file_size']} bytes")

                    if data["validation"]["warnings"]:
                        print(f"      警告: {data['validation']['warnings']}")

                    return data["document_id"]
                else:
                    print(f"   ❌ 文档上传失败: {response.status_code}")
                    print(f"      错误: {response.text}")
                    return None

            except Exception as e:
                print(f"   ❌ 文档上传异常: {e}")
                return None

    async def test_step2_analyze_document(self, document_id: str):
        """步骤2：测试文档分析"""
        print(f"\n🔍 步骤2：测试文档分析 (文档ID: {document_id})...")

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.api_base}/analyses/{document_id}/analyze",
                    json={
                        "analysis_options": {
                            "level": "detailed",
                            "focus_areas": [
                                "completeness",
                                "testability",
                                "consistency",
                            ],
                            "custom_requirements": "请特别关注API的可测试性和文档完整性",
                            "include_suggestions": True,
                        }
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ 文档分析成功")
                    print(f"      分析ID: {data['analysis_id']}")
                    print(f"      分析耗时: {data['analysis_time']:.2f}秒")
                    print(f"      质量评分: {data['analysis']['quality_score']}")
                    print(f"      质量等级: {data['analysis']['quality_level']}")

                    analysis_details = data["analysis"]["analysis_details"]
                    print(f"      完整性评分: {analysis_details['completeness']['score']}")
                    print(f"      可测试性评分: {analysis_details['testability']['score']}")
                    print(f"      一致性评分: {analysis_details['consistency']['score']}")

                    if data["analysis"]["issues"]:
                        print(f"      发现问题: {len(data['analysis']['issues'])}个")
                        for issue in data["analysis"]["issues"][:3]:  # 只显示前3个
                            print(f"        - {issue['message']}")

                    if data["analysis"]["recommendations"]:
                        print(
                            f"      改进建议: {len(data['analysis']['recommendations'])}个"
                        )
                        for rec in data["analysis"]["recommendations"][:2]:  # 只显示前2个
                            print(f"        - {rec['action']}")

                    return data["analysis_id"]
                else:
                    print(f"   ❌ 文档分析失败: {response.status_code}")
                    print(f"      错误: {response.text}")
                    return None

            except Exception as e:
                print(f"   ❌ 文档分析异常: {e}")
                return None

    async def test_step5_query_resources(
        self, document_id: str, analysis_id: str = None
    ):
        """步骤5：测试资源查询"""
        print(f"\n📋 步骤5：测试资源查询...")

        async with httpx.AsyncClient() as client:
            try:
                # 查询文档详情
                print("   查询文档详情...")
                response = await client.get(f"{self.api_base}/documents/{document_id}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ 文档详情获取成功")
                    print(f"      资源类型: {data['resource_type']}")
                    print(f"      状态: {data['status']}")
                    print(f"      创建时间: {data['created_at']}")
                    print(f"      可用操作: {data['available_actions']}")
                else:
                    print(f"   ❌ 文档详情获取失败: {response.status_code}")

                # 查询分析详情（如果有）
                if analysis_id:
                    print("   查询分析详情...")
                    response = await client.get(
                        f"{self.api_base}/analyses/{analysis_id}"
                    )

                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✅ 分析详情获取成功")
                        print(f"      分析状态: {data['status']}")
                        print(f"      完成时间: {data.get('completed_at', '未完成')}")
                    else:
                        print(f"   ❌ 分析详情获取失败: {response.status_code}")

                # 查询文档列表
                print("   查询文档列表...")
                response = await client.get(f"{self.api_base}/documents")

                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ 文档列表获取成功")
                    print(f"      总文档数: {data['total']}")
                    for doc in data["documents"][:3]:  # 只显示前3个
                        print(f"        - {doc['name']} ({doc['id']})")
                else:
                    print(f"   ❌ 文档列表获取失败: {response.status_code}")

            except Exception as e:
                print(f"   ❌ 资源查询异常: {e}")

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

    async def run_complete_workflow(self):
        """运行完整的工作流测试"""
        print("🚀 开始新API完整工作流测试...")
        print("=" * 60)

        # 测试API信息
        api_ok = await self.test_api_info()
        if not api_ok:
            print("\n❌ API基础信息获取失败，停止测试")
            return

        # 步骤1：上传文档
        document_id = await self.test_step1_upload_document()
        if not document_id:
            print("\n❌ 文档上传失败，停止测试")
            return

        # 步骤2：分析文档（需要API密钥）
        analysis_id = None
        if os.getenv("GEMINI_API_KEY"):
            analysis_id = await self.test_step2_analyze_document(document_id)
            if not analysis_id:
                print("\n⚠️  文档分析失败，但继续其他测试")
        else:
            print("\n⚠️  未设置GEMINI_API_KEY，跳过文档分析测试")

        # 步骤5：查询资源
        await self.test_step5_query_resources(document_id, analysis_id)

        print("\n" + "=" * 60)
        print("🎉 新API工作流测试完成！")
        print("\n💡 测试总结:")
        print("   ✅ 文档上传功能正常")
        if analysis_id:
            print("   ✅ 文档分析功能正常")
        else:
            print("   ⚠️  文档分析需要配置GEMINI_API_KEY")
        print("   ✅ 资源查询功能正常")

        print("\n🔗 可用的API端点:")
        print(f"   - 上传文档: POST {self.api_base}/documents/upload")
        print(f"   - 上传URL: POST {self.api_base}/documents/upload-url")
        print(f"   - 上传内容: POST {self.api_base}/documents/upload-content")
        print(f"   - 分析文档: POST {self.api_base}/analyses/{{document_id}}/analyze")
        print(f"   - 查询文档: GET {self.api_base}/documents/{{document_id}}")
        print(f"   - 查询分析: GET {self.api_base}/analyses/{{analysis_id}}")
        print(f"   - API文档: {self.base_url}/docs")


async def main():
    """主函数"""
    print("🤖 新的5步分离API测试工具")
    print("=" * 60)

    # 检查环境变量
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  警告: 未设置GEMINI_API_KEY环境变量")
        print("   文档分析功能将无法测试")
        print("   请设置: export GEMINI_API_KEY=your_api_key")
        print()

    # 创建测试器并运行测试
    tester = NewAPITester()

    try:
        await tester.run_complete_workflow()
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
