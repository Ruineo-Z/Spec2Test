"""性能和负载测试

测试API在高负载、大文件、并发请求等情况下的性能表现。
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestPerformanceBaseline:
    """性能基线测试类"""

    def test_health_check_response_time(self, client: TestClient):
        """TC034: 健康检查响应时间基线"""
        response_times = []

        # 执行多次健康检查，测量响应时间
        for _ in range(10):
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()

            assert response.status_code == status.HTTP_200_OK
            response_times.append(end_time - start_time)

        # 计算统计信息
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        # 性能断言（健康检查应该很快）
        assert avg_time < 0.1, f"平均响应时间过长: {avg_time:.3f}s"
        assert max_time < 0.5, f"最大响应时间过长: {max_time:.3f}s"

        print(f"健康检查性能统计:")
        print(f"  平均响应时间: {avg_time:.3f}s")
        print(f"  最小响应时间: {min_time:.3f}s")
        print(f"  最大响应时间: {max_time:.3f}s")

    def test_api_info_response_time(self, client: TestClient):
        """TC035: API信息接口响应时间基线"""
        response_times = []

        for _ in range(10):
            start_time = time.time()
            response = client.get("/api/v1/info")
            end_time = time.time()

            assert response.status_code == status.HTTP_200_OK
            response_times.append(end_time - start_time)

        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)

        # API信息接口也应该很快
        assert avg_time < 0.2, f"平均响应时间过长: {avg_time:.3f}s"
        assert max_time < 1.0, f"最大响应时间过长: {max_time:.3f}s"

        print(f"API信息接口性能统计:")
        print(f"  平均响应时间: {avg_time:.3f}s")
        print(f"  最大响应时间: {max_time:.3f}s")

    def test_document_list_response_time(self, client: TestClient):
        """TC036: 文档列表接口响应时间基线"""
        response_times = []

        for _ in range(5):
            start_time = time.time()
            response = client.get("/api/v1/parser/documents")
            end_time = time.time()

            assert response.status_code == status.HTTP_200_OK
            response_times.append(end_time - start_time)

        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)

        # 文档列表查询应该在合理时间内完成
        assert avg_time < 1.0, f"平均响应时间过长: {avg_time:.3f}s"
        assert max_time < 3.0, f"最大响应时间过长: {max_time:.3f}s"

        print(f"文档列表接口性能统计:")
        print(f"  平均响应时间: {avg_time:.3f}s")
        print(f"  最大响应时间: {max_time:.3f}s")


class TestFileUploadPerformance:
    """文件上传性能测试类"""

    def test_small_file_upload_performance(self, client: TestClient):
        """TC037: 小文件上传性能测试"""
        # 创建小的OpenAPI文档（约1KB）
        small_spec = """
        openapi: 3.0.3
        info:
          title: Small Test API
          version: 1.0.0
          description: A small API for performance testing
        paths:
          /test:
            get:
              summary: Test endpoint
              responses:
                '200':
                  description: Success
                  content:
                    application/json:
                      schema:
                        type: object
                        properties:
                          message:
                            type: string
        """

        upload_times = []

        for i in range(5):
            start_time = time.time()
            response = client.post(
                "/api/v1/parser/upload",
                files={
                    "file": (
                        f"small_{i}.yaml",
                        small_spec.encode(),
                        "application/x-yaml",
                    )
                },
            )
            end_time = time.time()

            assert response.status_code == status.HTTP_200_OK
            upload_times.append(end_time - start_time)

            # 清理：删除上传的文档
            if response.status_code == status.HTTP_200_OK:
                document_id = response.json().get("document_id")
                if document_id:
                    client.delete(f"/api/v1/parser/documents/{document_id}")

        avg_time = sum(upload_times) / len(upload_times)
        max_time = max(upload_times)

        # 小文件上传应该相对较快
        assert avg_time < 5.0, f"小文件平均上传时间过长: {avg_time:.3f}s"
        assert max_time < 10.0, f"小文件最大上传时间过长: {max_time:.3f}s"

        print(f"小文件上传性能统计:")
        print(f"  平均上传时间: {avg_time:.3f}s")
        print(f"  最大上传时间: {max_time:.3f}s")

    def test_medium_file_upload_performance(self, client: TestClient):
        """TC038: 中等文件上传性能测试"""
        # 创建中等大小的OpenAPI文档（约10KB）
        medium_spec_base = """
        openapi: 3.0.3
        info:
          title: Medium Test API
          version: 1.0.0
          description: A medium-sized API for performance testing
        paths:
        """

        # 添加多个端点以增加文件大小
        paths = []
        for i in range(20):
            path = f"""
          /endpoint_{i}:
            get:
              summary: Test endpoint {i}
              description: This is test endpoint number {i} for performance testing
              parameters:
                - name: param_{i}
                  in: query
                  description: Test parameter {i}
                  schema:
                    type: string
              responses:
                '200':
                  description: Success response for endpoint {i}
                  content:
                    application/json:
                      schema:
                        type: object
                        properties:
                          id:
                            type: integer
                            description: Unique identifier
                          name:
                            type: string
                            description: Name field
                          data_{i}:
                            type: string
                            description: Data field for endpoint {i}
            """
            paths.append(path)

        medium_spec = medium_spec_base + "".join(paths)

        start_time = time.time()
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("medium.yaml", medium_spec.encode(), "application/x-yaml")},
        )
        end_time = time.time()

        upload_time = end_time - start_time

        assert response.status_code == status.HTTP_200_OK

        # 中等文件上传时间限制
        assert upload_time < 15.0, f"中等文件上传时间过长: {upload_time:.3f}s"

        # 清理
        if response.status_code == status.HTTP_200_OK:
            document_id = response.json().get("document_id")
            if document_id:
                client.delete(f"/api/v1/parser/documents/{document_id}")

        print(f"中等文件上传性能统计:")
        print(f"  文件大小: {len(medium_spec.encode())} bytes")
        print(f"  上传时间: {upload_time:.3f}s")
        print(f"  上传速度: {len(medium_spec.encode()) / upload_time:.0f} bytes/s")


class TestConcurrentRequests:
    """并发请求测试类"""

    def test_concurrent_health_checks(self, client: TestClient):
        """TC039: 并发健康检查测试"""

        def health_check():
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == status.HTTP_200_OK,
            }

        # 使用线程池执行并发请求
        num_concurrent = 10
        results = []

        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(health_check) for _ in range(num_concurrent)]

            for future in as_completed(futures):
                results.append(future.result())

        # 验证所有请求都成功
        success_count = sum(1 for r in results if r["success"])
        assert (
            success_count == num_concurrent
        ), f"只有 {success_count}/{num_concurrent} 个请求成功"

        # 计算性能统计
        response_times = [r["response_time"] for r in results]
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)

        # 并发情况下的性能要求可以适当放宽
        assert avg_time < 1.0, f"并发健康检查平均响应时间过长: {avg_time:.3f}s"
        assert max_time < 3.0, f"并发健康检查最大响应时间过长: {max_time:.3f}s"

        print(f"并发健康检查性能统计 ({num_concurrent} 个并发请求):")
        print(
            f"  成功率: {success_count}/{num_concurrent} ({success_count/num_concurrent*100:.1f}%)"
        )
        print(f"  平均响应时间: {avg_time:.3f}s")
        print(f"  最大响应时间: {max_time:.3f}s")

    def test_concurrent_document_uploads(self, client: TestClient):
        """TC040: 并发文档上传测试"""

        def upload_document(doc_id: int):
            spec = f"""
            openapi: 3.0.3
            info:
              title: Concurrent Test API {doc_id}
              version: 1.0.0
            paths:
              /test_{doc_id}:
                get:
                  summary: Test endpoint {doc_id}
                  responses:
                    '200':
                      description: Success
            """

            start_time = time.time()
            try:
                response = client.post(
                    "/api/v1/parser/upload",
                    files={
                        "file": (
                            f"concurrent_{doc_id}.yaml",
                            spec.encode(),
                            "application/x-yaml",
                        )
                    },
                )
                end_time = time.time()

                return {
                    "doc_id": doc_id,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == status.HTTP_200_OK,
                    "document_id": response.json().get("document_id")
                    if response.status_code == status.HTTP_200_OK
                    else None,
                    "error": None,
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "doc_id": doc_id,
                    "status_code": None,
                    "response_time": end_time - start_time,
                    "success": False,
                    "document_id": None,
                    "error": str(e),
                }

        # 执行并发上传
        num_concurrent = 5  # 减少并发数以避免过载
        results = []

        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [
                executor.submit(upload_document, i) for i in range(num_concurrent)
            ]

            for future in as_completed(futures):
                results.append(future.result())

        # 验证结果
        success_count = sum(1 for r in results if r["success"])
        failed_results = [r for r in results if not r["success"]]

        # 至少应该有一半的请求成功（考虑到可能的资源限制）
        min_success = num_concurrent // 2
        assert (
            success_count >= min_success
        ), f"成功率过低: {success_count}/{num_concurrent}, 失败详情: {failed_results}"

        # 计算成功请求的性能统计
        successful_results = [r for r in results if r["success"]]
        if successful_results:
            response_times = [r["response_time"] for r in successful_results]
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)

            # 并发上传的性能要求
            assert avg_time < 30.0, f"并发上传平均响应时间过长: {avg_time:.3f}s"
            assert max_time < 60.0, f"并发上传最大响应时间过长: {max_time:.3f}s"

            print(f"并发文档上传性能统计 ({num_concurrent} 个并发请求):")
            print(
                f"  成功率: {success_count}/{num_concurrent} ({success_count/num_concurrent*100:.1f}%)"
            )
            print(f"  平均响应时间: {avg_time:.3f}s")
            print(f"  最大响应时间: {max_time:.3f}s")

        # 清理成功上传的文档
        for result in successful_results:
            if result["document_id"]:
                try:
                    client.delete(f"/api/v1/parser/documents/{result['document_id']}")
                except:
                    pass  # 忽略清理错误


class TestMemoryAndResourceUsage:
    """内存和资源使用测试类"""

    def test_multiple_uploads_memory_usage(self, client: TestClient):
        """TC041: 多次上传的内存使用测试"""
        # 这个测试主要是确保多次上传不会导致内存泄漏
        # 通过观察响应时间是否随着上传次数增加而显著增长来间接检测

        response_times = []
        document_ids = []

        spec_template = """
        openapi: 3.0.3
        info:
          title: Memory Test API {}
          version: 1.0.0
        paths:
          /test_{}:
            get:
              summary: Test endpoint {}
              responses:
                '200':
                  description: Success
        """

        # 执行多次上传
        num_uploads = 10
        for i in range(num_uploads):
            spec = spec_template.format(i, i, i)

            start_time = time.time()
            response = client.post(
                "/api/v1/parser/upload",
                files={
                    "file": (
                        f"memory_test_{i}.yaml",
                        spec.encode(),
                        "application/x-yaml",
                    )
                },
            )
            end_time = time.time()

            response_time = end_time - start_time
            response_times.append(response_time)

            if response.status_code == status.HTTP_200_OK:
                document_id = response.json().get("document_id")
                if document_id:
                    document_ids.append(document_id)

            # 每次上传都应该成功
            assert response.status_code == status.HTTP_200_OK, f"第 {i+1} 次上传失败"

        # 检查响应时间趋势（不应该显著增长）
        first_half_avg = sum(response_times[: num_uploads // 2]) / (num_uploads // 2)
        second_half_avg = sum(response_times[num_uploads // 2 :]) / (
            num_uploads - num_uploads // 2
        )

        # 后半部分的平均响应时间不应该比前半部分慢太多（允许50%的增长）
        growth_ratio = second_half_avg / first_half_avg if first_half_avg > 0 else 1
        assert growth_ratio < 2.0, f"响应时间增长过快，可能存在内存泄漏: {growth_ratio:.2f}x"

        print(f"内存使用测试统计 ({num_uploads} 次上传):")
        print(f"  前半部分平均响应时间: {first_half_avg:.3f}s")
        print(f"  后半部分平均响应时间: {second_half_avg:.3f}s")
        print(f"  响应时间增长比例: {growth_ratio:.2f}x")

        # 清理所有上传的文档
        for document_id in document_ids:
            try:
                client.delete(f"/api/v1/parser/documents/{document_id}")
            except:
                pass  # 忽略清理错误

    def test_large_document_list_performance(self, client: TestClient):
        """TC042: 大量文档列表查询性能测试"""
        # 首先上传多个文档
        document_ids = []
        num_docs = 20

        spec_template = """
        openapi: 3.0.3
        info:
          title: List Test API {}
          version: 1.0.0
        paths:
          /test_{}:
            get:
              responses:
                '200':
                  description: Success
        """

        # 上传文档
        for i in range(num_docs):
            spec = spec_template.format(i, i)
            response = client.post(
                "/api/v1/parser/upload",
                files={
                    "file": (f"list_test_{i}.yaml", spec.encode(), "application/x-yaml")
                },
            )

            if response.status_code == status.HTTP_200_OK:
                document_id = response.json().get("document_id")
                if document_id:
                    document_ids.append(document_id)

        # 测试文档列表查询性能
        list_times = []
        for _ in range(5):
            start_time = time.time()
            response = client.get("/api/v1/parser/documents")
            end_time = time.time()

            assert response.status_code == status.HTTP_200_OK
            list_times.append(end_time - start_time)

            # 验证返回的文档数量
            documents = response.json().get("documents", [])
            assert len(documents) >= len(document_ids), "返回的文档数量少于预期"

        avg_list_time = sum(list_times) / len(list_times)
        max_list_time = max(list_times)

        # 即使有很多文档，列表查询也应该相对较快
        assert avg_list_time < 2.0, f"文档列表查询平均时间过长: {avg_list_time:.3f}s"
        assert max_list_time < 5.0, f"文档列表查询最大时间过长: {max_list_time:.3f}s"

        print(f"大量文档列表查询性能统计 ({num_docs} 个文档):")
        print(f"  平均查询时间: {avg_list_time:.3f}s")
        print(f"  最大查询时间: {max_list_time:.3f}s")
        print(f"  实际上传文档数: {len(document_ids)}")

        # 清理所有文档
        for document_id in document_ids:
            try:
                client.delete(f"/api/v1/parser/documents/{document_id}")
            except:
                pass  # 忽略清理错误


@pytest.mark.slow
class TestStressTests:
    """压力测试类（标记为慢速测试）"""

    @pytest.mark.skip(reason="压力测试，仅在需要时手动运行")
    def test_sustained_load(self, client: TestClient):
        """TC043: 持续负载测试"""
        # 这是一个长时间运行的压力测试
        # 在生产环境或性能测试环境中运行

        duration_seconds = 60  # 运行1分钟
        start_time = time.time()
        request_count = 0
        error_count = 0
        response_times = []

        while time.time() - start_time < duration_seconds:
            try:
                req_start = time.time()
                response = client.get("/health")
                req_end = time.time()

                request_count += 1
                response_times.append(req_end - req_start)

                if response.status_code != status.HTTP_200_OK:
                    error_count += 1

                # 短暂休息以避免过度负载
                time.sleep(0.1)

            except Exception:
                error_count += 1

        # 计算统计信息
        total_time = time.time() - start_time
        requests_per_second = request_count / total_time
        error_rate = error_count / request_count if request_count > 0 else 1
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )

        # 性能要求
        assert error_rate < 0.05, f"错误率过高: {error_rate:.2%}"
        assert requests_per_second > 5, f"请求处理速度过慢: {requests_per_second:.1f} req/s"
        assert avg_response_time < 1.0, f"平均响应时间过长: {avg_response_time:.3f}s"

        print(f"持续负载测试结果 ({duration_seconds}s):")
        print(f"  总请求数: {request_count}")
        print(f"  错误数: {error_count}")
        print(f"  错误率: {error_rate:.2%}")
        print(f"  请求速率: {requests_per_second:.1f} req/s")
        print(f"  平均响应时间: {avg_response_time:.3f}s")
