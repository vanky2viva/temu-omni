"""ForgGPT API端点"""
import os
import shutil
import uuid
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
from app.services.file_parse_service import FileParseService
import json

router = APIRouter(prefix="/forggpt", tags=["ForgGPT"])

# 上传文件保存目录
UPLOAD_DIR = "/tmp/forggpt_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


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
        文件信息和解析结果
    """
    try:
        # 验证文件类型
        file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ''
        allowed_extensions = ['.xlsx', '.xls', '.csv', '.json', '.txt', '.md']
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_ext}，支持的类型: {', '.join(allowed_extensions)}"
            )
        
        # 生成文件ID和保存路径
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        # 保存文件到临时目录
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            file_size = os.path.getsize(file_path)
            logger.info(f"文件上传成功: {file.filename}, 大小: {file_size} 字节")
            
            # 解析文件
            try:
                # 确定文件类型
                file_type = None
                if file_ext in ['.xlsx', '.xls']:
                    file_type = 'excel'
                elif file_ext == '.csv':
                    file_type = 'csv'
                elif file_ext == '.json':
                    file_type = 'json'
                
                # 解析文件
                parse_result = FileParseService.parse_file(file_path, file_type)
                
                # 返回文件信息和解析结果
                return {
                    "success": True,
                    "file_id": file_id,
                    "file_name": file.filename,
                    "file_size": file_size,
                    "file_type": parse_result.get("file_type", "unknown"),
                    "file_path": file_path,  # 仅用于后续分析，不返回给前端
                    "parse_result": parse_result,
                    "message": f"文件上传并解析成功，{parse_result.get('summary', '')}"
                }
                
            except Exception as parse_error:
                # 解析失败，但文件已上传成功
                logger.error(f"文件解析失败: {parse_error}")
                return {
                    "success": True,
                    "file_id": file_id,
                    "file_name": file.filename,
                    "file_size": file_size,
                    "file_type": file_ext[1:] if file_ext else "unknown",
                    "file_path": file_path,
                    "parse_result": None,
                    "parse_error": str(parse_error),
                    "message": f"文件上传成功，但解析失败: {str(parse_error)}"
                }
            
        except Exception as save_error:
            logger.error(f"文件保存失败: {save_error}")
            raise HTTPException(
                status_code=500,
                detail=f"文件保存失败: {str(save_error)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

