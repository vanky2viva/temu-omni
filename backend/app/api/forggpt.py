"""ForgGPT API端点"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from loguru import logger

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.forggpt_service import ForgGPTService
import json

router = APIRouter(prefix="/forggpt", tags=["ForgGPT"])


class ChatRequest(BaseModel):
    """对话请求"""
    message: str
    session_id: Optional[str] = None
    shop_ids: Optional[List[int]] = None
    date_range: Optional[dict] = None
    stream: bool = False
    history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    """对话响应"""
    session_id: str
    message: Optional[str] = None
    usage: Optional[dict] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    进行AI对话
    
    Args:
        request: 对话请求
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        对话响应
    """
    try:
        service = ForgGPTService(db)
        
        # 如果是流式请求，返回流式响应
        if request.stream:
            try:
                response = service.chat(
                    message=request.message,
                    session_id=request.session_id,
                    shop_ids=request.shop_ids,
                    date_range=request.date_range,
                    stream=True,
                    history=request.history
                )
            except ValueError as e:
                # API Key 未配置等配置错误
                logger.error(f"ForgGPT配置错误: {e}")
                raise HTTPException(status_code=400, detail=str(e))
            
            def generate():
                try:
                    # 发送会话ID
                    yield f"data: {json.dumps({'type': 'session_id', 'data': response['session_id']})}\n\n"
                    
                    # 流式返回消息内容
                    for chunk in response['generator']:
                        # chunk 可能是字符串（旧格式）或 JSON 字符串（新格式，包含思考过程）
                        try:
                            # 尝试解析为 JSON（新格式）
                            chunk_data = json.loads(chunk)
                            yield f"data: {json.dumps(chunk_data)}\n\n"
                        except (json.JSONDecodeError, TypeError):
                            # 旧格式，直接作为内容返回
                            yield f"data: {json.dumps({'type': 'content', 'data': chunk})}\n\n"
                    
                    # 发送结束标记
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                except ValueError as e:
                    # 配置错误（如API Key未配置）
                    logger.error(f"流式响应配置错误: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
                except Exception as e:
                    logger.error(f"流式响应生成失败: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'data': f'AI服务调用失败: {str(e)}'})}\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            # 普通响应
            try:
                response = service.chat(
                    message=request.message,
                    session_id=request.session_id,
                    shop_ids=request.shop_ids,
                    date_range=request.date_range,
                    stream=False,
                    history=request.history
                )
            except ValueError as e:
                # API Key 未配置等配置错误
                logger.error(f"ForgGPT配置错误: {e}")
                raise HTTPException(status_code=400, detail=str(e))
            
            # 保存对话历史
            service.save_conversation_history(
                response['session_id'],
                "user",
                request.message
            )
            service.save_conversation_history(
                response['session_id'],
                "assistant",
                response['message']
            )
            
            return ChatResponse(
                session_id=response['session_id'],
                message=response['message'],
                usage=response.get('usage'),
                model=response.get('model'),
                finish_reason=response.get('finish_reason')
            )
            
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except ValueError as e:
        # 配置错误（如API Key未配置）
        logger.error(f"ForgGPT配置错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"ForgGPT对话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI对话失败: {str(e)}")


@router.get("/history/{session_id}")
def get_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取对话历史
    
    Args:
        session_id: 会话ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        对话历史
    """
    try:
        service = ForgGPTService(db)
        history = service.get_conversation_history(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        logger.error(f"获取对话历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取对话历史失败: {str(e)}")


@router.post("/upload")
def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传文件（用于数据分析）
    
    Args:
        file: 上传的文件
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        文件信息
    """
    try:
        # TODO: 实现文件上传和解析逻辑
        # 1. 保存文件到临时目录
        # 2. 解析文件（Excel/CSV/JSON）
        # 3. 提取数据摘要
        # 4. 返回文件ID和摘要
        
        return {
            "file_id": f"file_{file.filename}",
            "file_name": file.filename,
            "message": "文件上传功能开发中"
        }
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

