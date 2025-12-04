"""
FrogGPT AI模块API
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx
from loguru import logger
import traceback
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.frog_gpt_service import frog_gpt_service
from app.services.unified_statistics import UnifiedStatisticsService
import base64
import io

router = APIRouter(prefix="/frog-gpt", tags=["FrogGPT"])


class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str  # user, assistant, system
    content: str


class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    include_system_data: bool = True  # 是否包含系统数据上下文
    data_summary_days: Optional[int] = None  # 数据摘要天数，None表示全部时间数据
    shop_id: Optional[int] = None  # 店铺ID（可选，用于筛选数据）


class ChatResponse(BaseModel):
    """聊天响应模型"""
    id: str
    model: str
    content: str  # 提取的消息内容
    choices: Optional[List[Dict[str, Any]]] = None
    usage: Optional[Dict[str, Any]] = None


class ModelsResponse(BaseModel):
    """模型列表响应"""
    models: List[Dict[str, Any]]


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    发送聊天消息
    
    支持：
    - 文本对话
    - 系统数据上下文（可选）
    - 自定义模型和参数
    """
    try:
        # 构建消息列表
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # 如果需要包含系统数据上下文，在消息前添加系统提示
        if request.include_system_data:
            try:
                # 使用统一端点逻辑获取系统数据摘要（带缓存，性能更好）
                from app.api.statistics_unified import get_cached_or_compute, generate_cache_key
                import json
                
                # 如果提供了shop_id，只获取该店铺的数据
                shop_ids = [request.shop_id] if request.shop_id else None
                
                # 构建缓存键
                params = {
                    "shop_ids": sorted(shop_ids) if shop_ids else None,
                    "days": request.data_summary_days,
                }
                cache_key = generate_cache_key("summary", params)
                
                def compute():
                    # 解析日期范围
                    start_dt, end_dt = UnifiedStatisticsService.parse_date_range(
                        None, None, request.data_summary_days
                    )
                    
                    # 构建查询条件
                    filters = UnifiedStatisticsService.build_base_filters(
                        db, start_dt, end_dt, shop_ids, None, None, None
                    )
                    
                    # 计算总览统计
                    overview = UnifiedStatisticsService.calculate_order_statistics(db, filters)
                    
                    # 计算利润率
                    profit_margin = (
                        (overview['total_profit'] / overview['total_gmv'] * 100)
                        if overview['total_gmv'] > 0 else 0
                    )
                    
                    # 获取Top SKU（前10）
                    top_skus = UnifiedStatisticsService.get_sku_statistics(db, filters, limit=10)
                    
                    # 获取Top负责人（前10）
                    top_managers = UnifiedStatisticsService.get_manager_statistics(db, filters)[:10]
                    
                    return {
                        "overview": {
                            "total_orders": overview['order_count'],
                            "total_quantity": overview['total_quantity'],
                            "total_gmv": round(overview['total_gmv'], 2),
                            "total_cost": round(overview['total_cost'], 2),
                            "total_profit": round(overview['total_profit'], 2),
                            "profit_margin": round(profit_margin, 2),
                            "delay_rate": round(overview.get('delay_rate', 0), 2),
                            "delay_count": overview.get('delay_count', 0),
                        },
                        "top_skus": top_skus,
                        "top_managers": top_managers,
                    }
                
                # 获取数据（带缓存）
                summary_data = get_cached_or_compute(
                    cache_key,
                    compute,
                    ttl=300,  # 5分钟缓存
                    use_redis=True
                )
                
                # 转换为AI模块需要的格式
                data_summary = {
                    "overview": summary_data["overview"],
                    "top_skus": summary_data["top_skus"],
                    "top_managers": summary_data["top_managers"],
                }
                
                # 构建系统上下文
                system_context = frog_gpt_service.build_system_context(data_summary)
                
                # 在消息列表前添加系统消息
                messages.insert(0, {
                    "role": "system",
                    "content": system_context
                })
            except Exception as e:
                # 如果获取数据失败，记录错误但继续执行（不包含系统上下文）
                logger.warning(f"获取系统数据摘要失败，将不包含系统上下文: {e}")
                logger.debug(traceback.format_exc())
        
        # 检查是否有 API Key
        api_key = frog_gpt_service.get_api_key(db)
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="未配置 OpenRouter API Key，请在高级设置中配置 API Key"
            )
        
        # 记录请求信息（用于调试）
        logger.info(f"收到聊天请求: model={request.model}, temperature={request.temperature}, messages_count={len(messages)}, include_system_data={request.include_system_data}")
        
        # 调用OpenRouter API（传递db以从数据库读取API key）
        response = await frog_gpt_service.chat_completion(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            db=db
        )
        
        # OpenRouter返回标准格式，提取内容
        # 格式: {"id": "...", "model": "...", "choices": [{"message": {"role": "assistant", "content": "..."}}]}
        logger.info(f"OpenRouter API 响应: type={type(response)}, keys={list(response.keys()) if isinstance(response, dict) else 'N/A'}")
        
        if isinstance(response, dict):
            if "choices" in response and len(response.get("choices", [])) > 0:
                message = response["choices"][0].get("message", {})
                content = message.get("content", "")
                
                logger.info(f"提取响应内容: content_length={len(content) if content else 0}, model={response.get('model', 'unknown')}")
                
                if not content:
                    logger.warning(f"响应内容为空: response={response}")
                    raise HTTPException(
                        status_code=500,
                        detail="OpenRouter API 返回的内容为空"
                    )
                
                # 返回标准化的响应格式
                return {
                    "id": response.get("id", ""),
                    "model": response.get("model", request.model or "unknown"),
                    "content": content,
                    "choices": response.get("choices", []),
                    "usage": response.get("usage"),
                }
            else:
                # 如果没有 choices，尝试直接返回响应或提取错误信息
                error_message = response.get("error", {}).get("message", "OpenRouter API 返回了无效的响应格式")
                logger.error(f"OpenRouter API 响应格式错误: response={response}")
                raise HTTPException(
                    status_code=500,
                    detail=f"OpenRouter API 响应格式错误: {error_message}"
                )
        else:
            logger.error(f"OpenRouter API 返回了无效的响应类型: type={type(response)}, value={response}")
            raise HTTPException(
                status_code=500,
                detail=f"OpenRouter API 返回了无效的响应类型: {type(response)}"
            )
    
    except HTTPException:
        # 重新抛出 HTTPException
        raise
    except ValueError as e:
        # 参数验证错误（包括 OpenRouter API 返回的 ValueError）
        error_msg = str(e)
        logger.error(f"请求参数错误: {error_msg}")
        # 检查是否是 API Key 相关错误
        if "API Key" in error_msg or "未配置" in error_msg or "无效" in error_msg or "过期" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        elif "模型不存在" in error_msg or "模型名称" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=f"请求参数错误: {error_msg}")
    except httpx.HTTPStatusError as e:
        # OpenRouter API HTTP 错误
        error_detail = f"OpenRouter API 请求失败 (HTTP {e.response.status_code})"
        try:
            error_response = e.response.json()
            error_info = error_response.get("error", {})
            error_message = error_info.get("message", str(e))
            error_type = error_info.get("type", "")
            
            # 根据错误类型提供更详细的错误信息
            if e.response.status_code == 401:
                error_detail = "OpenRouter API Key 无效或已过期，请检查 API Key 配置"
            elif e.response.status_code == 403:
                error_detail = f"OpenRouter API 访问被拒绝: {error_message}. 请检查 API Key 权限或账户余额"
            elif e.response.status_code == 429:
                error_detail = "OpenRouter API 请求频率过高，请稍后重试"
            else:
                error_detail = f"OpenRouter API 错误 ({e.response.status_code}): {error_message}"
            
            logger.error(f"OpenRouter API 请求失败: {error_detail}, 完整响应: {error_response}")
        except:
            error_text = e.response.text[:500] if e.response.text else "无响应内容"
            error_detail = f"OpenRouter API 错误 ({e.response.status_code}): {error_text}"
            logger.error(f"OpenRouter API 请求失败: {error_detail}")
        
        # 根据 HTTP 状态码返回相应的状态码
        if e.response.status_code == 401:
            raise HTTPException(status_code=401, detail=error_detail)
        elif e.response.status_code == 403:
            raise HTTPException(status_code=403, detail=error_detail)
        elif e.response.status_code == 429:
            raise HTTPException(status_code=429, detail=error_detail)
        else:
            raise HTTPException(status_code=502, detail=error_detail)
    except httpx.TimeoutException as e:
        logger.error(f"OpenRouter API 请求超时: {e}")
        raise HTTPException(status_code=504, detail="OpenRouter API 请求超时，请稍后重试")
    except httpx.RequestError as e:
        logger.error(f"OpenRouter API 请求错误: {e}")
        raise HTTPException(status_code=502, detail=f"无法连接到 OpenRouter API: {str(e)}")
    except Exception as e:
        logger.error(f"AI服务错误: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"AI服务错误: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    发送流式聊天消息（SSE）
    
    支持：
    - 文本对话
    - 系统数据上下文（可选）
    - 自定义模型和参数
    - Server-Sent Events (SSE) 流式响应
    """
    async def generate():
        try:
            # 构建消息列表
            messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
            
            # 如果需要包含系统数据上下文，在消息前添加系统提示
            if request.include_system_data:
                try:
                    # 使用统一端点逻辑获取系统数据摘要（带缓存，性能更好）
                    from app.api.statistics_unified import get_cached_or_compute, generate_cache_key
                    
                    # 如果提供了shop_id，只获取该店铺的数据
                    shop_ids = [request.shop_id] if request.shop_id else None
                    
                    # 构建缓存键
                    params = {
                        "shop_ids": sorted(shop_ids) if shop_ids else None,
                        "days": request.data_summary_days,
                    }
                    cache_key = generate_cache_key("summary", params)
                    
                    def compute():
                        # 解析日期范围
                        start_dt, end_dt = UnifiedStatisticsService.parse_date_range(
                            None, None, request.data_summary_days
                        )
                        
                        # 构建查询条件
                        filters = UnifiedStatisticsService.build_base_filters(
                            db, start_dt, end_dt, shop_ids, None, None, None
                        )
                        
                        # 计算总览统计
                        overview = UnifiedStatisticsService.calculate_order_statistics(db, filters)
                        
                        # 计算利润率
                        profit_margin = (
                            (overview['total_profit'] / overview['total_gmv'] * 100)
                            if overview['total_gmv'] > 0 else 0
                        )
                        
                        # 获取Top SKU（前10）
                        top_skus = UnifiedStatisticsService.get_sku_statistics(db, filters, limit=10)
                        
                        # 获取Top负责人（前10）
                        top_managers = UnifiedStatisticsService.get_manager_statistics(db, filters)[:10]
                        
                        return {
                            "overview": {
                                "total_orders": overview['order_count'],
                                "total_quantity": overview['total_quantity'],
                                "total_gmv": round(overview['total_gmv'], 2),
                                "total_cost": round(overview['total_cost'], 2),
                                "total_profit": round(overview['total_profit'], 2),
                                "profit_margin": round(profit_margin, 2),
                                "delay_rate": round(overview.get('delay_rate', 0), 2),
                                "delay_count": overview.get('delay_count', 0),
                            },
                            "top_skus": top_skus,
                            "top_managers": top_managers,
                        }
                    
                    # 获取数据（带缓存）
                    summary_data = get_cached_or_compute(
                        cache_key,
                        compute,
                        ttl=300,  # 5分钟缓存
                        use_redis=True
                    )
                    
                    # 转换为AI模块需要的格式
                    data_summary = {
                        "overview": summary_data["overview"],
                        "top_skus": summary_data["top_skus"],
                        "top_managers": summary_data["top_managers"],
                    }
                    
                    system_context = frog_gpt_service.build_system_context(data_summary)
                    messages.insert(0, {
                        "role": "system",
                        "content": system_context
                    })
                except Exception as e:
                    logger.warning(f"获取系统数据摘要失败，将不包含系统上下文: {e}")
            
            # 检测供应商
            provider = frog_gpt_service._detect_provider_from_model(request.model or frog_gpt_service.default_model)
            
            # 检查是否有 API Key（根据供应商）
            api_key = frog_gpt_service.get_api_key(db, provider)
            if not api_key:
                provider_name = "OpenRouter" if provider == "openrouter" else provider.upper()
                yield f"data: {json.dumps({'type': 'error', 'error': f'未配置 {provider_name} API Key，请在高级设置中配置 API Key'})}\n\n"
                return
            
            logger.info(f"收到流式聊天请求: model={request.model}, provider={provider}, temperature={request.temperature}, messages_count={len(messages)}")
            
            # 调用流式方法
            async for chunk in frog_gpt_service.chat_completion_stream(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                db=db
            ):
                # 将数据块转换为 SSE 格式
                yield f"data: {json.dumps(chunk)}\n\n"
                
        except Exception as e:
            logger.error(f"流式聊天错误: {e}")
            logger.error(traceback.format_exc())
            error_chunk = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        }
    )


@router.post("/chat/with-files")
async def chat_with_files(
    messages: str = Form(...),  # JSON字符串
    files: Optional[List[UploadFile]] = File(None),
    model: Optional[str] = Form(None),
    temperature: Optional[float] = Form(0.7),
    include_system_data: bool = Form(True),
    data_summary_days: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    发送带文件的聊天消息
    
    支持：
    - 文本消息
    - 文件上传（图片、文档等）
    - 系统数据上下文（可选）
    """
    import json
    
    try:
        # 解析消息
        messages_data = json.loads(messages)
        message_list = [{"role": msg["role"], "content": msg["content"]} for msg in messages_data]
        
        # 处理文件
        if files:
            for file in files:
                # 读取文件内容
                content = await file.read()
                
                # 根据文件类型处理
                if file.content_type and file.content_type.startswith("image/"):
                    # 图片：转换为base64
                    base64_content = base64.b64encode(content).decode("utf-8")
                    image_url = f"data:{file.content_type};base64,{base64_content}"
                    
                    # 添加到消息中（OpenRouter支持图片URL）
                    message_list.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    })
                else:
                    # 文本文件：读取内容
                    try:
                        text_content = content.decode("utf-8")
                        message_list.append({
                            "role": "user",
                            "content": f"[文件: {file.filename}]\n{text_content}"
                        })
                    except:
                        # 如果不是文本文件，跳过
                        pass
        
        # 如果需要包含系统数据上下文
        if include_system_data:
            try:
                # 使用统一端点逻辑获取系统数据摘要（带缓存，性能更好）
                from app.api.statistics_unified import get_cached_or_compute, generate_cache_key
                
                # 构建缓存键
                params = {
                    "shop_ids": None,
                    "days": data_summary_days,
                }
                cache_key = generate_cache_key("summary", params)
                
                def compute():
                    # 解析日期范围
                    start_dt, end_dt = UnifiedStatisticsService.parse_date_range(
                        None, None, data_summary_days
                    )
                    
                    # 构建查询条件
                    filters = UnifiedStatisticsService.build_base_filters(
                        db, start_dt, end_dt, None, None, None, None
                    )
                    
                    # 计算总览统计
                    overview = UnifiedStatisticsService.calculate_order_statistics(db, filters)
                    
                    # 计算利润率
                    profit_margin = (
                        (overview['total_profit'] / overview['total_gmv'] * 100)
                        if overview['total_gmv'] > 0 else 0
                    )
                    
                    # 获取Top SKU（前10）
                    top_skus = UnifiedStatisticsService.get_sku_statistics(db, filters, limit=10)
                    
                    # 获取Top负责人（前10）
                    top_managers = UnifiedStatisticsService.get_manager_statistics(db, filters)[:10]
                    
                    return {
                        "overview": {
                            "total_orders": overview['order_count'],
                            "total_quantity": overview['total_quantity'],
                            "total_gmv": round(overview['total_gmv'], 2),
                            "total_cost": round(overview['total_cost'], 2),
                            "total_profit": round(overview['total_profit'], 2),
                            "profit_margin": round(profit_margin, 2),
                            "delay_rate": round(overview.get('delay_rate', 0), 2),
                            "delay_count": overview.get('delay_count', 0),
                        },
                        "top_skus": top_skus,
                        "top_managers": top_managers,
                    }
                
                # 获取数据（带缓存）
                summary_data = get_cached_or_compute(
                    cache_key,
                    compute,
                    ttl=300,  # 5分钟缓存
                    use_redis=True
                )
                
                # 转换为AI模块需要的格式
                data_summary = {
                    "overview": summary_data["overview"],
                    "top_skus": summary_data["top_skus"],
                    "top_managers": summary_data["top_managers"],
                }
                
                system_context = frog_gpt_service.build_system_context(data_summary)
                message_list.insert(0, {
                    "role": "system",
                    "content": system_context
                })
            except Exception as e:
                pass
        
        # 检查是否有 API Key
        api_key = frog_gpt_service.get_api_key(db)
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="未配置 OpenRouter API Key，请在高级设置中配置 API Key"
            )
        
        # 调用OpenRouter API（传递db以从数据库读取API key）
        response = await frog_gpt_service.chat_completion(
            messages=message_list,
            model=model,
            temperature=temperature,
            db=db
        )
        
        # 标准化响应格式，与 /chat 端点保持一致
        # 格式: {"id": "...", "model": "...", "choices": [{"message": {"role": "assistant", "content": "..."}}]}
        if isinstance(response, dict):
            if "choices" in response and len(response.get("choices", [])) > 0:
                message = response["choices"][0].get("message", {})
                content = message.get("content", "")
                
                if not content:
                    logger.warning(f"响应内容为空: response={response}")
                    raise HTTPException(
                        status_code=500,
                        detail="OpenRouter API 返回的内容为空"
                    )
                
                # 返回标准化的响应格式（与 /chat 端点一致）
                return {
                    "id": response.get("id", ""),
                    "model": response.get("model", model or "unknown"),
                    "content": content,
                    "choices": response.get("choices", []),
                    "usage": response.get("usage"),
                }
            else:
                # 如果没有 choices，尝试直接返回响应或提取错误信息
                error_message = response.get("error", {}).get("message", "OpenRouter API 返回了无效的响应格式")
                logger.error(f"OpenRouter API 响应格式错误: response={response}")
                raise HTTPException(
                    status_code=500,
                    detail=f"OpenRouter API 响应格式错误: {error_message}"
                )
        else:
            logger.error(f"OpenRouter API 返回了无效的响应类型: type={type(response)}, value={response}")
            raise HTTPException(
                status_code=500,
                detail=f"OpenRouter API 返回了无效的响应类型: {type(response)}"
            )
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="消息格式错误")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI服务错误: {str(e)}")


