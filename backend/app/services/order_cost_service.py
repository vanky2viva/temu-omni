"""订单成本计算服务"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from decimal import Decimal
from datetime import datetime
from loguru import logger

from app.models.order import Order, OrderStatus
from app.models.product import Product, ProductCost
from app.models.shop import Shop


class OrderCostCalculationService:
    """订单成本计算服务"""
    
    def __init__(self, db: Session):
        """
        初始化服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def _get_product_cost(
        self,
        shop_id: int,
        product_sku: Optional[str],
        product_sku_id: Optional[str],
        spu_id: Optional[str],
        order_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取商品成本价格
        
        匹配优先级：
        1. productSkuId (product_id)
        2. extCode (SKU货号)
        3. spu_id
        
        Args:
            shop_id: 店铺ID
            product_sku: SKU货号 (extCode)
            product_sku_id: 产品SKU ID (productSkuId)
            spu_id: SPU ID
            order_time: 订单时间，用于获取历史成本价
            
        Returns:
            商品成本信息字典或None
        """
        product = None
        match_method = None
        
        # 优先级1：通过 productSkuId 匹配
        if product_sku_id:
            product = self.db.query(Product).filter(
                Product.shop_id == shop_id,
                Product.product_id == str(product_sku_id)
            ).first()
            
            if product:
                match_method = "productSkuId"
                logger.debug(f"✅ 通过productSkuId匹配到商品: {product_sku_id} -> {product.sku}")
        
        # 优先级2：通过 extCode (SKU货号) 匹配
        if not product and product_sku:
            product = self.db.query(Product).filter(
                Product.shop_id == shop_id,
                Product.sku == product_sku
            ).first()
            
            if product:
                match_method = "extCode"
                logger.debug(f"✅ 通过extCode (SKU货号)匹配到商品: {product_sku} -> {product.product_id}")
        
        # 优先级3：通过 spu_id 匹配（备用）
        if not product and spu_id:
            product = self.db.query(Product).filter(
                Product.shop_id == shop_id,
                Product.spu_id == spu_id
            ).first()
            
            if product:
                match_method = "spu_id"
                logger.debug(f"✅ 通过spu_id匹配到商品: {spu_id} -> {product.sku}")
        
        if not product:
            logger.debug(
                f"❌ 未找到匹配的商品 - "
                f"productSkuId: {product_sku_id}, extCode: {product_sku}, spu_id: {spu_id}"
            )
            return None
        
        # 获取供货价
        supply_price = product.current_price
        
        # 获取订单时间有效的成本价
        cost_price = None
        cost_record = None
        
        if order_time:
            # 查询在订单时间有效的成本记录
            cost_record = self.db.query(ProductCost).filter(
                ProductCost.product_id == product.id,
                ProductCost.effective_from <= order_time,
                (ProductCost.effective_to.is_(None)) | (ProductCost.effective_to > order_time)
            ).order_by(ProductCost.effective_from.desc()).first()
            
            if cost_record:
                cost_price = cost_record.cost_price
                logger.debug(
                    f"找到商品 {product.sku} 在 {order_time} 的有效成本价: {cost_price}"
                )
        
        # 如果没有找到订单时间的成本价，则使用当前最新的成本价（fallback）
        if not cost_record:
            cost_record = self.db.query(ProductCost).filter(
                ProductCost.product_id == product.id,
                ProductCost.effective_to.is_(None)
            ).order_by(ProductCost.effective_from.desc()).first()
            
            if cost_record:
                cost_price = cost_record.cost_price
                if order_time:
                    logger.debug(
                        f"未找到订单时间的成本价，使用当前成本价: {product.sku} = {cost_price}"
                    )
        
        # 如果没有找到成本价，记录日志
        if not cost_price:
            logger.debug(
                f"商品 {product.sku} 没有成本价 - "
                f"匹配方式: {match_method}"
            )
        
        # 货币转换 - 统一转换为CNY
        from app.utils.currency import CurrencyConverter
        usd_to_cny_rate = CurrencyConverter.USD_TO_CNY_RATE
        
        # 转换供货价为CNY
        supply_price_cny = None
        if supply_price:
            if product.currency == 'USD':
                supply_price_cny = float(supply_price) * usd_to_cny_rate
            else:
                supply_price_cny = float(supply_price)
        
        # 转换成本价为CNY
        cost_price_cny = None
        if cost_price:
            cost_currency = cost_record.currency if cost_record else product.currency
            if cost_currency == 'USD':
                cost_price_cny = float(cost_price) * usd_to_cny_rate
            else:
                cost_price_cny = float(cost_price)
        
        return {
            'product_id': product.id,
            'supply_price': supply_price_cny,  # 已转换为CNY
            'cost_price': cost_price_cny,  # 已转换为CNY
            'currency': 'CNY',  # 统一为CNY
            'match_method': match_method
        }
    
    def calculate_order_costs(
        self,
        shop_id: Optional[int] = None,
        order_ids: Optional[List[int]] = None,
        force_recalculate: bool = False
    ) -> Dict[str, int]:
        """
        计算订单成本和利润
        
        Args:
            shop_id: 店铺ID，None表示所有店铺
            order_ids: 订单ID列表，None表示所有订单
            force_recalculate: 是否强制重新计算（即使已有成本）
            
        Returns:
            计算结果统计
        """
        logger.info("开始计算订单成本和利润...")
        
        # 构建查询条件
        filters = []
        
        if shop_id:
            filters.append(Order.shop_id == shop_id)
        
        if order_ids:
            filters.append(Order.id.in_(order_ids))
        
        # 排除已取消和已退款的订单
        filters.append(Order.status != OrderStatus.CANCELLED)
        filters.append(Order.status != OrderStatus.REFUNDED)
        
        # 如果不是强制重新计算，只处理没有成本数据或订单金额为0的订单
        if not force_recalculate:
            filters.append(
                or_(
                    Order.unit_cost.is_(None),
                    Order.total_cost.is_(None),
                    Order.total_price == 0,  # 订单金额为0也需要重新计算
                    Order.unit_price == 0    # 单价为0也需要重新计算
                )
            )
        
        # 查询需要计算的订单
        orders = self.db.query(Order).filter(and_(*filters)).all()
        
        logger.info(f"找到 {len(orders)} 个需要计算成本的订单")
        
        if not orders:
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'skipped': 0
            }
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for order in orders:
            try:
                # 获取商品成本信息
                # 从订单的 product_id (Temu商品ID) 获取 product_sku_id
                product_sku_id = None
                if order.product:
                    product_sku_id = order.product.product_id
                
                cost_info = self._get_product_cost(
                    shop_id=order.shop_id,
                    product_sku=order.product_sku,
                    product_sku_id=product_sku_id,
                    spu_id=order.spu_id,
                    order_time=order.order_time
                )
                
                # 如果没有找到匹配的商品或价格信息，跳过
                if not cost_info:
                    logger.debug(
                        f"订单 {order.order_sn} 未找到匹配的商品 - "
                        f"SKU: {order.product_sku}, SPU: {order.spu_id}"
                    )
                    skipped_count += 1
                    continue
                
                # 获取供货价格和成本价格
                supply_price = cost_info.get('supply_price')
                cost_price = cost_info.get('cost_price')
                
                quantity = Decimal(str(order.quantity))
                has_supply_price = supply_price is not None and Decimal(str(supply_price)) > 0
                has_cost_price = cost_price is not None and Decimal(str(cost_price)) > 0
                
                # 如果既没有供货价格也没有成本价格，跳过
                if not has_supply_price and not has_cost_price:
                    logger.debug(
                        f"订单 {order.order_sn} 没有供货价格和成本价格 - "
                        f"SKU: {order.product_sku}"
                    )
                    skipped_count += 1
                    continue
                
                # 计算订单金额（供货价格 × 数量）- 统一为CNY
                if has_supply_price:
                    unit_price = Decimal(str(supply_price))
                    total_price = unit_price * quantity
                    
                    # 更新订单价格（统一为CNY）
                    order.unit_price = unit_price
                    order.total_price = total_price
                    order.currency = 'CNY'  # 统一货币单位为CNY
                else:
                    # 如果没有供货价格，使用现有的订单金额（如果有）
                    total_price = order.total_price if order.total_price else Decimal('0')
                
                # 计算成本和利润（统一为CNY）
                if has_cost_price:
                    unit_cost = Decimal(str(cost_price))
                    total_cost = unit_cost * quantity
                    profit = total_price - total_cost
                    
                    # 更新订单成本和利润
                    order.unit_cost = unit_cost
                    order.total_cost = total_cost
                    order.profit = profit
                
                # 如果找到匹配的商品，更新 product_id 关联
                if cost_info.get('product_id') and not order.product_id:
                    order.product_id = cost_info['product_id']
                
                self.db.add(order)
                success_count += 1
                
                logger.debug(
                    f"✅ 订单 {order.order_sn} 计算完成 - "
                    f"订单金额: {order.total_price}, 成本: {order.total_cost}, 利润: {order.profit} "
                    f"(匹配方式: {cost_info.get('match_method', 'unknown')})"
                )
                
            except Exception as e:
                logger.error(f"计算订单 {order.order_sn} 成本失败: {e}")
                failed_count += 1
                continue
        
        # 提交事务
        try:
            self.db.commit()
            logger.info(
                f"订单成本计算完成 - "
                f"成功: {success_count}, 失败: {failed_count}, 跳过: {skipped_count}"
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"提交订单成本更新失败: {e}")
            raise
        
        return {
            'total': len(orders),
            'success': success_count,
            'failed': failed_count,
            'skipped': skipped_count
        }
    
    def get_daily_collection_forecast(
        self,
        shop_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        获取每日预估回款金额
        
        Args:
            shop_id: 店铺ID，None表示所有店铺
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            每日预估回款列表
        """
        from sqlalchemy import func, case
        from app.utils.currency import CurrencyConverter
        
        # 构建查询条件
        filters = []
        
        if shop_id:
            filters.append(Order.shop_id == shop_id)
        
        if start_date:
            filters.append(Order.order_time >= start_date)
        
        if end_date:
            filters.append(Order.order_time <= end_date)
        
        # 排除已取消和已退款的订单
        filters.append(Order.status != OrderStatus.CANCELLED)
        filters.append(Order.status != OrderStatus.REFUNDED)
        
        # 只统计有有效金额和利润的订单
        filters.append(Order.total_price > 0)
        filters.append(Order.profit.isnot(None))
        
        # 统一转换为CNY
        usd_rate = CurrencyConverter.USD_TO_CNY_RATE
        
        # 按日期分组统计
        daily_stats = self.db.query(
            func.date(Order.order_time).label('date'),
            func.count(Order.id).label('order_count'),
            func.sum(
                case(
                    (Order.currency == 'USD', Order.total_price * usd_rate),
                    (Order.currency == 'CNY', Order.total_price),
                    else_=Order.total_price * usd_rate
                )
            ).label('total_amount'),
            func.sum(
                case(
                    (Order.currency == 'USD', Order.total_cost * usd_rate),
                    (Order.currency == 'CNY', Order.total_cost),
                    else_=Order.total_cost * usd_rate
                )
            ).label('total_cost'),
            func.sum(
                case(
                    (Order.currency == 'USD', Order.profit * usd_rate),
                    (Order.currency == 'CNY', Order.profit),
                    else_=Order.profit * usd_rate
                )
            ).label('total_profit')
        ).filter(and_(*filters)).group_by(
            func.date(Order.order_time)
        ).order_by(func.date(Order.order_time)).all()
        
        # 格式化结果
        result = []
        for stat in daily_stats:
            profit_margin = 0
            if stat.total_amount and float(stat.total_amount) > 0:
                profit_margin = (float(stat.total_profit or 0) / float(stat.total_amount)) * 100
            
            result.append({
                'date': stat.date.isoformat() if stat.date else None,
                'order_count': stat.order_count or 0,
                'total_amount': float(stat.total_amount or 0),
                'total_cost': float(stat.total_cost or 0),
                'total_profit': float(stat.total_profit or 0),
                'profit_margin': round(profit_margin, 2)
            })
        
        return result

