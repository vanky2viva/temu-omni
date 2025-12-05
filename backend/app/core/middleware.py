"""全局中间件"""
import time
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger
import traceback
from sqlalchemy.exc import OperationalError, DisconnectionError
from httpx import RequestError, TimeoutException


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """全局异常处理中间件"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except (OperationalError, DisconnectionError) as e:
            logger.error(f"数据库连接错误: {e}")
            logger.error(traceback.format_exc())
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "数据库连接失败，请稍后重试",
                    "error": str(e)
                }
            )
        except (RequestError, TimeoutException) as e:
            logger.error(f"HTTP请求错误: {e}")
            logger.error(traceback.format_exc())
            return JSONResponse(
                status_code=504,
                content={
                    "detail": "外部服务请求超时或失败，请稍后重试",
                    "error": str(e)
                }
            )
        except HTTPException as http_exc:
            # 重新抛出 HTTP 异常，让 FastAPI 处理
            raise http_exc
        except Exception as e:
            logger.error(f"未处理的异常: {e}")
            logger.error(traceback.format_exc())
            # 检查是否是调试模式
            debug_mode = getattr(request.app, 'debug', False) if hasattr(request.app, 'debug') else False
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "服务器内部错误",
                    "error": str(e) if debug_mode else "Internal server error"
                }
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 记录请求信息
        logger.info(
            f"请求开始: {request.method} {request.url.path} - "
            f"客户端: {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # 记录响应信息
            logger.info(
                f"请求完成: {request.method} {request.url.path} - "
                f"状态码: {response.status_code} - "
                f"耗时: {process_time:.3f}秒"
            )
            
            # 添加处理时间到响应头
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"请求失败: {request.method} {request.url.path} - "
                f"错误: {e} - "
                f"耗时: {process_time:.3f}秒"
            )
            raise


class TimeoutMiddleware(BaseHTTPMiddleware):
    """请求超时中间件"""
    
    def __init__(self, app: ASGIApp, timeout: float = 300.0):
        super().__init__(app)
        self.timeout = timeout
    
    async def dispatch(self, request: Request, call_next):
        import asyncio
        
        try:
            response = await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout
            )
            return response
        except asyncio.TimeoutError:
            logger.error(f"请求超时: {request.method} {request.url.path}")
            return JSONResponse(
                status_code=504,
                content={
                    "detail": f"请求处理超时（超过{self.timeout}秒）",
                    "error": "Request timeout"
                }
            )

