"""ForgGPT AI对话服务"""
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger

from app.services.ai.deepseek_provider import DeepSeekProvider
from app.services.ai.openai_provider import OpenAIProvider
from app.services.ai.base_provider import AIProvider, ChatMessage
from app.services.statistics import StatisticsService
from app.services.forggpt_tools import ForgGPTTools, TOOLS_SCHEMA
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.shop import Shop
from app.models.system_config import SystemConfig
from app.core.redis_client import RedisClient
from app.core.config import settings


class ForgGPTService:
    """ForgGPT AI对话服务"""
    
    def __init__(self, db: Session):
        """
        初始化ForgGPT服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.ai_provider = self._init_ai_provider()
        self.tools = ForgGPTTools(db)  # 初始化工具集合
        self.max_history = 50  # 最大历史消息数
        self.max_context_tokens = 8000  # 最大上下文token数
    
    def _init_ai_provider(self) -> AIProvider:
        """
        从数据库初始化AI Provider（不再使用环境变量）
        
        Returns:
            AI Provider实例
        """
        def get_config_value(key: str, default: str = "") -> str:
            """从数据库获取配置值"""
            try:
                # 配置键名是小写的（与 system.py 中保存的格式一致）
                config = self.db.query(SystemConfig).filter(SystemConfig.key == key.lower()).first()
                
                if config and config.value:
                    logger.debug(f"从数据库读取配置 {key}: 找到值 (长度={len(config.value)})")
                    return config.value
                else:
                    logger.debug(f"从数据库读取配置 {key}: 未找到，使用默认值")
            except Exception as e:
                logger.warning(f"从数据库读取配置 {key} 失败: {e}")
            return default
        
        # 获取provider类型（默认deepseek）
        # 注意：配置键名是小写的（与 system.py 中保存的格式一致）
        provider = get_config_value("ai_provider", "deepseek")
        provider = provider.lower() if provider else "deepseek"
        logger.info(f"AI Provider类型: {provider}")
        
        if provider == "openai":
            # 初始化OpenAI Provider
            api_key = get_config_value("openai_api_key", "")
            base_url = get_config_value("openai_base_url", "https://api.openai.com/v1")
            model = get_config_value("openai_model", "gpt-4o")
            
            logger.info(f"初始化OpenAI Provider: base_url={base_url}, model={model}, has_api_key={bool(api_key)}")
            if not api_key:
                logger.warning("OpenAI API Key 未配置")
            return OpenAIProvider(
                api_key=api_key,
                base_url=base_url,
                default_model=model
            )
        else:
            # 默认使用DeepSeek Provider
            api_key = get_config_value("deepseek_api_key", "")
            base_url = get_config_value("deepseek_base_url", "https://api.deepseek.com")
            model = get_config_value("deepseek_model", "deepseek-chat")
            
            logger.info(f"初始化DeepSeek Provider: base_url={base_url}, model={model}, has_api_key={bool(api_key)}")
            if not api_key:
                logger.warning("DeepSeek API Key 未配置，请在前端设置页面配置")
            return DeepSeekProvider(
                api_key=api_key,
                base_url=base_url,
                default_model=model
            )
    
    def _get_system_prompt(self) -> str:
        """
        获取系统提示词（完整版FrogGPT Prompt体系）
        
        Returns:
            系统提示词
        """
        # 获取应用数据概览
        shop_count = self.db.query(Shop).count()
        order_count = self.db.query(Order).count()
        product_count = self.db.query(Product).count()
        
        # 获取最近7天的数据
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_orders = self.db.query(Order).filter(
            Order.order_time >= seven_days_ago
        ).all()
        
        recent_gmv = sum([float(order.total_price or 0) for order in recent_orders])
        recent_order_count = len(recent_orders)
        
        system_prompt = f"""你是 **FrogGPT**，一个专为电商运营打造的数据分析专家。

你可以访问系统提供的数据，包括：店铺、订单、商品、SKU、成本、库存、利润、GMV、退款、**回款金额**等。

**重要：你可以使用以下工具函数获取数据：**
- `get_collection_statistics`: 获取回款统计数据（汇总数据，按日期和店铺分组）。这是获取回款金额的主要接口。
- `get_collection_details`: 获取回款详细数据（最小粒度，按订单级别）。
- `get_order_details`: 获取订单详细数据。
- `get_product_cost_details`: 获取商品成本详细数据。
- `get_order_statistics`: 获取订单统计数据（GMV、订单量、利润等）。

当用户询问**回款、收款、回款金额、回款统计**等相关问题时，你应该使用 `get_collection_statistics` 工具来获取数据。

你的目标是：
1. **理解用户问题**
2. **自动识别相关数据类型（订单/商品/店铺/财务/回款等）**
3. **使用合适的工具函数获取数据**
4. **基于系统提供的数据上下文进行分析**
5. **输出清晰、可靠、可执行的运营决策建议**

