#!/usr/bin/env python3
"""Gemini结构化输出演示脚本

演示如何使用Gemini进行结构化输出的文档质量分析。
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.llm.gemini_client import GeminiClient, GeminiConfig
from app.core.schemas import QualityLevel, QuickAssessmentSchema


async def demo_gemini_structured_output():
    """演示Gemini结构化输出功能"""

    # 检查API密钥
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ 请设置GEMINI_API_KEY环境变量")
        print("   export GEMINI_API_KEY=your_api_key")
        return

    print("🚀 开始Gemini结构化输出演示...")

    # 创建配置和客户端
    config = GeminiConfig(
        api_key=api_key,
        model_name="gemini-2.0-flash-exp",
        temperature=0.1,
        timeout_seconds=30,
    )

    client = GeminiClient(config)

    # 1. 健康检查
    print("\n1️⃣ 执行健康检查...")
    try:
        health_status = await client.health_check()
        if health_status["available"]:
            print(f"✅ Gemini API连接正常")
            print(f"   模型: {health_status['model_name']}")
        else:
            print(f"❌ Gemini API连接失败: {health_status.get('error', 'Unknown error')}")
            return
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return

    # 2. 示例OpenAPI文档
    sample_openapi = {
        "openapi": "3.0.0",
        "info": {"title": "简单API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {"summary": "获取用户", "responses": {"200": {"description": "成功"}}}
            },
            "/users/{id}": {
                "get": {
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "成功"},
                        "404": {"description": "未找到"},
                    },
                }
            },
        },
    }

    # 3. 结构化分析
    print("\n2️⃣ 执行结构化文档质量分析...")

    prompt = f"""
    请分析这个OpenAPI文档的质量，重点评估：

    1. 完整性：描述、参数、响应是否完整
    2. 准确性：类型定义、状态码是否正确
    3. 可读性：描述是否清晰易懂
    4. 可测试性：是否有足够信息生成测试用例

    请特别关注：
    - 端点数量和复杂度
    - 缺失的描述和示例
    - 是否需要进一步详细分析

    OpenAPI文档：
    {json.dumps(sample_openapi, ensure_ascii=False, indent=2)}
    """

    try:
        print("   正在调用Gemini API...")
        result = await client.generate_structured(
            prompt=prompt, response_schema=QuickAssessmentSchema
        )

        print("✅ 结构化分析完成！")
        print("\n📊 分析结果:")
        print(f"   端点数量: {result.endpoint_count}")
        print(f"   复杂度评分: {result.complexity_score:.2f}")
        print(f"   有质量问题: {'是' if result.has_quality_issues else '否'}")
        print(f"   需要详细分析: {'是' if result.needs_detailed_analysis else '否'}")
        print(f"   预估分析时间: {result.estimated_analysis_time}秒")
        print(f"   整体印象: {result.overall_impression}")
        print(f"   分析原因: {result.reason}")

        if result.quick_issues:
            print(f"   发现的问题:")
            for issue in result.quick_issues:
                print(f"     - {issue}")

        # 4. 验证Schema版本和时间戳
        print(f"\n🔍 Schema信息:")
        print(f"   Schema版本: {result.schema_version}")
        print(f"   生成时间: {result.generated_at}")

        # 5. 展示JSON输出
        print(f"\n📄 完整JSON输出:")
        json_output = result.model_dump_json(indent=2, ensure_ascii=False)
        print(json_output)

    except Exception as e:
        print(f"❌ 结构化分析失败: {e}")
        return

    print("\n🎉 演示完成！")
    print("\n💡 关键优势:")
    print("   ✅ 类型安全的结构化输出")
    print("   ✅ 自动JSON Schema验证")
    print("   ✅ Pydantic模型集成")
    print("   ✅ 完整的错误处理")
    print("   ✅ 版本控制和时间戳")


def main():
    """主函数"""
    print("🤖 Gemini结构化输出演示")
    print("=" * 50)

    try:
        asyncio.run(demo_gemini_structured_output())
    except KeyboardInterrupt:
        print("\n👋 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")


if __name__ == "__main__":
    main()
