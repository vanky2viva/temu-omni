"""ChatKit API端点 - 用于高级AI中枢集成"""
import uuid
import json
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from loguru import logger

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.shop import Shop
from app.models.system_config import SystemConfig
from app.services.chatkit_service import ChatKitService

router = APIRouter(prefix="/chatkit", tags=["ChatKit"])


class ChatKitSessionRequest(BaseModel):
    """ChatKit会话创建请求"""
    shop_id: Optional[int] = None
    shop_ids: Optional[List[int]] = None
    tenant_id: Optional[str] = None


class ChatKitSessionResponse(BaseModel):
    """ChatKit会话响应"""
    session_id: str
    client_secret: Optional[str] = None  # 如果使用第三方ChatKit服务
    metadata: Dict[str, Any]
    model: str
    base_url: str
    api_key_configured: bool


class DashboardCommand(BaseModel):
    """Dashboard指令协议"""
    type: str  # SET_DATE_RANGE, SET_METRIC_CHART, FOCUS_SKU, COMPARE_SHOPS
    payload: Dict[str, Any]


@router.post("/session", response_model=ChatKitSessionResponse)
def create_session(
    request: ChatKitSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建ChatKit会话
    
    返回会话信息，包括：
    - session_id: 会话唯一标识
    - metadata: 包含用户ID、店铺ID等元数据
    - model: 当前使用的AI模型
    - api_key_configured: API Key是否已配置
    """
    try:
        # 生成会话ID
        session_id = str(uuid.uuid4())
        
        # 获取用户权限的店铺列表
        allowed_shop_ids: List[int] = []
        
        # 如果指定了shop_id，验证权限
        if request.shop_id:
            shop = db.query(Shop).filter(Shop.id == request.shop_id).first()
            if not shop:
                raise HTTPException(status_code=404, detail=f"店铺 {request.shop_id} 不存在")
            allowed_shop_ids = [request.shop_id]
        elif request.shop_ids:
            # 验证所有店铺是否存在
            shops = db.query(Shop).filter(Shop.id.in_(request.shop_ids)).all()
            if len(shops) != len(request.shop_ids):
                raise HTTPException(status_code=404, detail="部分店铺不存在")
            allowed_shop_ids = request.shop_ids
        else:
            # 获取用户有权限的所有店铺（TODO: 实现权限检查）
            shops = db.query(Shop).filter(Shop.is_active == True).all()
            allowed_shop_ids = [shop.id for shop in shops]
        
        # 获取AI配置
        def get_config_value(key: str, default: str = "") -> str:
            config = db.query(SystemConfig).filter(SystemConfig.key == key.lower()).first()
            return config.value if config and config.value else default
        
        provider = get_config_value("ai_provider", "deepseek")
        model = get_config_value(f"{provider}_model", "gpt-4o" if provider == "openai" else "deepseek-chat")
        base_url = get_config_value(f"{provider}_base_url", 
                                   "https://api.openai.com/v1" if provider == "openai" else "https://api.deepseek.com")
        api_key = get_config_value(f"{provider}_api_key", "")
        
        # 构建metadata
        metadata = {
            "userId": str(current_user.id),
            "username": current_user.username,
            "tenantId": request.tenant_id or "default",  # TODO: 实现多租户
            "shopId": allowed_shop_ids[0] if allowed_shop_ids else None,
            "allowedShops": allowed_shop_ids,
            "provider": provider,
            "model": model,
        }
        
        # 生成 client_secret（用于官方 ChatKit 组件）
        # 这是一个 JWT-like token，包含会话信息
        client_secret_payload = {
            "session_id": session_id,
            "user_id": str(current_user.id),
            "shop_ids": allowed_shop_ids,
            "exp": int((datetime.utcnow() + timedelta(hours=24)).timestamp()),  # 24小时过期
            "iat": int(datetime.utcnow().timestamp())
        }
        
        # 使用一个简单的签名机制（生产环境应使用更安全的方式）
        secret_key = api_key or "default_secret_key_change_in_production"
        payload_str = json.dumps(client_secret_payload, sort_keys=True)
        signature = hmac.new(
            secret_key.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        client_secret = base64.urlsafe_b64encode(
            f"{payload_str}.{signature}".encode('utf-8')
        ).decode('utf-8')
        
        logger.info(f"创建ChatKit会话: session_id={session_id}, user_id={current_user.id}, shops={allowed_shop_ids}")
        
        return ChatKitSessionResponse(
            session_id=session_id,
            client_secret=client_secret,  # 生成 client_secret 用于官方 ChatKit 组件
            metadata=metadata,
            model=model,
            base_url=base_url,
            api_key_configured=bool(api_key)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建ChatKit会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.get("/session/{session_id}")
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话信息"""
    # TODO: 实现会话存储和检索
    # 目前返回基本信息
    return {
        "session_id": session_id,
        "status": "active"
    }


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    session_id: str
    shop_ids: Optional[List[int]] = None
    model: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None


@router.post("/chat")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ChatKit 聊天接口（流式响应）
    
    使用 OpenAI SDK 进行对话，支持 Function Calling
    """
    try:
        service = ChatKitService(db)
        
        # 构建消息列表
        messages = request.history or []
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        # 获取模型
        def get_config_value(key: str, default: str = "") -> str:
            config = db.query(SystemConfig).filter(SystemConfig.key == key.lower()).first()
            return config.value if config and config.value else default
        
        model = request.model or get_config_value("openai_model", "gpt-4o")
        
        # 获取用户有权限的店铺
        shop_ids = request.shop_ids
        if not shop_ids:
            shops = db.query(Shop).filter(Shop.is_active == True).all()
            shop_ids = [shop.id for shop in shops]
        
        def generate():
            """生成流式响应"""
            try:
                for chunk in service.chat_completion_stream(
                    messages=messages,
                    model=model,
                    shop_ids=shop_ids
                ):
                    yield chunk
            except Exception as e:
                logger.error(f"ChatKit 流式响应生成失败: {e}", exc_info=True)
                error_data = {
                    'type': 'error',
                    'data': f'AI 调用失败: {str(e)}'
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"ChatKit 聊天失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"聊天失败: {str(e)}")

