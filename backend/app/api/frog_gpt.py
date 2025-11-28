"""
FrogGPT AI模块API
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel

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
    data_summary_days: int = 7  # 数据摘要天数


class ChatResponse(BaseModel):
    """聊天响应模型"""
    id: str
    model: str
    choices: List[Dict[str, Any]]
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
                # 获取系统数据摘要
                start_dt, end_dt = UnifiedStatisticsService.parse_date_range(
                    None, None, request.data_summary_days
                )
                filters = UnifiedStatisticsService.build_base_filters(
                    db, start_dt, end_dt, None, None, None, None
                )
                overview = UnifiedStatisticsService.calculate_order_statistics(db, filters)
                top_skus = UnifiedStatisticsService.get_sku_statistics(db, filters, limit=10)
                top_managers = UnifiedStatisticsService.get_manager_statistics(db, filters)[:10]
                profit_margin = (overview['total_profit'] / overview['total_gmv'] * 100) if overview['total_gmv'] > 0 else 0
                
                data_summary = {
                    "overview": {
                        "total_orders": overview['order_count'],
                        "total_quantity": overview['total_quantity'],
                        "total_gmv": round(overview['total_gmv'], 2),
                        "total_cost": round(overview['total_cost'], 2),
                        "total_profit": round(overview['total_profit'], 2),
                        "profit_margin": round(profit_margin, 2),
                    },
                    "top_skus": top_skus,
                    "top_managers": top_managers,
                }
                
                # 构建系统上下文
                system_context = frog_gpt_service.build_system_context(data_summary)
                
                # 在消息列表前添加系统消息
                messages.insert(0, {
                    "role": "system",
                    "content": system_context
                })
            except Exception as e:
                # 如果获取数据失败，继续但不包含系统上下文
                pass
        
        # 调用OpenRouter API（传递db以从数据库读取API key）
        response = await frog_gpt_service.chat_completion(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            db=db
        )
        
        return response
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI服务错误: {str(e)}")


@router.post("/chat/with-files")
async def chat_with_files(
    messages: str = Form(...),  # JSON字符串
    files: Optional[List[UploadFile]] = File(None),
    model: Optional[str] = Form(None),
    temperature: Optional[float] = Form(0.7),
    include_system_data: bool = Form(True),
    data_summary_days: int = Form(7),
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
                # 获取系统数据摘要
                start_dt, end_dt = UnifiedStatisticsService.parse_date_range(
                    None, None, data_summary_days
                )
                filters = UnifiedStatisticsService.build_base_filters(
                    db, start_dt, end_dt, None, None, None, None
                )
                overview = UnifiedStatisticsService.calculate_order_statistics(db, filters)
                top_skus = UnifiedStatisticsService.get_sku_statistics(db, filters, limit=10)
                top_managers = UnifiedStatisticsService.get_manager_statistics(db, filters)[:10]
                profit_margin = (overview['total_profit'] / overview['total_gmv'] * 100) if overview['total_gmv'] > 0 else 0
                
                data_summary = {
                    "overview": {
                        "total_orders": overview['order_count'],
                        "total_quantity": overview['total_quantity'],
                        "total_gmv": round(overview['total_gmv'], 2),
                        "total_cost": round(overview['total_cost'], 2),
                        "total_profit": round(overview['total_profit'], 2),
                        "profit_margin": round(profit_margin, 2),
                    },
                    "top_skus": top_skus,
                    "top_managers": top_managers,
                }
                
                system_context = frog_gpt_service.build_system_context(data_summary)
                message_list.insert(0, {
                    "role": "system",
                    "content": system_context
                })
            except Exception as e:
                pass
        
        # 调用OpenRouter API（传递db以从数据库读取API key）
        response = await frog_gpt_service.chat_completion(
            messages=message_list,
            model=model,
            temperature=temperature,
            db=db
        )
        
        return response
    
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
    """
    try:
        models = await frog_gpt_service.get_models(db=db)
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")


@router.get("/data-summary")
async def get_data_summary_for_ai(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取系统数据摘要（供AI使用）
    """
    try:
        start_dt, end_dt = UnifiedStatisticsService.parse_date_range(
            None, None, days
        )
        filters = UnifiedStatisticsService.build_base_filters(
            db, start_dt, end_dt, None, None, None, None
        )
        overview = UnifiedStatisticsService.calculate_order_statistics(db, filters)
        top_skus = UnifiedStatisticsService.get_sku_statistics(db, filters, limit=10)
        top_managers = UnifiedStatisticsService.get_manager_statistics(db, filters)[:10]
        profit_margin = (overview['total_profit'] / overview['total_gmv'] * 100) if overview['total_gmv'] > 0 else 0
        
        return {
            "overview": {
                "total_orders": overview['order_count'],
                "total_quantity": overview['total_quantity'],
                "total_gmv": round(overview['total_gmv'], 2),
                "total_cost": round(overview['total_cost'], 2),
                "total_profit": round(overview['total_profit'], 2),
                "profit_margin": round(profit_margin, 2),
            },
            "top_skus": top_skus,
            "top_managers": top_managers,
            "period": {
                "start_date": start_dt.isoformat() if start_dt else None,
                "end_date": end_dt.isoformat() if end_dt else None,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据摘要失败: {str(e)}")


class OpenRouterConfigResponse(BaseModel):
    """OpenRouter配置响应"""
    api_key: str = ""  # 部分隐藏的API key
    has_api_key: bool = False  # 是否有API key


class OpenRouterConfigUpdate(BaseModel):
    """OpenRouter配置更新"""
    api_key: str = ""


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

