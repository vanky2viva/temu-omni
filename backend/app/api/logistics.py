"""物流管理API"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
import re

from app.core.database import get_db
from app.models.order import Order
from pydantic import BaseModel

router = APIRouter(prefix="/logistics", tags=["logistics"])


class CityOrderStats(BaseModel):
    """城市订单统计"""
    city: str
    order_count: int
    country: Optional[str] = None


class DeliveryHeatmapResponse(BaseModel):
    """配送热力图响应"""
    city_stats: List[CityOrderStats]
    total_orders: int
    unique_cities: int


@router.get("/delivery-heatmap", response_model=DeliveryHeatmapResponse)
def get_delivery_heatmap(
    shop_id: Optional[int] = Query(None, description="店铺ID，不提供则统计所有店铺"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """
    获取配送地址热力图数据
    
    从订单的raw_data中提取城市信息，统计每个城市的订单数量
    """
    # 构建查询
    query = db.query(Order)
    
    if shop_id:
        query = query.filter(Order.shop_id == shop_id)
    
    if start_date:
        query = query.filter(Order.order_time >= start_date)
    
    if end_date:
        query = query.filter(Order.order_time <= end_date)
    
    orders = query.all()
    
    # 从raw_data中提取城市信息
    city_stats_dict = {}
    
    # 可能的城市字段名（中文和英文）
    city_field_names = [
        '城市', '收货城市', '收货人城市', '配送城市', '收件城市',
        'city', 'shipping_city', 'delivery_city', 'receiver_city',
        '收货地址城市', '配送地址城市'
    ]
    
    for order in orders:
        city = None
        country = order.shipping_country
        
        # 优先从shipping_country判断（如果是完整地址）
        # 然后尝试从raw_data中提取
        
        if order.raw_data:
            try:
                raw_data = json.loads(order.raw_data)
                
                # 尝试各种可能的字段名
                for field_name in city_field_names:
                    if field_name in raw_data and raw_data[field_name]:
                        city_value = str(raw_data[field_name]).strip()
                        if city_value and city_value not in ['', 'None', 'null']:
                            city = city_value
                            break
                
                # 如果从字段中没找到，尝试从地址字段中解析
                if not city:
                    address_fields = ['收货地址', '配送地址', '地址', 'address', 'shipping_address', 'delivery_address']
                    for addr_field in address_fields:
                        if addr_field in raw_data and raw_data[addr_field]:
                            address = str(raw_data[addr_field])
                            # 解析地址：尝试提取城市名
                            # 中国城市名通常包含"市"、"省"、"自治区"等
                            # 地址格式可能是：省/市/区/街道 或 国家/省/市
                            
                            # 匹配"XX市"格式（最常见）
                            city_match = re.search(r'([\u4e00-\u9fa5]+?市)', address)
                            if city_match:
                                city = city_match.group(1)
                                break
                            
                            # 匹配"XX省XX市"格式
                            province_city_match = re.search(r'([\u4e00-\u9fa5]+?省)([\u4e00-\u9fa5]+?市)', address)
                            if province_city_match:
                                city = province_city_match.group(2)
                                break
                            
                            # 匹配英文地址格式：City, State 或 City, Country
                            city_match_en = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*[A-Z]', address)
                            if city_match_en:
                                city = city_match_en.group(1)
                                break
                
            except (json.JSONDecodeError, TypeError):
                # 如果raw_data解析失败，跳过
                continue
        
        # 如果还是没有找到城市，但有国家信息，可以使用国家名
        if not city:
            if country:
                city = country  # 作为后备方案
            else:
                continue
        
        # 统计
        city_key = city.lower().strip() if city else '未知'
        if city_key not in city_stats_dict:
            city_stats_dict[city_key] = {
                'city': city,
                'country': country,
                'order_count': 0
            }
        city_stats_dict[city_key]['order_count'] += 1
    
    # 转换为列表并排序
    city_stats = [
        CityOrderStats(
            city=stats['city'],
            order_count=stats['order_count'],
            country=stats.get('country')
        )
        for stats in sorted(city_stats_dict.values(), key=lambda x: x['order_count'], reverse=True)
    ]
    
    total_orders = sum(stats['order_count'] for stats in city_stats_dict.values())
    unique_cities = len(city_stats)
    
    return DeliveryHeatmapResponse(
        city_stats=city_stats,
        total_orders=total_orders,
        unique_cities=unique_cities
    )
