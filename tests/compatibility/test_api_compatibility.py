"""API兼容性测试

测试实际API实现与test.yaml中定义的Inkflow AI小说接口规范的兼容性。
识别规范与实现之间的差异和不匹配问题。
"""

from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml
from fastapi import status
from fastapi.testclient import TestClient


class TestAPISpecificationCompatibility:
    """API规范兼容性测试类"""

    def test_openapi_version_compatibility(self, test_yaml_spec: Dict[str, Any]):
        """TC044: OpenAPI版本兼容性测试"""
        # 检查OpenAPI版本
        openapi_version = test_yaml_spec.get("openapi")
        assert openapi_version is not None, "test.yaml中缺少openapi版本声明"
        assert openapi_version.startswith("3."), f"不支持的OpenAPI版本: {openapi_version}"

        print(f"OpenAPI版本: {openapi_version}")

    def test_api_info_compatibility(
        self, client: TestClient, test_yaml_spec: Dict[str, Any]
    ):
        """TC045: API信息兼容性测试"""
        # 获取实际API信息
        response = client.get("/api/v1/info")

        if response.status_code == status.HTTP_200_OK:
            actual_info = response.json()
            spec_info = test_yaml_spec.get("info", {})

            # 比较API标题
            spec_title = spec_info.get("title")
            actual_title = actual_info.get("title")

            print(f"规范中的API标题: {spec_title}")
            print(f"实际API标题: {actual_title}")

            # 注意：这里可能不匹配，这正是我们要发现的问题
            if spec_title and actual_title:
                if spec_title != actual_title:
                    print(f"⚠️  API标题不匹配: 规范='{spec_title}' vs 实际='{actual_title}'")

            # 比较版本
            spec_version = spec_info.get("version")
            actual_version = actual_info.get("version")

            print(f"规范中的API版本: {spec_version}")
            print(f"实际API版本: {actual_version}")

            if spec_version and actual_version:
                if spec_version != actual_version:
                    print(f"⚠️  API版本不匹配: 规范='{spec_version}' vs 实际='{actual_version}'")
        else:
            print(f"⚠️  无法获取实际API信息，状态码: {response.status_code}")

    def test_inkflow_endpoints_existence(
        self, client: TestClient, test_yaml_spec: Dict[str, Any]
    ):
        """TC046: Inkflow AI小说接口端点存在性测试"""
        spec_paths = test_yaml_spec.get("paths", {})

        # 测试规范中定义的每个端点
        for path, methods in spec_paths.items():
            print(f"\n测试端点: {path}")

            for method, details in methods.items():
                method_upper = method.upper()
                print(f"  方法: {method_upper}")

                # 尝试访问端点（不提供参数，只测试端点是否存在）
                try:
                    if method_upper == "GET":
                        response = client.get(path)
                    elif method_upper == "POST":
                        response = client.post(path)
                    elif method_upper == "PUT":
                        response = client.put(path)
                    elif method_upper == "DELETE":
                        response = client.delete(path)
                    else:
                        print(f"    ⚠️  不支持的HTTP方法: {method_upper}")
                        continue

                    print(f"    状态码: {response.status_code}")

                    # 404表示端点不存在，这是我们要发现的主要问题
                    if response.status_code == status.HTTP_404_NOT_FOUND:
                        print(f"    ❌ 端点不存在: {method_upper} {path}")
                    elif response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
                        print(f"    ❌ 方法不允许: {method_upper} {path}")
                    elif response.status_code in [
                        status.HTTP_422_UNPROCESSABLE_ENTITY,
                        status.HTTP_400_BAD_REQUEST,
                    ]:
                        print(f"    ✅ 端点存在但参数错误: {method_upper} {path} (这是预期的)")
                    elif response.status_code == status.HTTP_401_UNAUTHORIZED:
                        print(f"    ✅ 端点存在但需要认证: {method_upper} {path}")
                    elif response.status_code == status.HTTP_200_OK:
                        print(f"    ✅ 端点存在且可访问: {method_upper} {path}")
                    else:
                        print(f"    ⚠️  未预期的状态码: {response.status_code}")

                except Exception as e:
                    print(f"    ❌ 请求失败: {e}")

    def test_chapter_generate_endpoint(self, client: TestClient):
        """TC047: 章节生成端点测试"""
        # 测试 /chapter/generate 端点
        endpoint = "/chapter/generate"

        # 测试端点是否存在
        response = client.post(endpoint)
        print(f"POST {endpoint} 状态码: {response.status_code}")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            print(f"❌ 章节生成端点不存在: {endpoint}")
            return

        # 如果端点存在，测试请求体格式
        test_payload = {
            "story_context": "这是一个测试故事背景",
            "character_info": "主角是一个年轻的冒险者",
            "plot_direction": "探索神秘的森林",
            "writing_style": "轻松幽默",
            "chapter_length": "medium",
        }

        response = client.post(endpoint, json=test_payload)
        print(f"带有测试数据的请求状态码: {response.status_code}")

        if response.status_code == status.HTTP_200_OK:
            print("✅ 章节生成端点正常工作")
            data = response.json()
            print(
                f"响应数据结构: {list(data.keys()) if isinstance(data, dict) else type(data)}"
            )
        elif response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST,
        ]:
            print("⚠️  章节生成端点存在但请求格式不匹配")
            try:
                error_data = response.json()
                print(f"错误详情: {error_data}")
            except:
                print(f"错误响应: {response.text}")
        else:
            print(f"⚠️  章节生成端点返回未预期状态码: {response.status_code}")

    def test_user_authentication_endpoints(self, client: TestClient):
        """TC048: 用户认证端点测试"""
        # 测试用户注册端点
        register_endpoint = "/user/register"
        response = client.post(register_endpoint)
        print(f"POST {register_endpoint} 状态码: {response.status_code}")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            print(f"❌ 用户注册端点不存在: {register_endpoint}")
        else:
            print(f"✅ 用户注册端点存在")

            # 测试注册请求格式
            test_register_data = {
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpassword123",
            }

            response = client.post(register_endpoint, json=test_register_data)
            print(f"注册测试请求状态码: {response.status_code}")

        # 测试用户登录端点
        login_endpoint = "/user/login"
        response = client.post(login_endpoint)
        print(f"POST {login_endpoint} 状态码: {response.status_code}")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            print(f"❌ 用户登录端点不存在: {login_endpoint}")
        else:
            print(f"✅ 用户登录端点存在")

            # 测试登录请求格式
            test_login_data = {"username": "testuser", "password": "testpassword123"}

            response = client.post(login_endpoint, json=test_login_data)
            print(f"登录测试请求状态码: {response.status_code}")

    def test_user_profile_endpoints(self, client: TestClient):
        """TC049: 用户资料端点测试"""
        # 测试获取用户信息端点
        profile_endpoint = "/user/profile"
        response = client.get(profile_endpoint)
        print(f"GET {profile_endpoint} 状态码: {response.status_code}")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            print(f"❌ 用户资料端点不存在: {profile_endpoint}")
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            print(f"✅ 用户资料端点存在但需要认证")
        else:
            print(f"✅ 用户资料端点存在，状态码: {response.status_code}")

    def test_creative_plan_endpoints(self, client: TestClient):
        """TC050: 创作计划端点测试"""
        # 测试保存创作计划端点
        save_plan_endpoint = "/user/creative-plans"
        response = client.post(save_plan_endpoint)
        print(f"POST {save_plan_endpoint} 状态码: {response.status_code}")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            print(f"❌ 保存创作计划端点不存在: {save_plan_endpoint}")
        else:
            print(f"✅ 保存创作计划端点存在")

        # 测试获取创作计划列表端点
        response = client.get(save_plan_endpoint)
        print(f"GET {save_plan_endpoint} 状态码: {response.status_code}")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            print(f"❌ 获取创作计划列表端点不存在: {save_plan_endpoint}")
        else:
            print(f"✅ 获取创作计划列表端点存在")

        # 测试获取特定创作计划端点
        plan_detail_endpoint = "/user/creative-plans/test-plan-id"
        response = client.get(plan_detail_endpoint)
        print(f"GET {plan_detail_endpoint} 状态码: {response.status_code}")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            print(f"❌ 获取特定创作计划端点不存在: {plan_detail_endpoint}")
        else:
            print(f"✅ 获取特定创作计划端点存在")

    def test_feedback_endpoint(self, client: TestClient):
        """TC051: 反馈端点测试"""
        feedback_endpoint = "/feedback"
        response = client.post(feedback_endpoint)
        print(f"POST {feedback_endpoint} 状态码: {response.status_code}")

        if response.status_code == status.HTTP_404_NOT_FOUND:
            print(f"❌ 反馈端点不存在: {feedback_endpoint}")
        else:
            print(f"✅ 反馈端点存在")

            # 测试反馈请求格式
            test_feedback_data = {
                "type": "bug_report",
                "content": "这是一个测试反馈",
                "user_contact": "test@example.com",
            }

            response = client.post(feedback_endpoint, json=test_feedback_data)
            print(f"反馈测试请求状态码: {response.status_code}")


