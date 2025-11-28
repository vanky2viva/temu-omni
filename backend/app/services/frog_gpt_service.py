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
                    # 注意：SDK 的流式方法可能是同步的，需要在线程中运行
                    # 但由于需要实时流式传输，我们直接使用 httpx 而不是 SDK
                    # SDK 的流式方法会阻塞，无法实现真正的实时流式传输
                    logger.info("跳过 SDK，直接使用 httpx 实现实时流式传输")
                    # 继续执行下面的 httpx 回退逻辑
                    
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
                    
                    # 处理 SSE 流（Server-Sent Events）
                    # 参考: https://openrouter.ai/docs/api/reference/streaming
                    buffer = ""
                    async for chunk in response.aiter_text():
                        if not chunk:
                            continue
                        buffer += chunk
                        
                        # 处理完整的 SSE 行（以 \n 分隔）
                        while True:
                            line_end = buffer.find('\n')
                            if line_end == -1:
                                break
                            
                            line = buffer[:line_end].strip()
                            buffer = buffer[line_end + 1:]
                            
                            # 跳过空行
                            if not line:
                                continue
                            
                            # 跳过 SSE 注释行（如 ": OPENROUTER PROCESSING"）
                            if line.startswith(':'):
                                logger.debug(f"收到 SSE 注释: {line}")
                                continue
                            
                            # 处理 data: 开头的行
                            if line.startswith("data: "):
                                data = line[6:]  # 移除 "data: " 前缀
                                
                                # 检查结束标记
                                if data == "[DONE]":
                                    logger.debug("收到流式响应结束标记 [DONE]")
                                    return
                                
                                try:
                                    parsed = json.loads(data)
                                    
                                    # 检查是否有错误（根据 OpenRouter 文档，错误可能在顶层）
                                    if "error" in parsed:
                                        error_info = parsed["error"]
                                        error_message = error_info.get("message", "未知错误")
                                        logger.error(f"流式响应中的错误: {error_message}")
                                        yield {
                                            "type": "error",
                                            "error": error_message,
                                        }
                                        return
                                    
                                    # 提取内容（根据 OpenRouter 文档格式）
                                    if "choices" in parsed and len(parsed["choices"]) > 0:
                                        choice = parsed["choices"][0]
                                        delta = choice.get("delta", {})
                                        content = delta.get("content")
                                        
                                        # 如果有内容，立即 yield（实现真正的流式传输）
                                        if content:
                                            yield {
                                                "type": "content",
                                                "content": content,
                                                "id": parsed.get("id"),
                                                "model": parsed.get("model"),
                                            }
                                        
                                        # 检查是否完成（finish_reason 不为 None 表示完成）
                                        finish_reason = choice.get("finish_reason")
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
                                            logger.debug(f"流式响应完成: finish_reason={finish_reason}")
                                            return
                                    
                                except json.JSONDecodeError as e:
                                    # 忽略无效的 JSON（可能是注释行或其他格式）
                                    logger.debug(f"跳过无效的 SSE 数据: {data[:100] if len(data) > 100 else data}")
                                    continue
                                except Exception as e:
                                    logger.warning(f"处理 SSE 数据时出错: {e}, data={data[:100] if len(data) > 100 else data}")
                                    continue
                            
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
            context_parts.append(f"- 延误率: {overview.get('delay_rate', 0):.2f}% (延误订单数: {overview.get('delay_count', 0)})")
        
        # 添加热门SKU
        if "top_skus" in data_summary and data_summary["top_skus"]:
            context_parts.append("\n## 热门SKU（Top 10）")
            for i, sku in enumerate(data_summary["top_skus"][:10], 1):
                context_parts.append(
                    f"{i}. {sku.get('sku', 'N/A')} ({sku.get('product_name', 'N/A')}) - "
                    f"销量: {sku.get('total_quantity', 0)} 件, "
                    f"订单: {sku.get('order_count', 0)} 单, "
                    f"GMV: ¥{sku.get('gmv', 0):,.2f}, "
                    f"利润: ¥{sku.get('total_profit', 0):,.2f}, "
                    f"负责人: {sku.get('manager', '未分配')}"
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
        system_prompt = """你是一个专业的电商运营助手，名为FrogGPT。你的任务是帮助运营人员分析数据、提供决策建议和运营指导。

## 你的核心能力：
1. **数据分析**：深入分析GMV、订单、利润、延误率等关键指标，识别趋势和异常
2. **问题诊断**：快速定位运营问题（如GMV下降、延误率上升、利润率下降等）的根本原因
3. **决策建议**：基于数据提供可执行的运营决策，包括：
   - SKU优化建议（哪些SKU需要下架、哪些需要加大投入）
   - **备货计划制定**（根据过去一周的回款数据和销量，制定未来一周/月的按SKU货号的备货计划）
   - 库存管理建议（根据销售趋势预测库存需求）
   - 价格策略建议（基于利润率和竞争情况）
   - 物流优化建议（降低延误率的具体措施）
   - 团队管理建议（负责人业绩分析和激励建议）
4. **风险预警**：识别潜在风险（如延误率过高、利润率下降、SKU滞销等）并提供应对方案
5. **运营优化**：提供提升GMV、利润、客户满意度的具体优化方案

## 数据说明：
- **GMV**：总交易额（已统一为人民币CNY）
- **利润率**：总利润/总GMV × 100%
- **延误率**：发货时间超过预期最晚发货时间的订单占比，是重要的物流质量指标（与订单列表的延误率是同一数据）
- **订单数**：按父订单去重统计（一个父订单可能包含多个子订单）
- **销量**：销售件数（商品数量）

## 分析原则：
1. 结合多个指标综合分析，不要只看单一指标
2. 关注趋势变化，识别异常波动
3. 提供具体、可执行的建议，避免空泛的建议
4. 优先关注影响GMV和利润的关键问题
5. 考虑业务实际情况，提供符合电商运营规律的方案

## 决策卡片输出格式（重要）：
当用户询问需要决策建议的问题时（如"分析最近7天GMV变化原因"、"如何提升利润率"、"延误率高的原因"等），你需要在回答中**同时输出决策卡片数据**。

决策卡片数据必须使用以下JSON格式，放在Markdown代码块中：

```json
{
  "decisionSummary": "决策总结（1-2句话，概括核心问题和解决方案）",
  "riskLevel": "low|medium|high",
  "actions": [
    {
      "type": "动作类型（如：调整SKU、优化库存、调整价格、优化物流、团队激励等）",
      "target": "目标对象（如：SKU编号、负责人姓名、具体指标等）",
      "delta": "变化量或目标值（如：+10%、提升至5%、降低2%等）",
      "reason": "原因说明（简要说明为什么需要这个动作）",
      "priority": "high|medium|low",
      "estimatedImpact": "预期影响（如：预计提升GMV 5%、降低延迟率2%等）"
    }
  ],
  "metadata": {
    "analysisDate": "分析日期（格式：YYYY-MM-DD）",
    "dataRange": "数据范围（如：最近7天、最近30天、全部数据等）",
    "confidence": 0.85
  }
}
```

### 决策卡片字段说明：
- **decisionSummary**（必需）：决策总结，1-2句话概括核心问题和解决方案
- **riskLevel**（必需）：风险级别
  - `low`：低风险，常规优化
  - `medium`：中等风险，需要关注
  - `high`：高风险，需要立即处理
- **actions**（必需）：执行动作数组，至少1个动作
  - `type`：动作类型（如：调整SKU、优化库存、调整价格、优化物流、团队激励、下架商品、加大投入等）
  - `target`：目标对象（具体SKU、负责人、指标名称等）
  - `delta`：变化量或目标值（如：+10%、提升至5%、降低2%等，可选）
  - `reason`：原因说明（简要说明为什么需要这个动作，可选）
  - `priority`：优先级（high/medium/low，可选，默认为medium）
  - `estimatedImpact`：预期影响（如：预计提升GMV 5%、降低延迟率2%等，可选）
- **metadata**（可选）：元数据
  - `analysisDate`：分析日期（格式：YYYY-MM-DD）
  - `dataRange`：数据范围（如：最近7天、最近30天、全部数据等）
  - `confidence`：置信度（0-1之间的数字，如0.85表示85%置信度）

### 决策卡片输出示例：

**用户问题**："分析最近7天GMV变化原因"

**你的回答应该包含**：
1. 文字分析（正常回答）
2. 决策卡片JSON（在回答末尾或中间，用```json代码块包裹）

示例：
```
根据数据分析，最近7天GMV下降了15%，主要原因是：
1. Top SKU "SKU-12345" 销量下降30%
2. 延误率上升至8%，影响客户满意度
3. 新SKU投入不足

建议采取以下措施：
- 立即检查SKU-12345的库存和价格
- 优化物流流程，降低延误率
- 加大新SKU的推广投入

```json
{
  "decisionSummary": "GMV下降15%，主要因Top SKU销量下降和延误率上升，需立即优化SKU和物流",
  "riskLevel": "high",
  "actions": [
    {
      "type": "调整SKU",
      "target": "SKU-12345",
      "delta": "提升销量30%",
      "reason": "Top SKU销量下降30%，影响整体GMV",
      "priority": "high",
      "estimatedImpact": "预计恢复GMV 10%"
    },
    {
      "type": "优化物流",
      "target": "延误率",
      "delta": "降低至5%",
      "reason": "延误率上升至8%，影响客户满意度",
      "priority": "high",
      "estimatedImpact": "预计提升客户满意度，减少退款"
    },
    {
      "type": "加大投入",
      "target": "新SKU推广",
      "delta": "增加20%推广预算",
      "reason": "新SKU投入不足，需要加大推广",
      "priority": "medium",
      "estimatedImpact": "预计提升新SKU销量15%"
    }
  ],
  "metadata": {
    "analysisDate": "2024-11-28",
    "dataRange": "最近7天",
    "confidence": 0.9
  }
}
```
```

### 重要提示：
1. **决策卡片必须包含在```json代码块中**，否则系统无法解析
2. **JSON格式必须严格正确**，不能有语法错误
3. **decisionSummary、riskLevel、actions是必需字段**，不能省略
4. **actions数组至少包含1个动作**，建议3-5个动作
5. **priority建议根据风险级别和影响程度设置**：高风险问题用high，常规优化用medium/low
6. **confidence建议根据数据完整性和分析确定性设置**：数据完整且分析确定用0.8-1.0，数据不足用0.5-0.8

## 数据查询方法（重要）：
系统已经为你提供了当前时间范围内的运营数据。这些数据是通过统一的数据端点获取的，所有端点都使用 `UnifiedStatisticsService` 确保数据一致性，并内置 Redis 缓存（TTL=300秒）以提升性能。

### 统一数据端点（系统已使用）
系统提供了以下统一数据端点，所有数据都经过缓存优化：
1. `/api/statistics/unified/overview` - 订单总览统计
2. `/api/statistics/unified/daily` - 每日统计数据
3. `/api/statistics/unified/sku-ranking` - SKU销售排行
4. `/api/statistics/unified/manager-ranking` - 负责人业绩排行
5. `/api/statistics/unified/summary` - 综合数据摘要（AI模块使用）

### 后端服务方法（内部实现）
以下方法用于实现统一端点，确保数据一致性和准确性：

### 1. 订单统计数据查询
- **方法**：`UnifiedStatisticsService.calculate_order_statistics(db, filters)`
- **返回字段**：
  - `order_count`: 订单数（按父订单去重）
  - `total_quantity`: 总销量（件数）
  - `total_gmv`: 总GMV（CNY）
  - `total_cost`: 总成本（CNY）
  - `total_profit`: 总利润（CNY）
  - `delay_rate`: 延误率（%）
  - `delay_count`: 延迟订单数

### 2. SKU统计数据查询
- **方法**：`UnifiedStatisticsService.get_sku_statistics(db, filters, limit=10)`
- **返回字段**（每个SKU）：
  - `sku`: SKU ID
  - `product_name`: 商品名称
  - `manager`: 负责人
  - `total_quantity`: 销量（件数）
  - `order_count`: 订单数
  - `total_gmv`: GMV（CNY）
  - `total_profit`: 利润（CNY）

### 3. 负责人统计数据查询
- **方法**：`UnifiedStatisticsService.get_manager_statistics(db, filters)`
- **返回字段**（每个负责人）：
  - `manager`: 负责人姓名
  - `total_quantity`: 销量（件数）
  - `order_count`: 订单数
  - `total_gmv`: GMV（CNY）
  - `total_profit`: 利润（CNY）

### 4. 每日统计数据查询
- **方法**：`StatisticsService.get_daily_statistics(db, shop_ids, start_date, end_date, days)`
- **返回字段**（每天）：
  - `date`: 日期（YYYY-MM-DD）
  - `order_count`: 订单数
  - `gmv`: GMV（CNY）
  - `cost`: 成本（CNY）
  - `profit`: 利润（CNY）
  - `delay_rate`: 延误率（%）

### 5. 统一过滤规则
所有数据查询都使用 `UnifiedStatisticsService.build_base_filters()` 构建过滤条件，确保：
- **订单状态过滤**：只统计有效订单（PROCESSING、SHIPPED、DELIVERED），排除已取消和已退款订单
- **订单去重**：按父订单去重统计（一个父订单可能包含多个子订单）
- **货币统一**：所有金额统一为CNY（人民币）
- **时间范围**：支持按日期范围或天数查询

### 6. 数据一致性保证
- 所有统计API都使用 `UnifiedStatisticsService` 确保统计口径一致
- 订单数统一按父订单去重
- GMV、成本、利润统一为CNY
- 延误率统一计算：发货时间 > 预期最晚发货时间的订单占比（与订单列表的延误率是同一数据）

### 7. 回款数据查询
- **方法**：`/api/analytics/payment-collection`
- **描述**：获取回款统计数据
- **回款逻辑**：已签收（DELIVERED）的订单，签收时间加8天后计入回款金额
- **返回字段**：
  - `table_data`: 按日期和店铺分组的回款金额
  - `summary`: 汇总信息（总回款金额、总订单数）
  - `period`: 日期范围

### 8. 备货计划数据查询
- **方法**：`/api/inventory-planning/stock-plan`
- **描述**：根据过去N天的回款数据和销量数据，生成未来一周/月的按SKU备货计划
- **参数**：
  - `shop_ids`: 店铺ID列表（可选）
  - `past_days`: 过去N天的数据用于分析（默认7天）
  - `future_period`: 备货周期（week=一周，month=一个月）
- **返回字段**（每个SKU）：
  - `sku`: SKU货号
  - `product_name`: 商品名称
  - `manager`: 负责人
  - `past_period`: 过去N天的数据（销量、订单数、GMV、回款金额、回款数量、回款率）
  - `prediction`: 预测数据（日均销量、预测未来销量）
  - `suggestion`: 备货建议（建议备货数量、安全系数、优先级）

### 9. 备货计划制定能力（重要）
当用户询问"制定备货计划"、"根据回款和销量制定备货计划"、"未来一周/月的备货计划"等问题时，你需要：

**方法一：使用备货计划API（必须使用，强烈推荐）**
- **API端点**：`/api/inventory-planning/stock-plan`
- **参数**：
  - `past_days`: 过去N天的数据用于分析（默认7天）
  - `future_period`: 备货周期（week=一周，month=一个月）
  - `shop_ids`: 店铺ID列表（可选）
- **返回数据**：包含每个SKU货号（product_sku）的过去销量、回款数据、预测销量和备货建议
- **重要**：
  - **必须使用此API生成备货计划**，不要使用其他SKU统计API
  - 备货计划API按 `product_sku`（SKU货号）统计，这是订单表中的 `product_sku` 字段，对应原始数据中的 extCode 字段值（如 LBB3-1-US）
  - **不要使用** `/api/statistics/unified/sku-ranking` 或类似API，因为它们可能按SKU ID统计，而不是SKU货号

**方法二：手动分析（仅在备货计划API不可用时使用，不推荐）**
1. **分析过去一周的数据**：
   - **注意**：如果必须手动分析，需要确保按SKU货号（product_sku）统计，不是按SKU ID统计
   - 获取过去7天的回款数据（使用 `/api/analytics/payment-collection?days=7`）
   - 从订单数据中按 `Order.product_sku` 字段分组统计销量
   - 分析每个SKU货号的销量趋势和回款情况
2. **预测未来需求**：
   - 计算日均销量 = 过去7天总销量 / 7
   - 预测未来销量 = 日均销量 × 未来天数（7天或30天）
   - 考虑回款率，评估资金回笼情况
3. **生成备货计划**：
   - 建议备货数量 = 预测销量 × 安全系数（建议1.2-1.5倍）
   - **必须按SKU货号（product_sku）列出备货计划**，这是订单表中的 `product_sku` 字段，对应原始数据中的 extCode 字段值（如 LBB3-1-US）
   - 标注优先级（高/中/低，基于过去销量）
   - 考虑回款情况，优先备货回款率高的SKU

**输出格式要求**：
- **文字说明**：备货计划的总体思路和建议，包括：
  - 分析周期（过去7天）
  - 备货周期（未来一周或一个月）
  - 总体备货建议和注意事项
- **表格数据**：按SKU货号（product_sku）列出详细的备货计划，包含：
  - SKU货号（product_sku，对应订单表中的 product_sku 字段，如 LBB3-1-US）
  - 商品名称
  - 负责人
  - 过去7天销量
  - 过去7天回款金额
  - 日均销量
  - 预测未来销量（7天或30天）
  - 建议备货数量
  - 优先级（高/中/低）
- **决策卡片（可选）**：如果用户明确要求，可以输出决策卡片JSON，action类型为"备货计划"
  - **重要**：决策卡片中的SKU字段必须是SKU货号（product_sku，如 LBB3-1-US），不能是SKU ID（纯数字）
  - 决策卡片中的每个item的id字段应该使用备货计划API返回的 `sku` 字段值（即product_sku）

**备货计划示例输出**：
```
根据过去7天的回款数据和销量分析，以下是未来一周的备货计划：

**分析周期**：过去7天（2024-11-21 至 2024-11-28）
**备货周期**：未来7天（2024-11-29 至 2024-12-05）

**备货计划表**（按SKU货号 product_sku 统计）：

| SKU货号 | 商品名称 | 负责人 | 过去7天销量 | 过去7天回款 | 日均销量 | 预测未来7天销量 | 建议备货数量 | 优先级 |
|---------|---------|--------|------------|------------|---------|----------------|------------|--------|
| LBB3-1-US | 商品A | 张三 | 140 | ¥14,000 | 20 | 140 | 182 | 高 |
| LBB4-A-US | 商品B | 李四 | 70 | ¥7,000 | 10 | 70 | 91 | 中 |
...

**总体建议**：
1. 优先备货高优先级SKU（过去7天销量>100）
2. 考虑回款情况，优先备货回款率高的SKU
3. 建议备货数量已考虑1.3倍安全系数
4. 建议每周更新备货计划，根据实际销售情况调整
```

### 10. 数据使用建议
- **引用数据时**：明确说明数据来源和时间范围
- **对比分析时**：确保使用相同的时间范围和过滤条件
- **趋势分析时**：使用每日统计数据，注意日期格式的一致性
- **SKU分析时**：使用SKU统计数据，注意SKU ID和商品名称的对应关系
- **备货计划时**：结合回款数据和销量数据，考虑资金回笼和销售趋势。**必须按SKU货号（product_sku）统计**，这是订单表中的 `product_sku` 字段，对应原始数据中的 extCode 字段值（如 LBB3-1-US），而不是按SKU ID统计

当前系统提供了以下运营数据，请基于这些数据回答用户的问题，并提供有价值的分析和建议。当问题需要决策建议时，务必输出决策卡片JSON。

"""
        return system_prompt + context
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


# 创建全局服务实例
frog_gpt_service = FrogGPTService()
