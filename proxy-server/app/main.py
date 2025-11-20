"""Temu API 代理服务器主应用"""
import hashlib
import json
import time
import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from loguru import logger
from pydantic import BaseModel


class ProxyRequest(BaseModel):
    """代理请求模型"""
    api_type: str
    request_data: Optional[Dict[str, Any]] = None
    access_token: Optional[str] = None
    app_key: Optional[str] = None  # 可选，如果不提供则使用环境变量
    app_secret: Optional[str] = None  # 可选，如果不提供则使用环境变量
    region: Optional[str] = None  # 可选，区域：us, eu, global，默认使用环境变量或 us


class ProxyResponse(BaseModel):
    """代理响应模型"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error_code: Optional[Any] = None  # 可能是 string 或 int
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

# Temu API 基础 URL（根据区域选择）
TEMU_API_BASE_URL_US = "https://openapi-b-us.temu.com/openapi/router"
TEMU_API_BASE_URL_EU = "https://openapi-b-eu.temu.com/openapi/router"
TEMU_API_BASE_URL_GLOBAL = "https://openapi-b-global.temu.com/openapi/router"

# 默认区域（从环境变量读取，默认为 us）
DEFAULT_REGION = os.getenv("TEMU_API_REGION", "us").lower()

def get_api_base_url(region: Optional[str] = None) -> str:
    """根据区域获取 API 基础 URL"""
    region = (region or DEFAULT_REGION).lower()
    if region == "eu":
        return TEMU_API_BASE_URL_EU
    elif region == "global":
        return TEMU_API_BASE_URL_GLOBAL
    else:
        return TEMU_API_BASE_URL_US

# 从环境变量读取默认的 app_key 和 app_secret（如果客户端未提供）
DEFAULT_APP_KEY = os.getenv("TEMU_APP_KEY", "")
DEFAULT_APP_SECRET = os.getenv("TEMU_APP_SECRET", "")


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
    
    支持两种方式：
    1. 客户端提供 app_key 和 app_secret（用于多应用场景）
    2. 客户端只提供 access_token，app_key/app_secret 从代理服务器环境变量读取（推荐，简化客户端调用）
    """
    try:
        # 确定使用的 app_key 和 app_secret
        # 优先使用客户端提供的，否则使用环境变量中的默认值
        app_key = request.app_key or DEFAULT_APP_KEY
        app_secret = request.app_secret or DEFAULT_APP_SECRET
        
        if not app_key or not app_secret:
            raise HTTPException(
                status_code=400,
                detail="缺少 app_key 或 app_secret。请在请求中提供，或在代理服务器环境变量中配置 TEMU_APP_KEY 和 TEMU_APP_SECRET"
            )
        
        # 构建通用参数
        timestamp = int(time.time())
        common_params = {
            "app_key": app_key,
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
            # 根据官方文档，某些API的参数应该直接放在顶层，而不是在request对象中
            # 例如：bg.order.detail.v2.get 和 bg.order.list.v2.get 的参数应该直接放在顶层
            # 检查是否是这些特殊API
            apis_with_top_level_params = [
                "bg.order.detail.v2.get",
                "bg.order.list.v2.get",
                # 可以在这里添加其他需要顶层参数的API
            ]
            
            if request.api_type in apis_with_top_level_params:
                # 对于这些API，将参数直接放在顶层
                all_params.update(request.request_data)
            else:
                # 其他API，业务参数放在 request 字段中
                all_params["request"] = request.request_data
        
        # 生成签名
        sign = generate_sign(app_secret, all_params)
        
        # 最终请求体
        request_payload = {**all_params, "sign": sign}
        
        logger.info(f"代理请求: {request.api_type}")
        logger.debug(f"请求参数: {json.dumps(request_payload, ensure_ascii=False, indent=2)}")
        
        # 确定使用的 API URL（根据区域）
        api_base_url = get_api_base_url(request.region)
        logger.info(f"使用 API URL: {api_base_url} (区域: {request.region or DEFAULT_REGION})")
        
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
                # 将 error_code 转换为字符串（如果它是数字）
                if isinstance(error_code, (int, float)):
                    error_code = str(error_code)
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
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )

