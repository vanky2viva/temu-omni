"""订单管理API"""
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderStatistics

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/", response_model=List[OrderResponse])
def get_orders(
    skip: int = 0,
    limit: int = 100,
    shop_id: Optional[int] = None,
    status_filter: Optional[OrderStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取订单列表"""
    query = db.query(Order)
    
    if shop_id:
        query = query.filter(Order.shop_id == shop_id)
    
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    if start_date:
        query = query.filter(Order.order_time >= start_date)
    
    if end_date:
        query = query.filter(Order.order_time <= end_date)
    
    orders = query.order_by(Order.order_time.desc()).offset(skip).limit(limit).all()
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取订单详情"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    return order


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """创建订单"""
    # 检查订单编号是否已存在
    existing_order = db.query(Order).filter(Order.order_sn == order.order_sn).first()
    if existing_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="订单编号已存在"
        )
    
    db_order = Order(**order.model_dump())
    
    # 如果有成本信息，计算利润
    if db_order.total_cost:
        db_order.calculate_profit()
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新订单信息"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    update_data = order_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    # 重新计算利润
    if order.total_cost:
        order.calculate_profit()
    
    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除订单"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    db.delete(order)
    db.commit()
    return None


@router.get("/statistics/summary", response_model=OrderStatistics)
def get_order_statistics(
    shop_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取订单统计信息（GMV、成本、利润等）
    
    Args:
        shop_id: 店铺ID（可选，不指定则统计所有店铺）
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
    
    Returns:
        订单统计信息，包括GMV、总成本、总利润、利润率等
    """
    # 构建查询
    query = db.query(Order).filter(
        Order.total_cost.isnot(None),  # 只统计有成本信息的订单
        Order.profit.isnot(None)
    )
    
    if shop_id:
        query = query.filter(Order.shop_id == shop_id)
    
    if start_date:
        query = query.filter(Order.order_time >= start_date)
    
    if end_date:
        query = query.filter(Order.order_time <= end_date)
    
    # 获取订单列表
    orders = query.all()
    
    if not orders:
        # 没有订单数据，返回零值
        return OrderStatistics(
            total_orders=0,
            total_gmv=Decimal('0'),
            total_cost=Decimal('0'),
            total_profit=Decimal('0'),
            avg_order_value=Decimal('0'),
            profit_margin=0.0
        )
    
    # 计算统计数据，统一转换为CNY
    from app.utils.currency import CurrencyConverter
    
    total_orders = len(orders)
    total_gmv = sum(
        CurrencyConverter.convert_to_cny(
            order.total_price or Decimal('0'),
            order.currency or 'USD'
        ) for order in orders
    )
    total_cost = sum(
        CurrencyConverter.convert_to_cny(
            order.total_cost or Decimal('0'),
            order.currency or 'USD'
        ) for order in orders if order.total_cost
    )
    total_profit = sum(
        CurrencyConverter.convert_to_cny(
            order.profit or Decimal('0'),
            order.currency or 'USD'
        ) for order in orders if order.profit
    )
    
    # 平均订单价值
    avg_order_value = total_gmv / Decimal(total_orders) if total_orders > 0 else Decimal('0')
    
    # 利润率
    profit_margin = float(total_profit / total_gmv * 100) if total_gmv > 0 else 0.0
    
    return OrderStatistics(
        total_orders=total_orders,
        total_gmv=total_gmv,
        total_cost=total_cost,
        total_profit=total_profit,
        avg_order_value=avg_order_value,
        profit_margin=profit_margin
    )