class TestSecuritySchemeCompatibility:
    """安全方案兼容性测试类"""

    def test_jwt_authentication_scheme(
        self, client: TestClient, test_yaml_spec: Dict[str, Any]
    ):
        """TC052: JWT认证方案测试"""
        # 检查规范中的安全方案定义
        components = test_yaml_spec.get("components", {})
        security_schemes = components.get("securitySchemes", {})

        print("规范中定义的安全方案:")
        for scheme_name, scheme_details in security_schemes.items():
            print(f"  {scheme_name}: {scheme_details}")

        # 检查是否定义了JWT Bearer认证
        bearer_auth = security_schemes.get("BearerAuth")
        if bearer_auth:
            assert bearer_auth.get("type") == "http", "BearerAuth类型应该是http"
            assert bearer_auth.get("scheme") == "bearer", "BearerAuth方案应该是bearer"
            assert bearer_auth.get("bearerFormat") == "JWT", "Bearer格式应该是JWT"
            print("✅ JWT Bearer认证方案定义正确")
        else:
            print("⚠️  规范中未找到BearerAuth安全方案")

    def test_protected_endpoints_authentication(
        self, client: TestClient, test_yaml_spec: Dict[str, Any]
    ):
        """TC053: 受保护端点认证测试"""
        # 识别需要认证的端点
        protected_endpoints = []
        paths = test_yaml_spec.get("paths", {})

        for path, methods in paths.items():
            for method, details in methods.items():
                security = details.get("security", [])
                if security:
                    protected_endpoints.append((method.upper(), path))
                    print(f"受保护的端点: {method.upper()} {path}")

        # 测试受保护端点在没有认证时的行为
        for method, path in protected_endpoints:
            try:
                if method == "GET":
                    response = client.get(path)
                elif method == "POST":
                    response = client.post(path)
                elif method == "PUT":
                    response = client.put(path)
                elif method == "DELETE":
                    response = client.delete(path)
                else:
                    continue

                print(f"  {method} {path} 无认证状态码: {response.status_code}")

                # 受保护的端点应该返回401或403
                if response.status_code == status.HTTP_404_NOT_FOUND:
                    print(f"    ❌ 端点不存在")
                elif response.status_code in [
                    status.HTTP_401_UNAUTHORIZED,
                    status.HTTP_403_FORBIDDEN,
                ]:
                    print(f"    ✅ 正确拒绝未认证请求")
                else:
                    print(f"    ⚠️  未预期的状态码，可能缺少认证保护")

            except Exception as e:
                print(f"    ❌ 请求失败: {e}")


