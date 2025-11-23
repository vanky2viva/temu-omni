"""
ChatKit 服务 - 基于 OpenAI SDK 的高级 AI 中枢
使用 OpenAI Assistants API 或 Chat Completions API with Function Calling
"""
import json
from typing import List, Dict, Any, Optional, Iterator
from datetime import datetime
from sqlalchemy.orm import Session
from loguru import logger

try:
    from openai import OpenAI
except ImportError:
    logger.warning("OpenAI SDK 未安装，请运行: pip install openai")
    OpenAI = None

from app.models.system_config import SystemConfig
from app.models.shop import Shop
from app.models.order import Order
from app.models.product import Product
from app.services.statistics import StatisticsService


class ChatKitService:
    """ChatKit 服务 - 基于 OpenAI SDK"""
    
    def __init__(self, db: Session):
        """
        初始化 ChatKit 服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.client = self._init_openai_client()
        self.statistics_service = StatisticsService(db)
    
    def _init_openai_client(self) -> Optional[OpenAI]:
        """初始化 OpenAI 客户端"""
        if OpenAI is None:
            logger.error("OpenAI SDK 未安装")
            return None
        
        # 从数据库获取配置
        def get_config_value(key: str, default: str = "") -> str:
            config = self.db.query(SystemConfig).filter(SystemConfig.key == key.lower()).first()
            return config.value if config and config.value else default
        
        api_key = get_config_value("openai_api_key", "")
        base_url = get_config_value("openai_base_url", "https://api.openai.com/v1")
        
        if not api_key:
            logger.warning("OpenAI API Key 未配置")
            return None
        
        return OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        获取可用的工具函数定义（用于 Function Calling）
        
        Returns:
            工具函数定义列表
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_shop_dashboard",
                    "description": "获取店铺仪表盘数据，包括 GMV、订单数、利润、退款率等核心指标",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "shop_id": {
                                "type": "integer",
                                "description": "店铺ID，如果为 None 则返回所有店铺的汇总数据"
                            },
                            "days": {
                                "type": "integer",
                                "description": "统计天数，默认 7 天",
                                "default": 7
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_order_trend",
                    "description": "获取订单趋势数据，返回最近 N 天的 GMV 和订单数趋势",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "shop_id": {
                                "type": "integer",
                                "description": "店铺ID，如果为 None 则返回所有店铺的汇总数据"
                            },
                            "days": {
                                "type": "integer",
                                "description": "统计天数，默认 7 天",
                                "default": 7
                            }
                        },
                        "required": ["days"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_top_profit_skus",
                    "description": "列出高利润 SKU，按利润从高到低排序",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "shop_id": {
                                "type": "integer",
                                "description": "店铺ID，如果为 None 则返回所有店铺的数据"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "返回数量限制，默认 10",
                                "default": 10
                            },
                            "days": {
                                "type": "integer",
                                "description": "统计天数，默认 30 天",
                                "default": 30
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_top_loss_skus",
                    "description": "列出亏损 SKU，按亏损金额从高到低排序",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "shop_id": {
                                "type": "integer",
                                "description": "店铺ID，如果为 None 则返回所有店铺的数据"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "返回数量限制，默认 10",
                                "default": 10
                            },
                            "days": {
                                "type": "integer",
                                "description": "统计天数，默认 30 天",
                                "default": 30
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "emit_dashboard_command",
                    "description": "发送 Dashboard 指令，用于控制前端图表和面板的显示。当用户要求展示图表、切换指标、设置时间范围时使用此函数",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command_type": {
                                "type": "string",
                                "enum": ["SET_DATE_RANGE", "SET_METRIC_CHART", "FOCUS_SKU", "COMPARE_SHOPS", "REFRESH_DATA"],
                                "description": "指令类型"
                            },
                            "payload": {
                                "type": "object",
                                "description": "指令负载数据",
                                "properties": {
                                    "start_date": {"type": "string", "description": "开始日期 (YYYY-MM-DD)"},
                                    "end_date": {"type": "string", "description": "结束日期 (YYYY-MM-DD)"},
                                    "days": {"type": "integer", "description": "天数"},
                                    "metric": {"type": "string", "enum": ["gmv", "orders", "profit", "refund_rate"], "description": "指标类型"},
                                    "chart_type": {"type": "string", "enum": ["line", "bar", "pie"], "description": "图表类型"},
                                    "sku": {"type": "string", "description": "SKU 编号"},
                                    "product_id": {"type": "integer", "description": "商品ID"},
                                    "shop_ids": {"type": "array", "items": {"type": "integer"}, "description": "店铺ID列表"},
                                    "compare_metric": {"type": "string", "description": "对比指标"},
                                    "force": {"type": "boolean", "description": "是否强制刷新"}
                                }
                            }
                        },
                        "required": ["command_type", "payload"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], shop_ids: Optional[List[int]] = None) -> Any:
        """
        执行工具函数
        
        Args:
            tool_name: 工具函数名称
            arguments: 函数参数
            shop_ids: 当前用户有权限的店铺ID列表
            
        Returns:
            工具函数执行结果
        """
        try:
            if tool_name == "get_shop_dashboard":
                return self._get_shop_dashboard(
                    shop_id=arguments.get("shop_id"),
                    days=arguments.get("days", 7),
                    shop_ids=shop_ids
                )
            elif tool_name == "get_order_trend":
                return self._get_order_trend(
                    shop_id=arguments.get("shop_id"),
                    days=arguments.get("days", 7),
                    shop_ids=shop_ids
                )
            elif tool_name == "list_top_profit_skus":
                return self._list_top_profit_skus(
                    shop_id=arguments.get("shop_id"),
                    limit=arguments.get("limit", 10),
                    days=arguments.get("days", 30),
                    shop_ids=shop_ids
                )
            elif tool_name == "list_top_loss_skus":
                return self._list_top_loss_skus(
                    shop_id=arguments.get("shop_id"),
                    limit=arguments.get("limit", 10),
                    days=arguments.get("days", 30),
                    shop_ids=shop_ids
                )
            elif tool_name == "emit_dashboard_command":
                # Dashboard 指令直接返回，由前端处理
                return {
                    "type": "dashboard_command",
                    "command": {
                        "type": arguments["command_type"],
                        "payload": arguments["payload"]
                    }
                }
            else:
                return {"error": f"未知的工具函数: {tool_name}"}
        except Exception as e:
            logger.error(f"执行工具函数 {tool_name} 失败: {e}", exc_info=True)
            return {"error": str(e)}
    
    def _get_shop_dashboard(self, shop_id: Optional[int], days: int, shop_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """获取店铺仪表盘数据"""
        from datetime import timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 构建查询
        query = self.db.query(Order).filter(
            Order.order_time >= start_date,
            Order.order_time <= end_date
        )
        
        if shop_id:
            query = query.filter(Order.shop_id == shop_id)
        elif shop_ids:
            query = query.filter(Order.shop_id.in_(shop_ids))
        
        orders = query.all()
        
        total_gmv = sum(float(order.total_price or 0) for order in orders)
        total_orders = len(orders)
        total_cost = sum(float(order.cost_price or 0) * float(order.quantity or 0) for order in orders)
        total_profit = total_gmv - total_cost
        refund_count = len([o for o in orders if o.status.value in ["REFUNDED", "CANCELLED"]])
        refund_rate = (refund_count / total_orders * 100) if total_orders > 0 else 0
        
        return {
            "shop_id": shop_id,
            "period_days": days,
            "total_gmv": round(total_gmv, 2),
            "total_orders": total_orders,
            "total_profit": round(total_profit, 2),
            "profit_margin": round((total_profit / total_gmv * 100) if total_gmv > 0 else 0, 2),
            "refund_rate": round(refund_rate, 2),
            "avg_order_value": round(total_gmv / total_orders if total_orders > 0 else 0, 2)
        }
    
    def _get_order_trend(self, shop_id: Optional[int], days: int, shop_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """获取订单趋势数据"""
        from datetime import timedelta
        from collections import defaultdict
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = self.db.query(Order).filter(
            Order.order_time >= start_date,
            Order.order_time <= end_date
        )
        
        if shop_id:
            query = query.filter(Order.shop_id == shop_id)
        elif shop_ids:
            query = query.filter(Order.shop_id.in_(shop_ids))
        
        orders = query.all()
        
        # 按日期分组
        daily_data = defaultdict(lambda: {"gmv": 0, "orders": 0})
        for order in orders:
            date_key = order.order_time.date().isoformat()
            daily_data[date_key]["gmv"] += float(order.total_price or 0)
            daily_data[date_key]["orders"] += 1
        
        # 转换为列表格式
        dates = sorted(daily_data.keys())
        trend_data = {
            "dates": dates,
            "gmv": [daily_data[date]["gmv"] for date in dates],
            "orders": [daily_data[date]["orders"] for date in dates]
        }
        
        return trend_data
    
    def _list_top_profit_skus(self, shop_id: Optional[int], limit: int, days: int, shop_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """列出高利润 SKU"""
        from datetime import timedelta
        from collections import defaultdict
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = self.db.query(Order).filter(
            Order.order_time >= start_date,
            Order.order_time <= end_date
        )
        
        if shop_id:
            query = query.filter(Order.shop_id == shop_id)
        elif shop_ids:
            query = query.filter(Order.shop_id.in_(shop_ids))
        
        orders = query.all()
        
        # 按 SKU 聚合
        sku_data = defaultdict(lambda: {"gmv": 0, "cost": 0, "quantity": 0, "product_name": ""})
        for order in orders:
            sku = order.product_sku or "未知"
            sku_data[sku]["gmv"] += float(order.total_price or 0)
            sku_data[sku]["cost"] += float(order.cost_price or 0) * float(order.quantity or 0)
            sku_data[sku]["quantity"] += int(order.quantity or 0)
            if not sku_data[sku]["product_name"]:
                sku_data[sku]["product_name"] = order.product_name or "未知商品"
        
        # 计算利润并排序
        sku_list = []
        for sku, data in sku_data.items():
            profit = data["gmv"] - data["cost"]
            sku_list.append({
                "sku": sku,
                "product_name": data["product_name"],
                "gmv": round(data["gmv"], 2),
                "cost": round(data["cost"], 2),
                "profit": round(profit, 2),
                "profit_margin": round((profit / data["gmv"] * 100) if data["gmv"] > 0 else 0, 2),
                "quantity": data["quantity"]
            })
        
        # 按利润排序
        sku_list.sort(key=lambda x: x["profit"], reverse=True)
        
        return sku_list[:limit]
    
    def _list_top_loss_skus(self, shop_id: Optional[int], limit: int, days: int, shop_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """列出亏损 SKU"""
        profit_skus = self._list_top_profit_skus(shop_id, 1000, days, shop_ids)  # 获取所有 SKU
        loss_skus = [sku for sku in profit_skus if sku["profit"] < 0]
        loss_skus.sort(key=lambda x: x["profit"])  # 按亏损金额排序（负数，最小的在最前）
        return loss_skus[:limit]
    
    def chat_completion_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str = "gpt-4o",
        shop_ids: Optional[List[int]] = None,
        temperature: float = 0.7
    ) -> Iterator[str]:
        """
        流式聊天完成（支持 Function Calling）
        
        Args:
            messages: 消息列表
            model: 模型名称
            shop_ids: 当前用户有权限的店铺ID列表
            temperature: 温度参数
            
        Yields:
            响应内容（JSON 格式字符串）
        """
        if not self.client:
            yield f"data: {json.dumps({'type': 'error', 'data': 'OpenAI 客户端未初始化'})}\n\n"
            return
        
        try:
            # 获取工具定义
            tools = self.get_available_tools()
            
            # 调用 OpenAI API
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=temperature,
                stream=True
            )
            
            # 工具调用状态跟踪
            tool_calls_map = {}  # {tool_call_id: {name, args}}
            
            for chunk in stream:
                if not chunk.choices:
                    continue
                
                choice = chunk.choices[0]
                delta = choice.delta
                
                # 处理工具调用
                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        tool_call_id = tool_call_delta.id
                        if tool_call_id:
                            if tool_call_id not in tool_calls_map:
                                tool_calls_map[tool_call_id] = {
                                    "name": "",
                                    "arguments": ""
                                }
                            
                            if tool_call_delta.function:
                                if tool_call_delta.function.name:
                                    tool_calls_map[tool_call_id]["name"] = tool_call_delta.function.name
                                
                                if tool_call_delta.function.arguments:
                                    tool_calls_map[tool_call_id]["arguments"] += tool_call_delta.function.arguments
                
                # 处理内容
                if delta.content:
                    content_data = {
                        'type': 'content',
                        'data': delta.content
                    }
                    yield f"data: {json.dumps(content_data)}\n\n"
                
                # 检查是否完成工具调用
                if choice.finish_reason == "tool_calls":
                    # 执行所有工具调用
                    assistant_message = {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": []
                    }
                    
                    for tool_call_id, tool_call_data in tool_calls_map.items():
                        try:
                            tool_name = tool_call_data["name"]
                            tool_args_str = tool_call_data["arguments"]
                            tool_args = json.loads(tool_args_str) if tool_args_str else {}
                            
                            # 执行工具
                            tool_result = self.execute_tool(tool_name, tool_args, shop_ids)
                            
                            # 检查是否是 Dashboard 指令
                            if isinstance(tool_result, dict) and tool_result.get("type") == "dashboard_command":
                                dashboard_data = {
                                    'type': 'dashboard_command',
                                    'data': tool_result['command']
                                }
                                yield f"data: {json.dumps(dashboard_data)}\n\n"
                            
                            # 添加到 assistant 消息
                            assistant_message["tool_calls"].append({
                                "id": tool_call_id,
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": tool_args_str
                                }
                            })
                            
                            # 添加工具结果消息
                            messages.append(assistant_message)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": json.dumps(tool_result, ensure_ascii=False)
                            })
                            
                        except Exception as e:
                            logger.error(f"执行工具调用失败: {e}", exc_info=True)
                            error_data = {
                                'type': 'error',
                                'data': f'工具调用失败: {str(e)}'
                            }
                            yield f"data: {json.dumps(error_data)}\n\n"
                    
                    # 继续调用 API 获取最终回复（递归处理）
                    for chunk2 in self._continue_conversation(messages, model, tools, temperature, shop_ids):
                        yield chunk2
                    
                    # 重置工具调用状态
                    tool_calls_map = {}
            
            if choice.finish_reason == "stop":
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            logger.error(f"ChatKit 流式调用失败: {e}", exc_info=True)
            error_data = {
                'type': 'error',
                'data': f'AI 调用失败: {str(e)}'
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    def _continue_conversation(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        tools: List[Dict[str, Any]],
        temperature: float,
        shop_ids: Optional[List[int]]
    ) -> Iterator[str]:
        """
        继续对话（处理工具调用后的回复）
        
        这是一个递归方法，可以处理多轮工具调用
        """
        if not self.client:
            return
        
        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=temperature,
                stream=True
            )
            
            tool_calls_map = {}
            
            for chunk in stream:
                if not chunk.choices:
                    continue
                
                choice = chunk.choices[0]
                delta = choice.delta
                
                # 处理工具调用
                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        tool_call_id = tool_call_delta.id
                        if tool_call_id:
                            if tool_call_id not in tool_calls_map:
                                tool_calls_map[tool_call_id] = {
                                    "name": "",
                                    "arguments": ""
                                }
                            
                            if tool_call_delta.function:
                                if tool_call_delta.function.name:
                                    tool_calls_map[tool_call_id]["name"] = tool_call_delta.function.name
                                
                                if tool_call_delta.function.arguments:
                                    tool_calls_map[tool_call_id]["arguments"] += tool_call_delta.function.arguments
                
                # 处理内容
                if delta.content:
                    content_data = {
                        'type': 'content',
                        'data': delta.content
                    }
                    yield f"data: {json.dumps(content_data)}\n\n"
                
                # 检查是否完成工具调用（递归处理）
                if choice.finish_reason == "tool_calls":
                    assistant_message = {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": []
                    }
                    
                    for tool_call_id, tool_call_data in tool_calls_map.items():
                        try:
                            tool_name = tool_call_data["name"]
                            tool_args_str = tool_call_data["arguments"]
                            tool_args = json.loads(tool_args_str) if tool_args_str else {}
                            
                            tool_result = self.execute_tool(tool_name, tool_args, shop_ids)
                            
                            if isinstance(tool_result, dict) and tool_result.get("type") == "dashboard_command":
                                dashboard_data = {
                                    'type': 'dashboard_command',
                                    'data': tool_result['command']
                                }
                                yield f"data: {json.dumps(dashboard_data)}\n\n"
                            
                            assistant_message["tool_calls"].append({
                                "id": tool_call_id,
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": tool_args_str
                                }
                            })
                            
                            messages.append(assistant_message)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": json.dumps(tool_result, ensure_ascii=False)
                            })
                            
                        except Exception as e:
                            logger.error(f"执行工具调用失败: {e}", exc_info=True)
                            error_data = {
                                'type': 'error',
                                'data': f'工具调用失败: {str(e)}'
                            }
                            yield f"data: {json.dumps(error_data)}\n\n"
                    
                    # 递归继续对话
                    for chunk2 in self._continue_conversation(messages, model, tools, temperature, shop_ids):
                        yield chunk2
                    
                    return
                
                if choice.finish_reason == "stop":
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    return
                    
        except Exception as e:
            logger.error(f"继续对话失败: {e}", exc_info=True)
            error_data = {
                'type': 'error',
                'data': f'继续对话失败: {str(e)}'
            }
            yield f"data: {json.dumps(error_data)}\n\n"

