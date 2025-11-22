"""OpenAI AI Provider实现"""
import httpx
import json
from typing import List, Optional, Iterator, Dict, Any
from loguru import logger

from app.services.ai.base_provider import AIProvider, ChatMessage, ChatCompletionResponse
from app.core.config import settings


class OpenAIProvider(AIProvider):
    """OpenAI AI Provider"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "gpt-4o"
    ):
        """
        初始化OpenAI Provider
        
        Args:
            api_key: OpenAI API密钥
            base_url: API基础URL（可选，支持代理）
            default_model: 默认模型名称
        """
        self.api_key = api_key or ''
        self.base_url = base_url or 'https://api.openai.com/v1'
        self.default_model = default_model or 'gpt-4o'
        self.timeout = 30  # 默认30秒超时
    
    def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> ChatCompletionResponse:
        """
        调用OpenAI API进行聊天完成
        """
        if not self.api_key:
            raise ValueError("OpenAI API密钥未配置")
        
        model = model or self.default_model
        url = f"{self.base_url}/chat/completions"
        
        # 构建请求体
        payload = {
            "model": model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # 添加工具定义（如果支持）
        if tools:
            payload["tools"] = tools
            # 设置工具选择模式（auto：AI自动决定是否调用工具）
            payload["tool_choice"] = "auto"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                # 解析响应
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                usage = data.get("usage", {})
                
                # 检查是否有工具调用
                tool_calls = message.get("tool_calls")
                
                return ChatCompletionResponse(
                    content=message.get("content", ""),
                    model=data.get("model", model),
                    usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                    finish_reason=choice.get("finish_reason"),
                    tool_calls=tool_calls  # 添加工具调用信息
                )
                
        except httpx.HTTPError as e:
            logger.error(f"OpenAI API调用失败: {e}")
            raise Exception(f"OpenAI API调用失败: {e}")
        except Exception as e:
            logger.error(f"OpenAI API响应解析失败: {e}")
            raise
    
    def chat_completion_stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Iterator[str]:
        """
        流式调用OpenAI API进行聊天完成
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            每个chunk的内容
        """
        if not self.api_key:
            raise ValueError("OpenAI API密钥未配置")
        
        model = model or self.default_model
        url = f"{self.base_url}/chat/completions"
        
        # 构建请求体
        payload = {
            "model": model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "temperature": temperature,
            "stream": True,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # 添加工具定义（流式响应中工具调用需要特殊处理）
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            with httpx.Client(timeout=self.timeout * 2) as client:
                with client.stream("POST", url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    
                    for line in response.iter_lines():
                        if not line:
                            continue
                        
                        # 移除 "data: " 前缀
                        if line.startswith("data: "):
                            line = line[6:]
                        
                        # 检查是否是结束标记
                        if line == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(line)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.HTTPError as e:
            logger.error(f"OpenAI API流式调用失败: {e}")
            raise Exception(f"OpenAI API流式调用失败: {e}")
        except Exception as e:
            logger.error(f"OpenAI API流式响应解析失败: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        return [
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ]
    
    def is_available(self) -> bool:
        """检查Provider是否可用"""
        return bool(self.api_key)