当前应用数据概览：
- 店铺数量：{shop_count}
- 订单总数：{order_count}
- 商品总数：{product_count}
- 最近7天GMV：{recent_gmv:.2f}
- 最近7天订单量：{recent_order_count}

---

## 【规则 1：必须使用数据，不可臆测】

当用户提出涉及 **趋势 / GMV / 销量 / 销售额 / 盈利 / SKU / 店铺情况** 的问题时：
- 你必须使用系统提供的数据上下文
- 不能凭主观推理"想象"数据，也不能编造数字
- 如果数据不足，必须明确告知用户

---

## 【规则 2：基于关键词自动选择合适的数据上下文】

当用户的问题涉及以下关键词时，你应当按对应数据源理解：

### 🟦 订单 / GMV / 销售
关键词：`订单、order、gmv、销售、销量、趋势、利润、收入、营收、数据、分析、统计`
→ 使用系统注入的"订单上下文数据"（来自 StatisticsService.get_order_statistics()）

### 💰 回款 / 收款 / 财务管理
关键词：`回款、收款、回款金额、回款统计、财务管理、collection、payment collection`
→ **必须使用 `get_collection_statistics` 工具函数获取回款数据**，不要使用其他数据源

### 🟩 商品 / SKU
关键词：`商品、sku、product、库存、top、畅销、销量前十、利润最高、成本`
→ 使用系统注入的"商品上下文数据"（来自 ORM + Product 表）

### 🟧 店铺
关键词：`店铺、shop、store、环境、店铺情况、店铺数据`
→ 使用系统注入的"店铺上下文数据"

---

## 【规则 3：回答输出格式】

你应当使用以下结构：

**📌【核心结论】**
（用 2~4 句总结问题结果）

**📊【关键数据】**
（用列表或表格列出关键指标）

**📈【详细分析】**
（从 GMV / 订单量 / 客单价 / SKU / 库存 / 退款 角度分析）

**📝【可执行建议】**
（每条建议应包含"动作 + 影响指标 + 风险提示"）

---

## 【规则 4：当数据不足时必须提示】

例如：
- "样本数量不足"
- "该 SKU 无订单"
- "近 7 天无 GMV 数据"
- "退款数据缺失，无法可靠分析"

不得硬编理由。

---

