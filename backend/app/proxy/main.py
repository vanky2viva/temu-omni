"""Temu API 代理服务器主应用"""
import hashlib
import json
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from loguru import logger
from pydantic import BaseModel


class ProxyRequest(BaseModel):
    """代理请求模型"""
    api_type: str
    request_data: Optional[Dict[str, Any]] = None
    access_token: Optional[str] = None
    app_key: str
    app_secret: str
    api_base_url: Optional[str] = None  # 可选的API基础URL，如果不提供则使用默认值


class ProxyResponse(BaseModel):
    """代理响应模型"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_msg: Optional[str] = None


# 创建 FastAPI 应用
app = FastAPI(
    title="Temu API Proxy",
    version="1.0.0",
    description="Temu API 代理服务器 - 用于通过白名单 IP 转发 API 请求"
)

# 配置 CORS - 允许所有来源（可根据需要限制）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temu API 基础 URL
TEMU_API_BASE_URL = "https://agentpartner.temu.com/api"


def generate_sign(app_secret: str, params: Dict[str, Any]) -> str:
    """
    生成 API 签名（MD5 算法）
    
    签名规则：
    1. 将所有参数（除 sign 外）按 key 字母顺序排序
    2. 拼接成 key1value1key2value2... 格式
    3. 在前后各加上 app_secret
    4. 对整个字符串进行 MD5 加密并转大写
    """
    temp = []
    # 按键排序参数
    sorted_params = sorted(params.items())
    
    # 拼接参数字符串
    for key, value in sorted_params:
        if value is not None:
            # 如果值是字典或列表，转换为 JSON 字符串
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
            # 去除字符串两端的引号
            temp.append(str(key) + str(value).strip('\"'))
    
    un_sign = ''.join(temp)
    # app_secret + 参数字符串 + app_secret
    un_sign = str(app_secret) + un_sign + str(app_secret)
    # MD5 加密并转大写
    sign = hashlib.md5(un_sign.encode('utf-8')).hexdigest().upper()
    
    return sign


@app.post("/api/proxy", response_model=ProxyResponse)
async def proxy_request(request: ProxyRequest):
    """
    代理 Temu API 请求
    
    接收客户端请求，转发到 Temu API，并返回响应
    """
    try:
        # 构建通用参数
        timestamp = int(time.time())
        common_params = {
            "app_key": request.app_key,
            "data_type": "JSON",
            "timestamp": timestamp,
            "type": request.api_type,
            "version": "V1"
        }
        
        # 添加 access_token（如果提供）
        if request.access_token:
            common_params["access_token"] = request.access_token
        
        # 合并所有参数
        all_params = {**common_params}
        if request.request_data:
            # 业务参数放在 request 字段中
            all_params["request"] = request.request_data
        
        # 生成签名
        sign = generate_sign(request.app_secret, all_params)
        
        # 最终请求体
        request_payload = {**all_params, "sign": sign}
        
        # 确定要使用的API基础URL
        api_base_url = request.api_base_url or TEMU_API_BASE_URL
        
        logger.info(f"代理请求: {request.api_type}, API URL: {api_base_url}")
        logger.debug(f"请求参数: {json.dumps(request_payload, ensure_ascii=False, indent=2)}")
        
        # 发送 POST 请求到 Temu API
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Content-Type": "application/json"}
            response = await client.post(
                api_base_url,
                headers=headers,
                json=request_payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"代理响应: {request.api_type} - 成功: {result.get('success', False)}")
            
            # 检查业务错误
            if not result.get("success", False):
                error_code = result.get("errorCode", "未知")
                error_msg = result.get("errorMsg", "未知错误")
                logger.error(f"Temu API 错误: [{error_code}] {error_msg}")
                return ProxyResponse(
                    success=False,
                    error_code=error_code,
                    error_msg=error_msg
                )
            
            return ProxyResponse(
                success=True,
                result=result.get("result", {})
            )
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP 错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"代理请求失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"代理请求异常: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"代理请求异常: {str(e)}"
        )


@app.get("/")
def root():
    """根路径"""
    return {
        "app": "Temu API Proxy",
        "version": "1.0.0",
        "status": "running",
        "description": "Temu API 代理服务器"
    }


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("Temu API 代理服务器启动中...")
    logger.info(f"Temu API 基础 URL: {TEMU_API_BASE_URL}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("Temu API 代理服务器关闭中...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )

