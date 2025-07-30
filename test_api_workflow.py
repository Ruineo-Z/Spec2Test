#!/usr/bin/env python3
"""
测试API工作流程脚本

该脚本将测试完整的API流程：
1. 上传OpenAPI文档
2. 解析文档
3. 生成测试用例
4. 生成测试代码

注意：不会执行测试代码，因为这是测试文档，没有真实的接口服务
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from loguru import logger

# 清除代理环境变量以避免SOCKS问题
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("all_proxy", None)
os.environ.pop("ALL_PROXY", None)


class APIWorkflowTester:
    """API工作流程测试器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_prefix = "/api/v1"
        # 创建HTTP客户端，明确禁用代理
        transport = httpx.AsyncHTTPTransport(proxy=None)
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0), transport=transport
        )

        # 存储各步骤的结果
        self.document_id: Optional[str] = None
        self.test_suite_id: Optional[str] = None
        self.code_project_id: Optional[str] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def check_health(self) -> bool:
        """检查服务健康状态"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                logger.info("✅ 服务健康检查通过")
                return True
            else:
                logger.error(f"❌ 服务健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 无法连接到服务: {e}")
            return False

    async def upload_document(self, file_path: str) -> Dict[str, Any]:
        """步骤1: 上传并解析OpenAPI文档"""
        logger.info(f"📤 开始上传文档: {file_path}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文档文件不存在: {file_path}")

        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "application/x-yaml")}

            response = await self.client.post(
                f"{self.base_url}{self.api_prefix}/parser/upload", files=files
            )

        if response.status_code == 200:
            result = response.json()
            self.document_id = result.get("document_id")
            logger.info(f"✅ 文档上传成功，文档ID: {self.document_id}")
            logger.info(f"📊 解析结果: {result.get('summary', {})}")
            return result
        else:
            logger.error(f"❌ 文档上传失败: {response.status_code} - {response.text}")
            raise Exception(f"文档上传失败: {response.text}")

    async def analyze_document(self) -> Dict[str, Any]:
        """步骤2: 分析文档质量（可选）"""
        if not self.document_id:
            raise ValueError("需要先上传文档")

        logger.info(f"🔍 开始分析文档质量: {self.document_id}")

        response = await self.client.get(
            f"{self.base_url}{self.api_prefix}/parser/analyze/{self.document_id}"
        )

        if response.status_code == 200:
            result = response.json()
            logger.info("✅ 文档质量分析完成")
            logger.info(f"📈 质量评分: {result.get('quality_score', 'N/A')}")
            return result
        else:
            logger.error(f"❌ 文档分析失败: {response.status_code} - {response.text}")
            raise Exception(f"文档分析失败: {response.text}")

    async def generate_test_cases(
        self,
        endpoint_paths: Optional[list] = None,
        test_types: Optional[list] = None,
        max_cases_per_endpoint: int = 5,
    ) -> Dict[str, Any]:
        """步骤3: 生成测试用例"""
        if not self.document_id:
            raise ValueError("需要先上传文档")

        logger.info("🧪 开始生成测试用例")

        # 默认测试类型
        if test_types is None:
            test_types = ["normal", "error", "edge"]

        request_data = {
            "document_id": self.document_id,
            "test_types": test_types,
            "max_cases_per_endpoint": max_cases_per_endpoint,
            "include_edge_cases": True,
            "include_security_tests": True,
        }

        if endpoint_paths:
            request_data["endpoint_paths"] = endpoint_paths

        response = await self.client.post(
            f"{self.base_url}{self.api_prefix}/generator/test-cases", json=request_data
        )

        if response.status_code == 200:
            result = response.json()
            self.test_suite_id = result.get("test_suite_id")
            logger.info(f"✅ 测试用例生成成功，测试套件ID: {self.test_suite_id}")
            logger.info(f"📝 生成了 {len(result.get('test_cases', []))} 个测试用例")

            # 显示生成的测试用例概览
            for i, test_case in enumerate(result.get("test_cases", [])[:3]):
                logger.info(
                    f"   {i+1}. {test_case.get('name', 'N/A')} - {test_case.get('test_type', 'N/A')}"
                )
            if len(result.get("test_cases", [])) > 3:
                logger.info(f"   ... 还有 {len(result.get('test_cases', [])) - 3} 个测试用例")

            return result
        else:
            logger.error(f"❌ 测试用例生成失败: {response.status_code} - {response.text}")
            raise Exception(f"测试用例生成失败: {response.text}")

    async def generate_test_code(
        self, framework: str = "pytest", base_url: str = "https://api.inkflow.ai/v1"
    ) -> Dict[str, Any]:
        """步骤4: 生成测试代码"""
        if not self.test_suite_id:
            raise ValueError("需要先生成测试用例")

        logger.info(f"💻 开始生成测试代码 (框架: {framework})")

        request_data = {
            "test_suite_id": self.test_suite_id,
            "framework": framework,
            "include_setup_teardown": True,
            "base_url": base_url,
            "auth_config": {"type": "bearer", "token_endpoint": "/user/login"},
        }

        response = await self.client.post(
            f"{self.base_url}{self.api_prefix}/generator/code", json=request_data
        )

        if response.status_code == 200:
            result = response.json()
            self.code_project_id = result.get("code_project_id")
            logger.info(f"✅ 测试代码生成成功，代码项目ID: {self.code_project_id}")
            generated_files = result.get("generated_files", [])
            file_names = [f.get("path", "unknown") for f in generated_files]
            logger.info(f"📁 生成的文件: {', '.join(file_names)}")
            logger.info(
                f"📦 项目结构: {result.get('project_structure', {}).get('framework', 'N/A')} 框架"
            )
            logger.info(
                f"📏 总文件大小: {result.get('project_structure', {}).get('total_size', 0)} 字节"
            )
            return result
        else:
            logger.error(f"❌ 测试代码生成失败: {response.status_code} - {response.text}")
            raise Exception(f"测试代码生成失败: {response.text}")

    async def get_documents_list(self) -> Dict[str, Any]:
        """获取已上传的文档列表"""
        logger.info("📋 获取文档列表")

        response = await self.client.get(
            f"{self.base_url}{self.api_prefix}/parser/documents"
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"📄 找到 {len(result.get('documents', []))} 个文档")
            return result
        else:
            logger.error(f"❌ 获取文档列表失败: {response.status_code} - {response.text}")
            raise Exception(f"获取文档列表失败: {response.text}")

    async def run_complete_workflow(self, yaml_file_path: str) -> Dict[str, Any]:
        """运行完整的工作流程"""
        logger.info("🚀 开始完整的API工作流程测试")
        logger.info("=" * 50)

        results = {}

        try:
            # 检查服务健康状态
            if not await self.check_health():
                raise Exception("服务不可用")

            # 步骤1: 上传文档
            logger.info("\n📤 步骤1: 上传并解析文档")
            upload_result = await self.upload_document(yaml_file_path)
            results["upload"] = upload_result

            # 步骤2: 分析文档质量
            logger.info("\n🔍 步骤2: 分析文档质量")
            analyze_result = await self.analyze_document()
            results["analyze"] = analyze_result

            # 步骤3: 生成测试用例
            logger.info("\n🧪 步骤3: 生成测试用例")
            test_cases_result = await self.generate_test_cases()
            results["test_cases"] = test_cases_result

            # 步骤4: 生成测试代码
            logger.info("\n💻 步骤4: 生成测试代码")
            test_code_result = await self.generate_test_code()
            results["test_code"] = test_code_result

            # 获取文档列表
            logger.info("\n📋 获取文档列表")
            documents_result = await self.get_documents_list()
            results["documents"] = documents_result

            logger.info("\n" + "=" * 50)
            logger.info("🎉 完整工作流程测试成功完成！")
            logger.info(f"📊 最终结果:")
            logger.info(f"   - 文档ID: {self.document_id}")
            logger.info(f"   - 测试套件ID: {self.test_suite_id}")
            logger.info(f"   - 代码项目ID: {self.code_project_id}")

            return results

        except Exception as e:
            logger.error(f"❌ 工作流程执行失败: {e}")
            raise


async def main():
    """主函数"""
    # 配置日志
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO",
    )

    # 测试文档路径
    yaml_file_path = "/Users/augenstern/development/personal/Spec2Test/test.yaml"

    if not os.path.exists(yaml_file_path):
        logger.error(f"❌ 测试文档不存在: {yaml_file_path}")
        return

    async with APIWorkflowTester() as tester:
        try:
            results = await tester.run_complete_workflow(yaml_file_path)

            # 保存结果到文件
            output_file = "api_workflow_test_results.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"\n💾 测试结果已保存到: {output_file}")

        except Exception as e:
            logger.error(f"❌ 测试失败: {e}")
            return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))