请用专业、简洁、易懂的方式回答用户问题，并提供可操作的建议。
在回答时，可以引用具体的数据，但不要编造数据。如果用户询问的数据不在当前数据库中，请明确告知。
"""
        return system_prompt
    
    def _get_data_context(self, query: str, shop_ids: Optional[List[int]] = None, date_range: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        根据用户查询获取相关数据上下文（优化版）
        
        Args:
            query: 用户查询
            shop_ids: 店铺ID列表（可选）
            date_range: 日期范围（可选，格式：{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}）
            
        Returns:
            数据上下文字符串
        """
        context_parts = []
        
        # 检测关键词，决定查询哪些数据
        query_lower = query.lower()
        
        # 解析日期范围
        start_date = None
        end_date = None
        if date_range:
            try:
                start_date = datetime.strptime(date_range.get('start', ''), '%Y-%m-%d') if date_range.get('start') else None
                end_date = datetime.strptime(date_range.get('end', ''), '%Y-%m-%d') if date_range.get('end') else None
            except Exception as e:
                logger.warning(f"解析日期范围失败: {e}")
        
        # 订单相关查询
        order_keywords = ['订单', 'order', 'gmv', '销售', 'sales', '销量', '趋势', '利润', '收入', '营收', '数据', '分析', '统计']
        if any(keyword in query_lower for keyword in order_keywords):
            try:
                # 获取最近7天和30天的订单统计
                seven_days_ago = datetime.now() - timedelta(days=7)
                thirty_days_ago = datetime.now() - timedelta(days=30)
                
                # 7天统计
                stats_7d = StatisticsService.get_order_statistics(
                    self.db,
                    shop_ids=shop_ids,
                    start_date=start_date or seven_days_ago,
                    end_date=end_date
                )
                
                # 30天统计
                stats_30d = StatisticsService.get_order_statistics(
                    self.db,
                    shop_ids=shop_ids,
                    start_date=start_date or thirty_days_ago,
                    end_date=end_date
                )
                
                context_parts.append(f"""
订单数据（最近7天）：
- 总订单数：{stats_7d.get('total_orders', 0)}
- 总GMV：{stats_7d.get('total_gmv', 0):.2f} CNY
- 总利润：{stats_7d.get('total_profit', 0):.2f} CNY
- 平均订单金额：{stats_7d.get('avg_order_amount', 0):.2f} CNY
- 利润率：{stats_7d.get('profit_margin', 0):.2f}%
- 退款订单数：{stats_7d.get('refunded_orders', 0)}
- 退款率：{stats_7d.get('refund_rate', 0):.2%}

订单数据（最近30天）：
- 总订单数：{stats_30d.get('total_orders', 0)}
- 总GMV：{stats_30d.get('total_gmv', 0):.2f} CNY
- 总利润：{stats_30d.get('total_profit', 0):.2f} CNY
- 平均订单金额：{stats_30d.get('avg_order_amount', 0):.2f} CNY
- 利润率：{stats_30d.get('profit_margin', 0):.2f}%
- 退款订单数：{stats_30d.get('refunded_orders', 0)}
- 退款率：{stats_30d.get('refund_rate', 0):.2%}
""")
            except Exception as e:
                logger.warning(f"获取订单数据上下文失败: {e}")
        
        # 商品相关查询
        product_keywords = ['商品', 'product', 'sku', '销量', '库存', 'top', '畅销', '销量前十', '利润最高', '成本']
        if any(keyword in query_lower for keyword in product_keywords):
            try:
                # 获取商品统计
                total_products = self.db.query(Product).count()
                active_products = self.db.query(Product).filter(Product.is_active == True).count()
                
                # 获取销量前10的商品
                top_products_query = self.db.query(
                    Product.id,
                    Product.product_name,
                    Product.sku,
                    func.sum(Order.quantity).label('total_sales')
                ).join(
                    Order, Product.id == Order.product_id
                ).filter(
                    Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.REFUNDED])
                )
                
                if shop_ids:
                    top_products_query = top_products_query.filter(Order.shop_id.in_(shop_ids))
                
                top_products = top_products_query.group_by(
                    Product.id, Product.product_name, Product.sku
                ).order_by(
                    func.sum(Order.quantity).desc()
                ).limit(10).all()
                
                context_parts.append(f"""
商品数据：
- 商品总数：{total_products}
- 在售商品数：{active_products}
- 销量前10商品：
""")
                for product in top_products:
                    context_parts.append(f"  - {product.product_name} ({product.sku}): {product.total_sales}件")
            except Exception as e:
                logger.warning(f"获取商品数据上下文失败: {e}")
        
        # 店铺相关查询
        shop_keywords = ['店铺', 'shop', 'store', '环境', '店铺情况', '店铺数据']
        if any(keyword in query_lower for keyword in shop_keywords):
            try:
                shops_query = self.db.query(Shop)
                if shop_ids:
                    shops_query = shops_query.filter(Shop.id.in_(shop_ids))
                shops = shops_query.all()
                
                context_parts.append(f"""
店铺数据：
- 店铺总数：{len(shops)}
- 店铺列表：
""")
                for shop in shops[:10]:  # 最多显示10个店铺
                    context_parts.append(f"  - {shop.shop_name} (ID: {shop.id}, 环境: {shop.environment.value})")
            except Exception as e:
                logger.warning(f"获取店铺数据上下文失败: {e}")
        
        return "\n".join(context_parts) if context_parts else None
    
    def _build_messages(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        include_data_context: bool = True,
        shop_ids: Optional[List[int]] = None,
        date_range: Optional[Dict[str, str]] = None
    ) -> List[ChatMessage]:
        """
        构建消息列表（优化版，支持店铺和日期筛选）
        
        Args:
            user_message: 用户消息
            history: 历史消息列表
            include_data_context: 是否包含数据上下文
            shop_ids: 店铺ID列表（用于筛选数据）
            date_range: 日期范围（用于筛选数据）
            
        Returns:
            消息列表
        """
        messages = []
        
        # 系统提示词
        system_prompt = self._get_system_prompt()
        messages.append(ChatMessage(role="system", content=system_prompt))
        
        # 数据上下文（可选）
        if include_data_context:
            data_context = self._get_data_context(user_message, shop_ids=shop_ids, date_range=date_range)
            if data_context:
                messages.append(ChatMessage(
                    role="system",
                    content=f"以下是当前应用的相关数据，供你参考：\n{data_context}\n\n请基于这些真实数据进行分析和回答。"
                ))
        
        # 历史消息（限制数量）
        if history:
            # 只保留最近的历史消息
            recent_history = history[-self.max_history:]
            for msg in recent_history:
                messages.append(ChatMessage(
                    role=msg.get("role", "user"),
                    content=msg.get("content", "")
                ))
        
        # 当前用户消息
        messages.append(ChatMessage(role="user", content=user_message))
        
        return messages
    
    def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        shop_ids: Optional[List[int]] = None,
        date_range: Optional[Dict[str, str]] = None,
        stream: bool = False,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        进行对话
        
        Args:
            message: 用户消息
            session_id: 会话ID（可选，不提供则自动生成）
            shop_ids: 店铺ID列表（用于筛选数据）
            date_range: 日期范围（用于筛选数据）
            stream: 是否流式返回
            history: 历史消息列表
            
        Returns:
            对话响应
        """
        if not self.ai_provider.is_available():
            raise ValueError("AI服务不可用，请检查API密钥配置")
        
        # 生成会话ID
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:16]}"
        
        # 构建消息列表（传入店铺和日期范围）
        messages = self._build_messages(
            message, 
            history, 
            shop_ids=shop_ids, 
            date_range=date_range
        )
        
        try:
            if stream:
                # 流式响应（返回生成器）
                return {
                    "session_id": session_id,
                    "stream": True,
                    "generator": self.ai_provider.chat_completion_stream(messages)
                }
            else:
                # 普通响应（支持工具调用）
                response = self._chat_with_tools(messages)
                
                return {
                    "session_id": session_id,
                    "message": response.content,
                    "usage": response.usage,
                    "model": response.model,
                    "finish_reason": response.finish_reason
                }
        except Exception as e:
            logger.error(f"ForgGPT对话失败: {e}")
            raise Exception(f"AI对话失败: {str(e)}")
    
    def save_conversation_history(
        self,
        session_id: str,
        role: str,
        content: str
    ):
        """
        保存对话历史到Redis
        
        Args:
            session_id: 会话ID
            role: 角色（user/assistant）
            content: 消息内容
        """
        try:
            cache_key = f"forggpt:history:{session_id}"
            history = RedisClient.get(cache_key) or []
            
            history.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
            
            # 限制历史消息数量
            if len(history) > self.max_history:
                history = history[-self.max_history:]
            
            # 保存到Redis（7天过期）
            RedisClient.set(cache_key, history, ttl=7 * 24 * 3600)
        except Exception as e:
            logger.warning(f"保存对话历史失败: {e}")
    
    def _chat_with_tools(
        self,
        messages: List[ChatMessage],
        max_iterations: int = 3
    ) -> Any:
        """
        带工具调用的对话（支持多轮工具调用）
        
        Args:
            messages: 消息列表
            max_iterations: 最大迭代次数（防止无限循环）
            
        Returns:
            最终响应
        """
        iteration = 0
        current_messages = messages.copy()
        
        while iteration < max_iterations:
            iteration += 1
            
            # 调用AI（传入工具定义）
            response = self.ai_provider.chat_completion(
                current_messages,
                tools=TOOLS_SCHEMA
            )
            
            # 检查是否有工具调用
            tool_calls = response.tool_calls or []
            
            if not tool_calls:
                # 没有工具调用，返回最终响应
                return response
            
            # 有工具调用，执行工具函数
            logger.info(f"检测到 {len(tool_calls)} 个工具调用")
            
            # 将AI的响应添加到消息历史
            current_messages.append(ChatMessage(
                role="assistant",
                content=response.content or ""
            ))
            
            # 执行每个工具调用
            tool_results = []
            for tool_call in tool_calls:
                tool_name = tool_call.get("function", {}).get("name")
                tool_args = tool_call.get("function", {}).get("arguments", "{}")
                
                if not tool_name:
                    continue
                
                try:
                    # 解析参数
                    import json
                    args = json.loads(tool_args) if isinstance(tool_args, str) else tool_args
                    
                    # 调用工具函数
                    tool_method = getattr(self.tools, tool_name, None)
                    if tool_method:
                        result = tool_method(**args)
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tool_call.get("id"),
                            "name": tool_name,
                            "content": json.dumps(result, ensure_ascii=False)
                        })
                        logger.info(f"工具 {tool_name} 执行成功")
                    else:
                        logger.warning(f"工具 {tool_name} 不存在")
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tool_call.get("id"),
                            "name": tool_name,
                            "content": json.dumps({"success": False, "error": f"工具 {tool_name} 不存在"}, ensure_ascii=False)
                        })
                except Exception as e:
                    logger.error(f"执行工具 {tool_name} 失败: {e}")
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id"),
                        "name": tool_name,
                        "content": json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
                    })
            
            # 将工具调用结果添加到消息历史
            # 注意：工具调用结果需要按照特定的格式添加
            # 格式：{"role": "tool", "tool_call_id": "...", "content": "..."}
            for tool_result in tool_results:
                # 将工具结果作为JSON字符串添加到消息内容中
                current_messages.append(ChatMessage(
                    role="tool",
                    content=tool_result["content"]
                ))
        
        # 达到最大迭代次数，返回最后一次响应
        logger.warning(f"工具调用达到最大迭代次数 {max_iterations}")
        return response
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        获取对话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            历史消息列表
        """
        try:
            cache_key = f"forggpt:history:{session_id}"
            history = RedisClient.get(cache_key) or []
            return history
        except Exception as e:
            logger.warning(f"获取对话历史失败: {e}")
            return []