@router.get("/models", response_model=ModelsResponse)
async def get_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取可用的AI模型列表
    
    从 OpenRouter API 获取最新的模型列表。
    需要配置 OpenRouter API Key 才能获取完整列表。
    """
    try:
        # 检查是否有 API Key
        api_key = frog_gpt_service.get_api_key(db)
        if not api_key:
            # 如果没有 API Key，返回提示信息
            return {
                "models": [],
                "message": "请先配置 OpenRouter API Key 以获取模型列表"
            }
        
        models = await frog_gpt_service.get_models(db=db)
        return {"models": models}
    except Exception as e:
        from loguru import logger
        logger.error(f"获取模型列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")


@router.get("/data-summary")
async def get_data_summary_for_ai(
    days: Optional[int] = None,
    shop_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取系统数据摘要（供AI使用）
    
    使用统一端点获取数据，带缓存优化
    
    Args:
        days: 统计天数，如果为None则获取全部历史数据
        shop_id: 店铺ID（可选，用于筛选数据）
    """
    try:
        # 使用统一端点逻辑获取数据摘要（带缓存，性能更好）
        from app.api.statistics_unified import get_cached_or_compute, generate_cache_key
        
        shop_ids = [shop_id] if shop_id else None
        
        # 构建缓存键
        params = {
            "shop_ids": sorted(shop_ids) if shop_ids else None,
            "days": days,
        }
        cache_key = generate_cache_key("summary", params)
        
        def compute():
            # 解析日期范围
            start_dt, end_dt = UnifiedStatisticsService.parse_date_range(
                None, None, days
            )
            
            # 构建查询条件
            filters = UnifiedStatisticsService.build_base_filters(
                db, start_dt, end_dt, shop_ids, None, None, None
            )
            
            # 计算总览统计
            overview = UnifiedStatisticsService.calculate_order_statistics(db, filters)
            
            # 计算利润率
            profit_margin = (
                (overview['total_profit'] / overview['total_gmv'] * 100)
                if overview['total_gmv'] > 0 else 0
            )
            
            # 获取Top SKU（前10）
            top_skus = UnifiedStatisticsService.get_sku_statistics(db, filters, limit=10)
            
            # 获取Top负责人（前10）
            top_managers = UnifiedStatisticsService.get_manager_statistics(db, filters)[:10]
            
            return {
                "overview": {
                    "total_orders": overview['order_count'],
                    "total_quantity": overview['total_quantity'],
                    "total_gmv": round(overview['total_gmv'], 2),
                    "total_cost": round(overview['total_cost'], 2),
                    "total_profit": round(overview['total_profit'], 2),
                    "profit_margin": round(profit_margin, 2),
                    "delay_rate": round(overview.get('delay_rate', 0), 2),
                    "delay_count": overview.get('delay_count', 0),
                },
                "top_skus": top_skus,
                "top_managers": top_managers,
                "period": {
                    "start_date": start_dt.isoformat() if start_dt else None,
                    "end_date": end_dt.isoformat() if end_dt else None,
                }
            }
        
        # 获取数据（带缓存）
        return get_cached_or_compute(
            cache_key,
            compute,
            ttl=300,  # 5分钟缓存
            use_redis=True
        )
    except Exception as e:
        logger.error(f"获取数据摘要失败: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"获取数据摘要失败: {str(e)}")


class OpenRouterConfigResponse(BaseModel):
    """OpenRouter配置响应"""
    api_key: str = ""  # 部分隐藏的API key
    has_api_key: bool = False  # 是否有API key


class OpenRouterConfigUpdate(BaseModel):
    """OpenRouter配置更新"""
    api_key: str = ""


class AllProvidersApiKeysUpdate(BaseModel):
    """所有供应商API Key更新"""
    openrouter: Optional[str] = None
    openai: Optional[str] = None
    anthropic: Optional[str] = None
    gemini: Optional[str] = None
    deepseek: Optional[str] = None


@router.get("/api-config", response_model=OpenRouterConfigResponse)
def get_openrouter_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取OpenRouter API配置"""
    from app.models.system_config import SystemConfig
    
    config = db.query(SystemConfig).filter(SystemConfig.key == "openrouter_api_key").first()
    api_key = config.value if config and config.value else ""
    
    # 部分隐藏API key（只显示前8位和后4位）
    masked_key = ""
    if api_key:
        if len(api_key) > 12:
            masked_key = api_key[:8] + "..." + api_key[-4:]
        else:
            masked_key = api_key[:4] + "..." + api_key[-2:] if len(api_key) > 6 else "***"
    
    return {
        "api_key": masked_key,
        "has_api_key": bool(api_key)
    }


class FullApiKeyResponse(BaseModel):
    """完整API key响应"""
    api_key: str
    has_api_key: bool


@router.get("/api-config/full")
def get_full_openrouter_api_key(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取完整的OpenRouter API key（用于显示）"""
    from app.models.system_config import SystemConfig
    
    config = db.query(SystemConfig).filter(SystemConfig.key == "openrouter_api_key").first()
    api_key = config.value if config and config.value else ""
    
    return {
        "api_key": api_key,
        "has_api_key": bool(api_key)
    }


@router.get("/api-config/all-providers")
def get_all_providers_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有AI提供商的完整API key"""
    from app.models.system_config import SystemConfig
    
    def get_full_key(key: str) -> str:
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        return config.value if config and config.value else ""
    
    return {
        "openrouter": {
            "api_key": get_full_key("openrouter_api_key"),
            "has_api_key": bool(get_full_key("openrouter_api_key"))
        },
        "openai": {
            "api_key": get_full_key("openai_api_key"),
            "has_api_key": bool(get_full_key("openai_api_key"))
        },
        "anthropic": {
            "api_key": get_full_key("anthropic_api_key"),
            "has_api_key": bool(get_full_key("anthropic_api_key"))
        },
        "gemini": {
            "api_key": get_full_key("gemini_api_key"),
            "has_api_key": bool(get_full_key("gemini_api_key"))
        },
        "deepseek": {
            "api_key": get_full_key("deepseek_api_key"),
            "has_api_key": bool(get_full_key("deepseek_api_key"))
        }
    }


@router.put("/api-config")
def update_openrouter_config(
    config: OpenRouterConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新OpenRouter API配置"""
    from app.models.system_config import SystemConfig
    
    # 如果API key为空，不更新（保留原值）
    if not config.api_key:
        return {"message": "API key未更新（保留原值）"}
    
    # 更新或创建配置
    api_key_config = db.query(SystemConfig).filter(SystemConfig.key == "openrouter_api_key").first()
    if api_key_config:
        api_key_config.value = config.api_key
    else:
        api_key_config = SystemConfig(
            key="openrouter_api_key",
            value=config.api_key,
            description="OpenRouter API密钥",
            is_encrypted=True
        )
        db.add(api_key_config)
    
    db.commit()
    
    return {"message": "OpenRouter API配置更新成功"}


@router.get("/api-config/verify")
async def verify_api_key(
    provider: str = "openrouter",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """验证API Key是否有效"""
    
    try:
        if provider == "openrouter":
            api_key = frog_gpt_service.get_api_key(db)
            if not api_key:
                return {
                    "valid": False,
                    "message": "未配置 OpenRouter API Key"
                }
            
            # 尝试获取模型列表来验证
            models = await frog_gpt_service.get_models(db=db)
            if models and len(models) > 0:
                return {
                    "valid": True,
                    "message": f"API Key 有效，可访问 {len(models)} 个模型",
                    "models_count": len(models)
                }
            else:
                return {
                    "valid": False,
                    "message": "API Key 可能无效或无法访问模型列表"
                }
        else:
            return {
                "valid": False,
                "message": f"暂不支持验证 {provider} 的 API Key"
            }
    except Exception as e:
        logger.error(f"验证 API Key 失败: {e}")
        logger.error(traceback.format_exc())
        return {
            "valid": False,
            "message": f"验证失败: {str(e)}"
        }


@router.put("/api-config/all-providers")
async def update_all_providers_api_keys(
    config: AllProvidersApiKeysUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新所有供应商的API Key配置"""
    from app.models.system_config import SystemConfig
    
    def update_or_create_key(key: str, value: Optional[str], description: str):
        """更新或创建API Key配置"""
        if value is None or value == "":
            return  # 不更新空值
        
        config_item = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if config_item:
            config_item.value = value
        else:
            config_item = SystemConfig(
                key=key,
                value=value,
                description=description,
                is_encrypted=True
            )
            db.add(config_item)
    
    # 更新各个供应商的API Key
    updated_keys = []
    if config.openrouter:
        update_or_create_key("openrouter_api_key", config.openrouter, "OpenRouter API密钥")
        updated_keys.append("OpenRouter")
    if config.openai:
        update_or_create_key("openai_api_key", config.openai, "OpenAI API密钥")
        updated_keys.append("OpenAI")
    if config.anthropic:
        update_or_create_key("anthropic_api_key", config.anthropic, "Anthropic API密钥")
        updated_keys.append("Anthropic")
    if config.gemini:
        update_or_create_key("gemini_api_key", config.gemini, "Google Gemini API密钥")
        updated_keys.append("Gemini")
    
    db.commit()
    
    # 如果更新了 OpenRouter API Key，尝试验证
    if config.openrouter:
        try:
            models = await frog_gpt_service.get_models(db=db)
            if models and len(models) > 0:
                return {
                    "message": f"API Key配置更新成功（已更新: {', '.join(updated_keys)}）",
                    "verified": True,
                    "models_count": len(models)
                }
        except Exception as e:
            logger.warning(f"OpenRouter API Key验证失败: {e}")
            return {
                "message": f"API Key已保存，但验证失败: {str(e)}",
                "verified": False,
                "updated_keys": updated_keys
            }
    
    return {
        "message": f"API Key配置更新成功（已更新: {', '.join(updated_keys) if updated_keys else '无'}）",
        "updated_keys": updated_keys
    }


class TestConnectionResponse(BaseModel):
    """测试连接响应"""
    success: bool
    message: str
    response_content: Optional[str] = None
    model_used: Optional[str] = None


@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_connection(
    model: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    测试 OpenRouter API 连接，发送一个简单的测试消息验证是否能获得回复
    """
    
    try:
        # 使用默认模型或指定的模型（如果没有指定，使用 auto）
        test_model = model or "auto"
        
        # 构建测试消息
        test_messages = [
            {
                "role": "user",
                "content": "Hello, please reply with 'OK' to confirm the connection is working."
            }
        ]
        
        logger.info(f"测试 OpenRouter 连接: model={test_model}")
        
        # 调用 OpenRouter API
        response = await frog_gpt_service.chat_completion(
            messages=test_messages,
            model=test_model,
            temperature=0.7,
            db=db
        )
        
        # 提取响应内容
        if isinstance(response, dict) and "choices" in response and len(response.get("choices", [])) > 0:
            message = response["choices"][0].get("message", {})
            content = message.get("content", "")
            model_used = response.get("model", test_model)
            
            logger.info(f"测试连接成功: model={model_used}, response_length={len(content)}")
            
            return TestConnectionResponse(
                success=True,
                message="连接测试成功！OpenRouter API 可以正常响应。",
                response_content=content,
                model_used=model_used
            )
        else:
            logger.error(f"测试连接失败: 响应格式错误, response={response}")
            return TestConnectionResponse(
                success=False,
                message="连接测试失败: OpenRouter API 返回了无效的响应格式",
                response_content=None,
                model_used=test_model
            )
            
    except ValueError as e:
        error_msg = str(e)
        logger.error(f"测试连接失败: {error_msg}")
        return TestConnectionResponse(
            success=False,
            message=f"连接测试失败: {error_msg}",
            response_content=None,
            model_used=test_model if 'test_model' in locals() else None
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"测试连接异常: {error_msg}")
        logger.error(traceback.format_exc())
        return TestConnectionResponse(
            success=False,
            message=f"连接测试异常: {error_msg}",
            response_content=None,
            model_used=test_model if 'test_model' in locals() else None
        )

