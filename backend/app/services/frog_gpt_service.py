"""
FrogGPT AI服务 - 使用OpenRouter.ai提供AI能力
"""
from typing import List, Dict, Any, Optional
import httpx
from loguru import logger
from app.core.config import settings


class FrogGPTService:
    """FrogGPT AI服务类"""
    
    def __init__(self):
        """初始化服务"""
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
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
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
            model = model or self.default_model
            
            # 构建请求头
            headers = {
                "Content-Type": "application/json",
            }
            
            # 如果提供了API Key，添加到请求头
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
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
    
    async def get_models(self) -> List[Dict[str, Any]]:
        """
        获取可用的AI模型列表
        
        Returns:
            模型列表
        """
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
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