class TestResponseSchemaCompatibility:
    """响应模式兼容性测试类"""

    def test_health_check_response_schema(
        self, client: TestClient, test_yaml_spec: Dict[str, Any]
    ):
        """TC054: 健康检查响应模式测试"""
        # 检查规范中是否定义了健康检查端点
        paths = test_yaml_spec.get("paths", {})
        health_path = paths.get("/health")

        if health_path:
            print("✅ 规范中定义了/health端点")

            # 获取实际健康检查响应
            response = client.get("/health")
            if response.status_code == status.HTTP_200_OK:
                actual_data = response.json()
                print(f"实际健康检查响应: {actual_data}")

                # 检查响应结构是否符合规范
                get_details = health_path.get("get", {})
                responses = get_details.get("responses", {})
                success_response = responses.get("200", {})

                if success_response:
                    print("规范中定义了200响应")
                    content = success_response.get("content", {})
                    json_content = content.get("application/json", {})
                    schema = json_content.get("schema", {})

                    if schema:
                        print(f"规范中的响应模式: {schema}")
                        # 这里可以进一步验证实际响应是否符合模式
            else:
                print(f"⚠️  健康检查端点返回状态码: {response.status_code}")
        else:
            print("⚠️  规范中未定义/health端点")

            # 但实际API可能有健康检查
            response = client.get("/health")
            if response.status_code == status.HTTP_200_OK:
                print("✅ 实际API有健康检查端点，但规范中未定义")
                actual_data = response.json()
                print(f"实际健康检查响应: {actual_data}")

    def test_error_response_consistency(self, client: TestClient):
        """TC055: 错误响应一致性测试"""
        # 测试不同端点的错误响应格式是否一致
        error_responses = []

        # 测试404错误
        response = client.get("/nonexistent-endpoint")
        if response.status_code == status.HTTP_404_NOT_FOUND:
            try:
                error_data = response.json()
                error_responses.append(("404", error_data))
                print(f"404错误响应格式: {error_data}")
            except:
                print("404错误响应不是JSON格式")

        # 测试405错误（方法不允许）
        response = client.post("/health")  # 健康检查通常只支持GET
        if response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            try:
                error_data = response.json()
                error_responses.append(("405", error_data))
                print(f"405错误响应格式: {error_data}")
            except:
                print("405错误响应不是JSON格式")

        # 测试422错误（请求体验证错误）
        response = client.post("/api/v1/parser/upload", json={"invalid": "data"})
        if response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            try:
                error_data = response.json()
                error_responses.append(("422", error_data))
                print(f"422错误响应格式: {error_data}")
            except:
                print("422错误响应不是JSON格式")

        # 分析错误响应格式的一致性
        if len(error_responses) > 1:
            first_format = (
                set(error_responses[0][1].keys())
                if isinstance(error_responses[0][1], dict)
                else None
            )

            consistent = True
            for status_code, error_data in error_responses[1:]:
                if isinstance(error_data, dict):
                    current_format = set(error_data.keys())
                    if current_format != first_format:
                        consistent = False
                        print(f"⚠️  {status_code}错误响应格式与其他不一致")
                else:
                    consistent = False
                    print(f"⚠️  {status_code}错误响应不是字典格式")

            if consistent:
                print("✅ 错误响应格式一致")
            else:
                print("❌ 错误响应格式不一致")


