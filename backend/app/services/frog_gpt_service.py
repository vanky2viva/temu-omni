"""
FrogGPT AI服务 - 使用OpenRouter.ai提供AI能力
使用 OpenRouter Python SDK: https://openrouter.ai/docs/sdks/python/overview
"""
from typing import List, Dict, Any, Optional
import httpx
import json
from loguru import logger
import traceback
from app.core.config import settings
from sqlalchemy.orm import Session

try:
    from openrouter import OpenRouter
    OPENROUTER_SDK_AVAILABLE = True
except ImportError:
    OPENROUTER_SDK_AVAILABLE = False
    logger.warning("OpenRouter SDK 未安装，将使用 httpx 直接调用 API。建议安装: pip install openrouter")


class FrogGPTService:
    """FrogGPT AI服务类"""
    
    def __init__(self):
        """初始化服务"""
        # 优先使用环境变量，如果没有则从数据库读取（在需要时）
        self.api_key = settings.OPENROUTER_API_KEY
        self.default_model = settings.OPENROUTER_MODEL
        self.timeout = settings.OPENROUTER_TIMEOUT
        self.http_referer = settings.OPENROUTER_HTTP_REFERER
        self.x_title = settings.OPENROUTER_X_TITLE
        self.base_url = "https://openrouter.ai/api/v1"
        
        # 创建HTTP客户端
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True
        )
    
    def get_api_key_from_db(self, db: Session) -> Optional[str]:
        """从数据库获取API key"""
        from app.models.system_config import SystemConfig
        
        config = db.query(SystemConfig).filter(SystemConfig.key == "openrouter_api_key").first()
        if config and config.value:
            return config.value
        
        # 如果数据库中没有，返回环境变量中的值
        return self.api_key
    
    def get_api_key(self, db: Optional[Session] = None) -> Optional[str]:
        """获取API key（优先从数据库，其次环境变量）"""
        if db:
            db_key = self.get_api_key_from_db(db)
            if db_key:
                return db_key
        
        # 如果数据库中没有或没有提供db，使用环境变量
        return self.api_key
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        发送聊天完成请求到OpenRouter
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            model: 模型名称，如果为None则使用默认模型
            temperature: 温度参数（0-2），默认0.7
            max_tokens: 最大token数，如果为None则不限制
            
        Returns:
            API响应数据
        """
        try:
            # 处理AUTO模式：如果model为"auto"，使用OpenRouter的自动路由
            use_auto_routing = False
            if model and model.lower() == "auto":
                # OpenRouter的自动路由：使用通用模型，OpenRouter会在多个提供商间智能选择
                # 根据OpenRouter文档，可以通过provider配置实现智能路由
                model = "openai/gpt-4o-mini"  # 使用通用模型作为基础
                use_auto_routing = True
            else:
                model = model or self.default_model
            
            # 验证模型名称格式（OpenRouter 要求格式为 provider/model）
            if model and "/" not in model and model.lower() != "auto":
                # 如果不是 auto 且没有 provider 前缀，尝试添加默认前缀
                logger.warning(f"模型名称 '{model}' 缺少 provider 前缀，尝试使用默认格式")
                # 检查是否是常见的模型名称，如果是则添加对应的前缀
                model_lower = model.lower()
                if "gpt" in model_lower or "openai" in model_lower:
                    model = f"openai/{model}"
                elif "claude" in model_lower or "anthropic" in model_lower:
                    model = f"anthropic/{model}"
                elif "gemini" in model_lower or "google" in model_lower:
                    model = f"google/{model}"
                else:
                    # 默认使用 openai 前缀
                    model = f"openai/{model}"
                logger.info(f"模型名称已修正为: {model}")
            
            # 确保模型名称格式正确（必须是 provider/model 格式）
            if model and model.lower() != "auto" and "/" not in model:
                raise ValueError(f"模型名称格式错误: {model}。OpenRouter 要求格式为 'provider/model'，例如 'openai/gpt-4o-mini'")
            
            # 获取API key（优先从数据库）
            api_key = self.get_api_key(db)
            
            # 构建请求头（根据 OpenRouter API 文档）
            # 参考: https://openrouter.ai/docs/api/reference/overview
            # 参考: https://openrouter.ai/docs/sdks/typescript/chat
            headers = {
                "Content-Type": "application/json",
            }
            
            # Authorization 头是必需的（如果使用 API Key）
            # 格式: Authorization: Bearer <api_key>
            # 参考: https://openrouter.ai/docs/api/reference/overview
            if api_key:
                # 确保 API Key 格式正确（去除前后空格）
                api_key = api_key.strip()
                if not api_key:
                    raise ValueError("API Key 不能为空")
                headers["Authorization"] = f"Bearer {api_key}"
            else:
                # 如果没有 API Key，记录警告
                logger.warning("未提供 OpenRouter API Key，请求可能失败")
            
            # HTTP-Referer 和 X-Title 是可选的，用于免费使用和标识应用
            # 参考: https://openrouter.ai/docs/api/reference/overview
            # 注意：OpenRouter 要求使用 HTTP-Referer（不是标准的 Referer 头）
            if self.http_referer:
                headers["HTTP-Referer"] = self.http_referer
            
            if self.x_title:
                headers["X-Title"] = self.x_title
            
            # User-Agent 头（可选，但建议添加）
            headers["User-Agent"] = f"Temu-Omni/{settings.APP_VERSION}"
            
            # 构建请求体（OpenRouter 标准格式，与 OpenAI Chat API 兼容）
            # 参考: https://openrouter.ai/docs/api/reference/overview
            # 参考: https://openrouter.ai/docs/sdks/typescript/chat
            # 请求体格式必须符合 OpenRouter API 规范
            payload = {
                "model": model,  # 模型 ID，格式: provider/model-name
                "messages": messages,  # 消息列表，格式: [{"role": "user", "content": "..."}]
                "temperature": temperature,  # 温度参数，范围: 0-2
            }
            
            # 可选参数
            if max_tokens:
                payload["max_tokens"] = max_tokens
            
            # 验证消息格式
            if not messages or len(messages) == 0:
                raise ValueError("消息列表不能为空")
            
            # 验证消息格式
            for msg in messages:
                if not isinstance(msg, dict):
                    raise ValueError(f"消息格式错误: 必须是字典类型，收到 {type(msg)}")
                if "role" not in msg or "content" not in msg:
                    raise ValueError(f"消息格式错误: 必须包含 'role' 和 'content' 字段")
                if msg["role"] not in ["system", "user", "assistant"]:
                    raise ValueError(f"消息角色错误: 必须是 'system', 'user' 或 'assistant'，收到 '{msg['role']}'")
            
            # 如果 SDK 可用，优先使用 SDK
            if OPENROUTER_SDK_AVAILABLE and api_key:
                try:
                    logger.info(f"使用 OpenRouter SDK 发送请求: model={model}, messages_count={len(messages)}")
                    
                    async with OpenRouter(api_key=api_key) as client:
                        request_params = {
                            "model": model,
                            "messages": messages,
                            "temperature": temperature,
                        }
                        if max_tokens:
                            request_params["max_tokens"] = max_tokens
                        
                        # 使用 SDK 的异步方法
                        response = await client.chat.send_async(**request_params)
                        
                        # 转换 SDK 响应为字典格式（兼容现有代码）
                        result = {
                            "id": getattr(response, "id", None),
                            "model": getattr(response, "model", model),
                            "choices": [],
                            "usage": {}
                        }
                        
                        # 转换 choices
                        if hasattr(response, "choices") and response.choices:
                            for choice in response.choices:
                                choice_dict = {
                                    "index": getattr(choice, "index", 0),
                                    "message": {
                                        "role": getattr(choice.message, "role", "assistant"),
                                        "content": getattr(choice.message, "content", ""),
                                    },
                                    "finish_reason": getattr(choice, "finish_reason", "stop"),
                                }
                                result["choices"].append(choice_dict)
                        
                        # 转换 usage
                        if hasattr(response, "usage"):
                            result["usage"] = {
                                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                                "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                                "total_tokens": getattr(response.usage, "total_tokens", 0),
                            }
                        
                        logger.debug(f"OpenRouter SDK 响应成功: model={model}, choices_count={len(result.get('choices', []))}")
                        return result
                        
                except Exception as e:
                    logger.warning(f"OpenRouter SDK 调用失败，回退到 httpx: {e}")
                    logger.debug(traceback.format_exc())
                    # 继续执行 httpx 回退逻辑
            
            # 回退到 httpx 直接调用
            logger.info(f"使用 httpx 发送请求: model={model}, messages_count={len(messages)}, has_api_key={bool(api_key)}")
            if not api_key:
                raise ValueError("未提供 OpenRouter API Key，无法发送请求。请在高级设置中配置 API Key。")
            
            # 记录请求详情（用于调试，不记录完整的 API Key）
            api_key_preview = f"{api_key[:8]}...{api_key[-4:]}" if api_key and len(api_key) > 12 else "***"
            logger.info(f"请求详情: URL={self.base_url}/chat/completions, API Key={api_key_preview}, 模型={model}")
            logger.debug(f"请求头: {list(headers.keys())}")
            logger.debug(f"请求体: {payload}")
            
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            )
            
            # 记录响应状态
            logger.debug(f"OpenRouter响应状态: {response.status_code}")
            
            # 如果状态码不是 2xx，记录详细错误信息并抛出异常
            if response.status_code >= 400:
                try:
                    error_body = response.json()
                    error_info = error_body.get("error", {})
                    error_message = error_info.get("message", str(error_body))
                    error_code = error_info.get("code", "")
                    error_type = error_info.get("type", "")
                    
                    # 根据错误类型提供更详细的错误信息
                    if response.status_code == 401:
                        error_detail = "OpenRouter API Key 无效或已过期，请检查 API Key 配置"
                    elif response.status_code == 403:
                        # 403 错误可能是多种原因，提供更详细的建议
                        if "Provider returned error" in error_message:
                            error_detail = f"OpenRouter API 访问被拒绝: {error_message}. 可能的原因：1) API Key 权限不足 2) 账户余额不足 3) 模型 '{model}' 不可用或需要特殊权限 4) API Key 已过期。请检查 OpenRouter 账户状态和模型访问权限。建议：尝试使用 'auto' 模式或 'openai/gpt-4o-mini' 等基础模型。"
                        else:
                            error_detail = f"OpenRouter API 访问被拒绝: {error_message}. 请检查 API Key 权限、账户余额或模型访问权限"
                    elif response.status_code == 404:
                        error_detail = f"模型不存在: {model}. 请检查模型名称是否正确"
                    elif response.status_code == 429:
                        error_detail = "OpenRouter API 请求频率过高，请稍后重试"
                    else:
                        error_detail = f"OpenRouter API 错误 ({response.status_code}): {error_message}"
                    
                    logger.error(f"OpenRouter API 错误响应: {error_detail}, 完整响应: {error_body}")
                    raise ValueError(error_detail)
                except ValueError:
                    # 重新抛出 ValueError（包含错误详情）
                    raise
                except:
                    error_text = response.text[:500] if response.text else "无响应内容"
                    error_detail = f"OpenRouter API 错误 ({response.status_code}): {error_text}"
                    logger.error(f"OpenRouter API 错误响应: {error_detail}")
                    raise ValueError(error_detail)
            
            # 检查 HTTP 状态码
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"OpenRouter响应成功: model={model}, response_keys={list(result.keys())}")
            
            # 验证响应格式
            if not isinstance(result, dict):
                raise ValueError(f"OpenRouter API 返回了无效的响应类型: {type(result)}")
            
            if "choices" not in result:
                error_msg = result.get("error", {}).get("message", "响应中缺少 choices 字段")
                logger.error(f"OpenRouter API 响应格式错误: {error_msg}, response: {result}")
                raise ValueError(f"OpenRouter API 响应格式错误: {error_msg}")
            
            if not result.get("choices") or len(result["choices"]) == 0:
                error_msg = result.get("error", {}).get("message", "choices 数组为空")
                logger.error(f"OpenRouter API 响应中 choices 为空: {error_msg}, response: {result}")
                raise ValueError(f"OpenRouter API 响应中 choices 为空: {error_msg}")
            
            return result
            
        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_json = e.response.json()
                error_msg = error_json.get("error", {}).get("message", e.response.text)
                error_detail = f"HTTP {e.response.status_code}: {error_msg}"
            except:
                error_detail = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"OpenRouter API请求失败: {error_detail}")
            raise ValueError(f"OpenRouter API 请求失败: {error_detail}")
        except httpx.TimeoutException as e:
            logger.error(f"OpenRouter API 请求超时: {e}")
            raise ValueError("OpenRouter API 请求超时，请稍后重试")
        except httpx.RequestError as e:
            logger.error(f"OpenRouter API 请求错误: {e}")
            raise ValueError(f"OpenRouter API 请求错误: {str(e)}")
        except Exception as e:
            logger.error(f"OpenRouter API请求异常: {e}")
            logger.error(traceback.format_exc())
            raise
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        db: Optional[Session] = None
    ):
        """
        发送流式聊天完成请求到OpenRouter
        参考: https://openrouter.ai/docs/sdks/python/chat
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            model: 模型名称，如果为None则使用默认模型
            temperature: 温度参数（0-2），默认0.7
            max_tokens: 最大token数，如果为None则不限制
            
        Yields:
            SSE格式的数据块（字典格式）
        """
        try:
            # 处理AUTO模式：如果model为"auto"，使用OpenRouter的自动路由
            if model == "auto" or model is None:
                model = self.default_model or "openai/gpt-4o-mini"
            
            # 验证模型名称格式
            if "/" not in model:
                model = f"openai/{model}"
            
            # 获取 API Key
            api_key = self.get_api_key(db)
            if not api_key:
                raise ValueError("未提供 OpenRouter API Key，无法发送请求。请在高级设置中配置 API Key。")
            
            # 清理 API Key（去除前后空格）
            api_key = api_key.strip()
            
            # 如果 SDK 可用，优先使用 SDK
            if OPENROUTER_SDK_AVAILABLE and api_key:
                try:
                    logger.info(f"使用 OpenRouter SDK 发送流式请求: model={model}, messages_count={len(messages)}")
                    
                    # 构建请求参数
                    request_params = {
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "stream": True,  # 启用流式响应
                    }
                    if max_tokens:
                        request_params["max_tokens"] = max_tokens
                    
                    # 使用 SDK 的流式方法
                    # 注意：SDK 的流式方法可能是同步的，需要在异步上下文中运行
                    import asyncio
                    from concurrent.futures import ThreadPoolExecutor
                    
                    def run_sdk_stream():
                        """在同步上下文中运行 SDK 流式请求"""
                        with OpenRouter(api_key=api_key.strip()) as client:
                            stream = client.chat.send(**request_params)
                            events = []
                            try:
                                # SDK 返回的事件流需要迭代
                                for event in stream:
                                    events.append(event)
                            except Exception as e:
                                logger.error(f"SDK 流式迭代错误: {e}")
                                raise
                            return events
                    
                    # 在线程池中运行同步 SDK 调用
                    loop = asyncio.get_event_loop()
                    with ThreadPoolExecutor() as executor:
                        events = await loop.run_in_executor(executor, run_sdk_stream)
                    
                    # 处理 SDK 返回的事件
                    for event in events:
                        # 检查是否有错误
                        if hasattr(event, 'error') and event.error:
                            error_message = getattr(event.error, 'message', '未知错误')
                            logger.error(f"流式响应中的错误: {error_message}")
                            yield {
                                "type": "error",
                                "error": error_message,
                            }
                            return
                        
                        # 提取内容
                        if hasattr(event, 'choices') and event.choices:
                            choice = event.choices[0] if len(event.choices) > 0 else None
                            if choice and hasattr(choice, 'delta'):
                                delta = choice.delta
                                if hasattr(delta, 'content') and delta.content:
                                    yield {
                                        "type": "content",
                                        "content": delta.content,
                                        "id": getattr(event, 'id', None),
                                        "model": getattr(event, 'model', model),
                                    }
                            
                            # 检查是否完成
                            if choice and hasattr(choice, 'finish_reason') and choice.finish_reason:
                                # 发送使用统计（如果有）
                                if hasattr(event, 'usage') and event.usage:
                                    yield {
                                        "type": "usage",
                                        "usage": {
                                            "prompt_tokens": getattr(event.usage, 'prompt_tokens', 0),
                                            "completion_tokens": getattr(event.usage, 'completion_tokens', 0),
                                            "total_tokens": getattr(event.usage, 'total_tokens', 0),
                                        },
                                    }
                                yield {
                                    "type": "done",
                                    "finish_reason": choice.finish_reason,
                                }
                                return
                    
                    logger.debug("OpenRouter SDK 流式响应完成")
                    return
                    
                except Exception as e:
                    logger.warning(f"OpenRouter SDK 流式调用失败，回退到 httpx: {e}")
                    logger.debug(traceback.format_exc())
                    # 继续执行 httpx 回退逻辑
            
            # 回退到 httpx 直接调用
            logger.info(f"使用 httpx 发送流式请求: model={model}, messages_count={len(messages)}")
            
            # 构建请求头（确保格式正确）
            headers = {
                "Authorization": f"Bearer {api_key.strip()}",
                "Content-Type": "application/json",
            }
            # 添加可选的 HTTP-Referer 和 X-Title（如果配置了）
            if self.http_referer:
                headers["HTTP-Referer"] = self.http_referer
            if self.x_title:
                headers["X-Title"] = self.x_title
            
            # 构建请求体
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": True,  # 启用流式响应
            }
            if max_tokens:
                payload["max_tokens"] = max_tokens
            
            # 使用 httpx 发送流式请求
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                ) as response:
                    # 检查初始 HTTP 状态码
                    if response.status_code >= 400:
                        try:
                            error_body = await response.aread()
                            error_json = json.loads(error_body.decode('utf-8'))
                            error_info = error_json.get("error", {})
                            error_message = error_info.get("message", str(error_json))
                            raise ValueError(f"OpenRouter API 错误 ({response.status_code}): {error_message}")
                        except:
                            raise ValueError(f"OpenRouter API 错误 ({response.status_code})")
                    
                    # 处理 SSE 流
                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        
                        # 处理完整的 SSE 行
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            
                            if line.startswith("data: "):
                                data = line[6:]  # 移除 "data: " 前缀
                                
                                if data == "[DONE]":
                                    return
                                
                                try:
                                    parsed = json.loads(data)
                                    
                                    # 检查是否有错误
                                    if "error" in parsed:
                                        error_info = parsed["error"]
                                        error_message = error_info.get("message", "未知错误")
                                        logger.error(f"流式响应中的错误: {error_message}")
                                        yield {
                                            "type": "error",
                                            "error": error_message,
                                        }
                                        return
                                    
                                    # 提取内容
                                    if "choices" in parsed and len(parsed["choices"]) > 0:
                                        delta = parsed["choices"][0].get("delta", {})
                                        content = delta.get("content", "")
                                        
                                        if content:
                                            yield {
                                                "type": "content",
                                                "content": content,
                                                "id": parsed.get("id"),
                                                "model": parsed.get("model"),
                                            }
                                        
                                        # 检查是否完成
                                        finish_reason = parsed["choices"][0].get("finish_reason")
                                        if finish_reason:
                                            # 发送使用统计（如果有）
                                            if "usage" in parsed:
                                                yield {
                                                    "type": "usage",
                                                    "usage": parsed["usage"],
                                                }
                                            yield {
                                                "type": "done",
                                                "finish_reason": finish_reason,
                                            }
                                            return
                                    
                                except json.JSONDecodeError:
                                    # 忽略无效的 JSON（可能是注释行）
                                    pass
                            elif line.startswith(":"):
                                # SSE 注释行，忽略
                                pass
                            
        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_json = e.response.json()
                error_msg = error_json.get("error", {}).get("message", e.response.text)
                error_detail = f"HTTP {e.response.status_code}: {error_msg}"
            except:
                error_detail = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"OpenRouter API流式请求失败: {error_detail}")
            yield {
                "type": "error",
                "error": f"OpenRouter API 请求失败: {error_detail}",
            }
        except Exception as e:
            logger.error(f"流式聊天请求失败: {e}")
            logger.error(traceback.format_exc())
            yield {
                "type": "error",
                "error": f"流式聊天请求失败: {str(e)}",
            }
    
    async def get_models(self, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """
        获取可用的AI模型列表
        使用 OpenRouter Python SDK: https://openrouter.ai/docs/sdks/python/overview
        
        Args:
            db: 数据库会话（可选，用于从数据库读取API key）
        
        Returns:
            模型列表
        """
        api_key = self.get_api_key(db)
        
        # 如果 SDK 可用，尝试使用 SDK
        if OPENROUTER_SDK_AVAILABLE and api_key:
            try:
                logger.info("使用 OpenRouter SDK 获取模型列表")
                async with OpenRouter(api_key=api_key.strip()) as client:
                    # 注意：根据 SDK 文档，可能需要使用不同的方法
                    # 这里尝试使用 SDK 的方法，如果不存在则回退
                    try:
                        # 尝试使用 SDK 的 models API
                        if hasattr(client, "models") and hasattr(client.models, "list_async"):
                            models_response = await client.models.list_async()
                            
                            models = []
                            if hasattr(models_response, "data") and models_response.data:
                                for model in models_response.data:
                                    model_dict = {
                                        "id": getattr(model, "id", ""),
                                        "name": getattr(model, "name", ""),
                                        "description": getattr(model, "description", ""),
                                        "context_length": getattr(model, "context_length", 0),
                                    }
                                    # 添加定价信息（如果可用）
                                    if hasattr(model, "pricing"):
                                        model_dict["pricing"] = {
                                            "prompt": getattr(model.pricing, "prompt", "0"),
                                            "completion": getattr(model.pricing, "completion", "0"),
                                        }
                                    models.append(model_dict)
                            
                            logger.debug(f"OpenRouter SDK 返回 {len(models)} 个模型")
                            return models
                        else:
                            # SDK 可能没有 models API，回退到 httpx
                            logger.debug("SDK 不支持 models API，回退到 httpx")
                            raise AttributeError("SDK models API not available")
                    except (AttributeError, NotImplementedError) as e:
                        logger.debug(f"SDK models API 不可用: {e}，回退到 httpx")
                        raise
            except Exception as e:
                logger.warning(f"OpenRouter SDK 获取模型列表失败，回退到 httpx: {e}")
                logger.debug(traceback.format_exc())
                # 继续执行 httpx 回退逻辑
        
        # 回退到 httpx 直接调用
        try:
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key.strip()}"
            
            response = await self.client.get(
                f"{self.base_url}/models",
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("data", [])
            
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            # 返回一些默认模型
            return [
                {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini"},
                {"id": "openai/gpt-4o", "name": "GPT-4o"},
                {"id": "anthropic/claude-3-haiku", "name": "Claude 3 Haiku"},
            ]
    
    def build_system_context(self, data_summary: Dict[str, Any]) -> str:
        """
        构建系统上下文提示词
        
        Args:
            data_summary: 数据摘要字典，包含overview、top_skus、top_managers等
            
        Returns:
            系统上下文字符串
        """
        context_parts = []
        
        # 添加总览信息
        if "overview" in data_summary:
            overview = data_summary["overview"]
            context_parts.append("## 运营数据总览")
            context_parts.append(f"- 总订单数: {overview.get('total_orders', 0)}")
            context_parts.append(f"- 总销量: {overview.get('total_quantity', 0)} 件")
            context_parts.append(f"- 总GMV: ¥{overview.get('total_gmv', 0):,.2f}")
            context_parts.append(f"- 总成本: ¥{overview.get('total_cost', 0):,.2f}")
            context_parts.append(f"- 总利润: ¥{overview.get('total_profit', 0):,.2f}")
            context_parts.append(f"- 利润率: {overview.get('profit_margin', 0):.2f}%")
        
        # 添加热门SKU
        if "top_skus" in data_summary and data_summary["top_skus"]:
            context_parts.append("\n## 热门SKU（Top 10）")
            for i, sku in enumerate(data_summary["top_skus"][:10], 1):
                context_parts.append(
                    f"{i}. {sku.get('sku', 'N/A')} - "
                    f"销量: {sku.get('total_quantity', 0)} 件, "
                    f"订单: {sku.get('order_count', 0)} 单, "
                    f"GMV: ¥{sku.get('gmv', 0):,.2f}"
                )
        
        # 添加负责人统计
        if "top_managers" in data_summary and data_summary["top_managers"]:
            context_parts.append("\n## 负责人业绩（Top 10）")
            for i, manager in enumerate(data_summary["top_managers"][:10], 1):
                context_parts.append(
                    f"{i}. {manager.get('manager', 'N/A')} - "
                    f"订单: {manager.get('order_count', 0)} 单, "
                    f"销量: {manager.get('total_quantity', 0)} 件, "
                    f"GMV: ¥{manager.get('total_gmv', 0):,.2f}, "
                    f"利润: ¥{manager.get('total_profit', 0):,.2f}"
                )
        
        context = "\n".join(context_parts)
        
        # 添加系统提示
        system_prompt = """你是一个专业的电商运营助手，名为FrogGPT。你的任务是帮助运营人员分析数据、提供决策建议。

当前系统提供了以下运营数据，请基于这些数据回答用户的问题，并提供有价值的分析和建议。

"""
        return system_prompt + context
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


# 创建全局服务实例
frog_gpt_service = FrogGPTService()
