"""DeepSeek AI Provider实现"""
import httpx
import json
from typing import List, Optional, Iterator
from loguru import logger

from app.services.ai.base_provider import AIProvider, ChatMessage, ChatCompletionResponse
from app.core.config import settings


class DeepSeekProvider(AIProvider):
    """DeepSeek AI Provider"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "deepseek-chat"
    ):
        """
        初始化DeepSeek Provider
        
        Args:
            api_key: DeepSeek API密钥
            base_url: API基础URL
            default_model: 默认模型名称
        """
        self.api_key = api_key or ''
        self.base_url = base_url or 'https://api.deepseek.com'
        self.default_model = default_model or 'deepseek-chat'
        self.timeout = 30  # 默认30秒超时
    
    def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> ChatCompletionResponse:
        """
        调用DeepSeek API进行聊天完成
        """
        if not self.api_key:
            raise ValueError("DeepSeek API密钥未配置")
        
        model = model or self.default_model
        # 构建URL：如果base_url已经包含/v1，则直接使用，否则添加/v1
        base_url = self.base_url.rstrip('/')
        if base_url.endswith('/v1'):
            url = f"{base_url}/chat/completions"
        else:
            url = f"{base_url}/v1/chat/completions"
        
        # 构建请求体
        # 注意：对于 deepseek-reasoner 模型，不支持 temperature、top_p 等参数
        # 但为了兼容，我们仍然传入，API 会忽略这些参数
        payload = {
            "model": model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
        }
        
        # 对于非推理模型，添加 temperature 参数
        if "reasoner" not in model.lower():
            payload["temperature"] = temperature
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
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
                
                return ChatCompletionResponse(
                    content=message.get("content", ""),
                    model=data.get("model", model),
                    usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                    finish_reason=choice.get("finish_reason")
                )
                
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", str(e))
            except:
                error_detail = str(e)
            logger.error(f"DeepSeek API调用失败 (状态码 {e.response.status_code}): {error_detail}")
            raise Exception(f"DeepSeek API调用失败: {error_detail}")
        except httpx.HTTPError as e:
            logger.error(f"DeepSeek API网络错误: {e}")
            raise Exception(f"DeepSeek API网络错误: {str(e)}")
        except Exception as e:
            logger.error(f"DeepSeek API响应解析失败: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        return [
            "deepseek-chat",
            "deepseek-coder",
            "deepseek-reasoner",  # 思考模式
        ]
    
    def chat_completion_stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Iterator[str]:
        """
        流式调用DeepSeek API进行聊天完成
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            每个chunk的内容
        """
        if not self.api_key:
            raise ValueError("DeepSeek API密钥未配置")
        
        model = model or self.default_model
        # 构建URL：如果base_url已经包含/v1，则直接使用，否则添加/v1
        base_url = self.base_url.rstrip('/')
        if base_url.endswith('/v1'):
            url = f"{base_url}/chat/completions"
        else:
            url = f"{base_url}/v1/chat/completions"
        
        # 构建请求体
        # 注意：对于 deepseek-reasoner 模型，不支持 temperature、top_p 等参数
        # 但为了兼容，我们仍然传入，API 会忽略这些参数
        payload = {
            "model": model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "stream": True,
        }
        
        # 对于非推理模型，添加 temperature 参数
        if "reasoner" not in model.lower():
            payload["temperature"] = temperature
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
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
                                finish_reason = choices[0].get("finish_reason")
                                
                                # 根据 DeepSeek 推理模型文档：
                                # - reasoning_content 和 content 是同级字段
                                # - 在流式响应中，delta.reasoning_content 和 delta.content 是分开的
                                # - 需要分别处理这两个字段
                                
                                reasoning_content = delta.get("reasoning_content")
                                content = delta.get("content")
                                
                                # 如果有思考内容，返回思考内容（标记为 thinking）
                                if reasoning_content:
                                    yield json.dumps({
                                        "type": "thinking",
                                        "content": reasoning_content
                                    })
                                
                                # 返回正常内容（注意：reasoning_content 和 content 可能同时存在）
                                if content:
                                    yield json.dumps({
                                        "type": "content",
                                        "content": content
                                    })
                                
                                # 检查是否完成思考
                                # 当 finish_reason 存在且不是 "thinking" 时，表示思考已完成
                                if finish_reason and finish_reason not in ("thinking", None):
                                    # 思考完成，发送思考结束标记
                                    yield json.dumps({
                                        "type": "thinking_end"
                                    })
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", str(e))
            except:
                error_detail = str(e)
            logger.error(f"DeepSeek API流式调用失败 (状态码 {e.response.status_code}): {error_detail}")
            raise Exception(f"DeepSeek API调用失败: {error_detail}")
        except httpx.HTTPError as e:
            logger.error(f"DeepSeek API流式网络错误: {e}")
            raise Exception(f"DeepSeek API网络错误: {str(e)}")
        except Exception as e:
            logger.error(f"DeepSeek API流式响应解析失败: {e}")
            raise
    
    def is_available(self) -> bool:
        """检查Provider是否可用"""
        return bool(self.api_key)