class TestDataModelCompatibility:
    """数据模型兼容性测试类"""

    def test_component_schemas_validation(self, test_yaml_spec: Dict[str, Any]):
        """TC056: 组件模式验证测试"""
        components = test_yaml_spec.get("components", {})
        schemas = components.get("schemas", {})

        print(f"规范中定义的数据模型数量: {len(schemas)}")

        for schema_name, schema_details in schemas.items():
            print(f"\n数据模型: {schema_name}")
            print(f"  类型: {schema_details.get('type', '未定义')}")

            properties = schema_details.get("properties", {})
            required = schema_details.get("required", [])

            print(f"  属性数量: {len(properties)}")
            print(f"  必需属性: {required}")

            # 检查属性定义的完整性
            for prop_name, prop_details in properties.items():
                prop_type = prop_details.get("type")
                prop_description = prop_details.get("description")

                if not prop_type:
                    print(f"    ⚠️  属性 {prop_name} 缺少类型定义")
                if not prop_description:
                    print(f"    ⚠️  属性 {prop_name} 缺少描述")

    def test_request_response_model_consistency(self, test_yaml_spec: Dict[str, Any]):
        """TC057: 请求响应模型一致性测试"""
        paths = test_yaml_spec.get("paths", {})

        for path, methods in paths.items():
            for method, details in methods.items():
                print(f"\n检查端点: {method.upper()} {path}")

                # 检查请求体模式
                request_body = details.get("requestBody")
                if request_body:
                    content = request_body.get("content", {})
                    json_content = content.get("application/json", {})
                    request_schema = json_content.get("schema")

                    if request_schema:
                        print(
                            f"  请求体模式: {request_schema.get('$ref', request_schema.get('type', '内联定义'))}"
                        )
                    else:
                        print("  ⚠️  请求体缺少模式定义")

                # 检查响应模式
                responses = details.get("responses", {})
                for status_code, response_details in responses.items():
                    content = response_details.get("content", {})
                    json_content = content.get("application/json", {})
                    response_schema = json_content.get("schema")

                    if response_schema:
                        print(
                            f"  {status_code}响应模式: {response_schema.get('$ref', response_schema.get('type', '内联定义'))}"
                        )
                    else:
                        print(f"  ⚠️  {status_code}响应缺少模式定义")
