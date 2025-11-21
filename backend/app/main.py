"""主应用入口"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import traceback

from app.core.config import settings
from app.core.database import engine, Base, check_database_connection
from app.core.middleware import ExceptionHandlerMiddleware, RequestLoggingMiddleware, TimeoutMiddleware
from app.api import shops, orders, products, statistics, sync, analytics, system, import_data, auth, order_costs

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Temu多店铺管理系统API",
    debug=settings.DEBUG
)

# 添加中间件（顺序很重要，从外到内执行）
# 1. 超时中间件（最外层）
app.add_middleware(TimeoutMiddleware, timeout=300.0)

# 2. 异常处理中间件
app.add_middleware(ExceptionHandlerMiddleware)

# 3. 请求日志中间件
app.add_middleware(RequestLoggingMiddleware)

# 4. CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api")  # 认证路由（无需认证）
app.include_router(shops.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(statistics.router, prefix="/api")
app.include_router(sync.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(system.router, prefix="/api")
app.include_router(import_data.router, prefix="/api")
app.include_router(order_costs.router, prefix="/api", tags=["订单成本"])


@app.get("/")
def root():
    """根路径"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
def health_check():
    """
    健康检查端点
    
    检查数据库连接和应用状态
    """
    try:
        db_healthy = check_database_connection()
        return {
            "status": "healthy" if db_healthy else "degraded",
            "database": "connected" if db_healthy else "disconnected",
            "version": settings.APP_VERSION
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} is starting...")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # 初始化默认管理员用户
    try:
        from app.core.init_default_user import init_default_user
        init_default_user()
    except Exception as e:
        logger.warning(f"初始化默认用户失败: {str(e)}")

    # 启动定时任务调度器
    try:
        from app.core.scheduler import start_scheduler
        start_scheduler()
        logger.info("定时任务调度器已启动")
    except Exception as e:
        logger.error(f"启动定时任务调度器失败: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info(f"{settings.APP_NAME} is shutting down...")
    
    # 停止定时任务调度器
    try:
        from app.core.scheduler import stop_scheduler
        stop_scheduler()
        logger.info("定时任务调度器已停止")
    except Exception as e:
        logger.error(f"停止定时任务调度器失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

