"""
FrogGPT AI服务 - 使用OpenRouter.ai提供AI能力
"""
from typing import List, Dict, Any, Optional
import httpx
from loguru import logger
from app.core.config import settings
from sqlalchemy.orm import Session


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
            
            # 获取API key（优先从数据库）
            api_key = self.get_api_key(db)
            
            # 构建请求头
            headers = {
                "Content-Type": "application/json",
            }
            
            # 如果提供了API Key，添加到请求头
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            # 如果提供了HTTP Referer，添加到请求头（用于免费使用）
            if self.http_referer:
                headers["HTTP-Referer"] = self.http_referer
            
            # 如果提供了X-Title，添加到请求头（用于免费使用）
            if self.x_title:
                headers["X-Title"] = self.x_title
            
            # 构建请求体
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
            
            # 如果使用AUTO模式，添加provider配置以实现智能路由
            # OpenRouter会根据价格、性能等因素自动选择最佳提供商
            if use_auto_routing:
                payload["provider"] = {
                    "sort": "price",  # 按价格排序，选择最经济的提供商
                    "allow_fallbacks": True,  # 允许备用提供商
                }
            
            if max_tokens:
                payload["max_tokens"] = max_tokens
            
            # 发送请求
            logger.debug(f"发送OpenRouter请求: model={model}, messages_count={len(messages)}")
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"OpenRouter响应成功: model={model}")
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API请求失败: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"OpenRouter API请求异常: {e}")
            raise
    
    async def get_models(self, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """
        获取可用的AI模型列表
        
        Args:
            db: 数据库会话（可选，用于从数据库读取API key）
        
        Returns:
            模型列表
        """
        try:
            # 获取API key（优先从数据库）
            api_key = self.get_api_key(db)
            
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
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
        
        # 添加热门SKU
        if "top_skus" in data_summary and data_summary["top_skus"]:
            context_parts.append("\n## 热门SKU（Top 10）")
            for i, sku in enumerate(data_summary["top_skus"][:10], 1):
                context_parts.append(
                    f"{i}. {sku.get('sku', 'N/A')} - "
                    f"销量: {sku.get('total_quantity', 0)} 件, "
                    f"订单: {sku.get('order_count', 0)} 单, "
                    f"GMV: ¥{sku.get('gmv', 0):,.2f}"
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
        system_prompt = """你是一个专业的电商运营助手，名为FrogGPT。你的任务是帮助运营人员分析数据、提供决策建议。

当前系统提供了以下运营数据，请基于这些数据回答用户的问题，并提供有价值的分析和建议。

"""
        return system_prompt + context
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


# 创建全局服务实例
frog_gpt_service = FrogGPTService()
