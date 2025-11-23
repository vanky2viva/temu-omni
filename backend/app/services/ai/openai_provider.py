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
        
        # 验证并修正模型名称
        valid_models = self.get_available_models()
        if default_model and default_model not in valid_models:
            # 尝试修正常见的模型名称错误
            model_lower = default_model.lower().strip()
            if 'gpt-5' in model_lower or 'gpt5' in model_lower:
                logger.warning(f"检测到无效的模型名称 '{default_model}'，自动修正为 'gpt-4o'")
                default_model = 'gpt-4o'
            elif 'mini' in model_lower and 'gpt-4o' not in model_lower:
                logger.warning(f"检测到无效的模型名称 '{default_model}'，自动修正为 'gpt-4o-mini'")
                default_model = 'gpt-4o-mini'
            else:
                logger.warning(f"模型名称 '{default_model}' 不在有效列表中，使用默认模型 'gpt-4o'")
                default_model = 'gpt-4o'
        
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
                
                # 如果请求失败，记录详细错误信息
                if response.status_code != 200:
                    error_detail = "未知错误"
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("error", {}).get("message", str(error_data))
                        logger.error(f"OpenAI API错误响应: {error_detail}, 状态码: {response.status_code}")
                        
                        # 友好的错误提示
                        if response.status_code == 429:
                            if 'quota' in error_detail.lower() or 'billing' in error_detail.lower():
                                raise ValueError("OpenAI API 配额已用完，请检查您的账户余额和账单设置。如需继续使用，请访问 https://platform.openai.com/account/billing 充值。")
                            else:
                                raise ValueError("OpenAI API 请求频率过高，请稍后再试。")
                        elif response.status_code == 401:
                            raise ValueError("OpenAI API Key 无效或已过期，请检查设置中的 API Key 是否正确。")
                        elif response.status_code == 400:
                            raise ValueError(f"OpenAI API 请求错误: {error_detail}")
                    except ValueError:
                        # 重新抛出友好的错误消息
                        raise
                    except:
                        error_detail = response.text[:500] if response.text else "无错误详情"
                        logger.error(f"OpenAI API错误响应: {error_detail}, 状态码: {response.status_code}")
                        if response.status_code == 429:
                            raise ValueError("OpenAI API 请求频率过高或配额已用完，请稍后再试或检查账户余额。")
                        raise Exception(f"OpenAI API调用失败 (状态码 {response.status_code}): {error_detail}")
                
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
                    # 如果请求失败，记录详细错误信息
                    if response.status_code != 200:
                        error_detail = "未知错误"
                        try:
                            # 尝试读取错误响应
                            error_text = ""
                            for chunk in response.iter_bytes():
                                error_text += chunk.decode('utf-8', errors='ignore')
                                if len(error_text) > 1000:
                                    break
                            error_data = json.loads(error_text) if error_text else {}
                            error_detail = error_data.get("error", {}).get("message", str(error_data))
                            logger.error(f"OpenAI API流式调用错误响应: {error_detail}, 状态码: {response.status_code}")
                            
                            # 友好的错误提示
                            if response.status_code == 429:
                                if 'quota' in error_detail.lower() or 'billing' in error_detail.lower():
                                    raise ValueError("OpenAI API 配额已用完，请检查您的账户余额和账单设置。如需继续使用，请访问 https://platform.openai.com/account/billing 充值。")
                                else:
                                    raise ValueError("OpenAI API 请求频率过高，请稍后再试。")
                            elif response.status_code == 401:
                                raise ValueError("OpenAI API Key 无效或已过期，请检查设置中的 API Key 是否正确。")
                            elif response.status_code == 400:
                                raise ValueError(f"OpenAI API 请求错误: {error_detail}")
                        except ValueError:
                            # 重新抛出友好的错误消息
                            raise
                        except:
                            error_detail = f"HTTP {response.status_code}"
                            logger.error(f"OpenAI API流式调用错误: {error_detail}")
                            if response.status_code == 429:
                                raise ValueError("OpenAI API 请求频率过高或配额已用完，请稍后再试或检查账户余额。")
                            raise Exception(f"OpenAI API流式调用失败 (状态码 {response.status_code}): {error_detail}")
                    
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
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ]
    
    def is_available(self) -> bool:
        """检查Provider是否可用"""
        return bool(self.api_key)

