"""
Google Gemini LLM客户端

基于Google Generative AI SDK的Gemini客户端实现。
"""

import json
import time
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from .base import BaseLLMClient, LLMResponse, LLMError
from ..utils.logger import get_logger


class GeminiClient(BaseLLMClient):
    """Google Gemini客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化Gemini客户端
        
        Args:
            config: 配置字典，包含：
                - api_key: Gemini API密钥
                - model: 模型名称，默认为gemini-pro
                - temperature: 温度参数，默认0.3
                - max_tokens: 最大token数，默认4000
                - timeout: 超时时间，默认30秒
        """
        super().__init__(config)
        self.logger = get_logger(f"{self.__class__.__name__}")
        
        # 获取配置
        self.api_key = config.get("api_key")
        self.model_name = config.get("model", "gemini-pro")
        self.temperature = config.get("temperature", 0.3)
        self.max_tokens = config.get("max_tokens", 4000)
        self.timeout = config.get("timeout", 30)
        
        if not self.api_key:
            raise LLMError("Gemini API密钥未配置")
        
        try:
            # 配置API密钥
            genai.configure(api_key=self.api_key)
            
            # 初始化模型
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            )
            
            self.logger.info(f"Gemini客户端初始化成功: {self.model_name}")
            
        except Exception as e:
            error_msg = f"Gemini客户端初始化失败: {str(e)}"
            self.logger.error(error_msg)
            raise LLMError(error_msg)
    
    def generate_text(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本
        
        Args:
            prompt: 输入提示词
            **kwargs: 其他参数
                - schema: JSON Schema（用于结构化输出）
                - temperature: 临时温度设置
                - max_tokens: 临时最大token设置
        
        Returns:
            LLMResponse: 生成的响应
        """
        try:
            start_time = time.time()
            
            # 处理结构化输出
            schema = kwargs.get("schema")
            if schema:
                prompt = self._build_structured_prompt(prompt, schema)
            
            # 临时参数覆盖
            temp_temperature = kwargs.get("temperature", self.temperature)
            temp_max_tokens = kwargs.get("max_tokens", self.max_tokens)
            
            # 更新生成配置
            generation_config = genai.types.GenerationConfig(
                temperature=temp_temperature,
                max_output_tokens=temp_max_tokens,
            )
            
            # 安全设置（允许所有内容，避免过度审查）
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            self.logger.debug(f"发送Gemini请求: {len(prompt)}字符")
            
            # 调用Gemini API
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # 检查响应
            if not response.text:
                if response.prompt_feedback:
                    error_msg = f"Gemini请求被阻止: {response.prompt_feedback}"
                    self.logger.error(error_msg)
                    raise LLMError(error_msg)
                else:
                    error_msg = "Gemini返回空响应"
                    self.logger.error(error_msg)
                    raise LLMError(error_msg)
            
            duration = time.time() - start_time
            
            # 创建响应对象
            llm_response = LLMResponse(
                content=response.text,
                model=self.model_name,
                usage={
                    "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
                    "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
                },
                response_time=duration
            )
            
            self.logger.debug(f"Gemini响应成功: {duration:.2f}秒, {len(response.text)}字符")
            return llm_response
            
        except Exception as e:
            error_msg = f"Gemini文本生成失败: {str(e)}"
            self.logger.error(error_msg)
            raise LLMError(error_msg)
    
    def _build_structured_prompt(self, prompt: str, schema: Dict[str, Any]) -> str:
        """构建结构化输出提示词
        
        Args:
            prompt: 原始提示词
            schema: JSON Schema
            
        Returns:
            str: 增强的提示词
        """
        schema_str = json.dumps(schema, indent=2, ensure_ascii=False)
        
        structured_prompt = f"""{prompt}

请严格按照以下JSON Schema格式返回结果：

```json
{schema_str}
```

重要要求：
1. 返回的内容必须是有效的JSON格式
2. 必须符合上述Schema的结构和类型要求
3. 不要包含任何JSON代码块标记（```json 或 ```）
4. 直接返回JSON对象，不要添加额外的解释文字

请开始生成："""
        
        return structured_prompt
    
    def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """生成对话（将消息转换为单个提示词）
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 生成的响应
        """
        # 将消息转换为单个提示词
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"系统指令: {content}")
            elif role == "user":
                prompt_parts.append(f"用户: {content}")
            elif role == "assistant":
                prompt_parts.append(f"助手: {content}")
        
        prompt = "\n\n".join(prompt_parts)
        return self.generate_text(prompt, **kwargs)
    
    def test_connection(self) -> bool:
        """测试连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            response = self.generate_text("Hello", max_tokens=10)
            return response.content is not None
        except Exception as e:
            self.logger.error(f"Gemini连接测试失败: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息

        Returns:
            Dict[str, Any]: 模型信息
        """
        return {
            "provider": "gemini",
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "supports_streaming": False,
            "supports_functions": False,
            "supports_vision": self.model_name in ["gemini-pro-vision"],
        }

    # 实现抽象方法
    def _get_provider(self) -> str:
        """获取提供商名称"""
        return "gemini"

    def analyze_document(self, document: str, **kwargs) -> Dict[str, Any]:
        """分析文档"""
        prompt = f"请分析以下文档：\n\n{document}"
        response = self.generate_text(prompt, **kwargs)
        return {"analysis": response.content}

    def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """生成结构化内容"""
        response = self.generate_text(prompt, schema=schema, **kwargs)
        try:
            import json
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"content": response.content}

    def generate_test_cases(self, api_spec: str, **kwargs) -> List[Dict[str, Any]]:
        """生成测试用例"""
        prompt = f"为以下API规范生成测试用例：\n\n{api_spec}"
        response = self.generate_text(prompt, **kwargs)
        return [{"test_case": response.content}]

    def validate_response(self, response: str, expected_format: str, **kwargs) -> bool:
        """验证响应格式"""
        prompt = f"验证以下响应是否符合格式 '{expected_format}'：\n\n{response}"
        response = self.generate_text(prompt, **kwargs)
        return "是" in response.content or "yes" in response.content.lower()


class GeminiLangChainClient(BaseLLMClient):
    """Gemini LangChain客户端（如果需要LangChain集成）"""

    def __init__(self, config: Dict[str, Any]):
        """初始化Gemini LangChain客户端"""
        super().__init__(config)
        self.logger = get_logger(f"{self.__class__.__name__}")

        # 目前直接使用原生客户端
        self.native_client = GeminiClient(config)
        self.logger.info("Gemini LangChain客户端初始化完成（使用原生客户端）")

    def generate_text(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本（委托给原生客户端）"""
        return self.native_client.generate_text(prompt, **kwargs)

    def generate_chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """生成对话（委托给原生客户端）"""
        return self.native_client.generate_chat(messages, **kwargs)

    def test_connection(self) -> bool:
        """测试连接（委托给原生客户端）"""
        return self.native_client.test_connection()

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息（委托给原生客户端）"""
        info = self.native_client.get_model_info()
        info["integration"] = "langchain_compatible"
        return info

    # 实现抽象方法
    def _get_provider(self) -> str:
        """获取提供商名称"""
        return "gemini"

    def analyze_document(self, document: str, **kwargs) -> Dict[str, Any]:
        """分析文档（委托给原生客户端）"""
        prompt = f"请分析以下文档：\n\n{document}"
        response = self.native_client.generate_text(prompt, **kwargs)
        return {"analysis": response.content}

    def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """生成结构化内容（委托给原生客户端）"""
        response = self.native_client.generate_text(prompt, schema=schema, **kwargs)
        try:
            import json
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"content": response.content}

    def generate_test_cases(self, api_spec: str, **kwargs) -> List[Dict[str, Any]]:
        """生成测试用例（委托给原生客户端）"""
        prompt = f"为以下API规范生成测试用例：\n\n{api_spec}"
        response = self.native_client.generate_text(prompt, **kwargs)
        return [{"test_case": response.content}]

    def validate_response(self, response: str, expected_format: str, **kwargs) -> bool:
        """验证响应格式（委托给原生客户端）"""
        prompt = f"验证以下响应是否符合格式 '{expected_format}'：\n\n{response}"
        response = self.native_client.generate_text(prompt, **kwargs)
        return "是" in response.content or "yes" in response.content.lower()
