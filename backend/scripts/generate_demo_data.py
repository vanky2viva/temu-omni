"""生成演示数据脚本"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta
import random
from decimal import Decimal

from app.core.database import SessionLocal
from app.models.shop import Shop
from app.models.order import Order, OrderStatus
from app.models.product import Product, ProductCost
from app.models.activity import Activity, ActivityType


def clear_demo_data(db):
    """清除演示数据"""
    print("清除旧的演示数据...")
    # 删除所有演示店铺及其关联数据
    demo_shops = db.query(Shop).filter(Shop.shop_id.like("DEMO_%")).all()
    for shop in demo_shops:
        db.delete(shop)
    db.commit()
    print("✓ 演示数据已清除")


def generate_shops(db, count=3):
    """生成演示店铺"""
    print(f"\n生成 {count} 个演示店铺...")
    
    regions = ["US", "UK", "DE", "FR", "AU"]
    entities = ["公司A", "公司B", "公司C"]
    
    shops = []
    for i in range(count):
        shop = Shop(
            shop_id=f"DEMO_SHOP_{i+1:03d}",
            shop_name=f"演示店铺{i+1} ({regions[i % len(regions)]})",
            region=regions[i % len(regions)],
            entity=entities[i % len(entities)],
            app_key=f"demo_app_key_{i+1}",
            app_secret=f"demo_app_secret_{i+1}",
            is_active=True,
            description=f"这是演示店铺{i+1}，用于测试系统功能",
            created_at=datetime.now() - timedelta(days=random.randint(30, 180)),
            last_sync_at=datetime.now() - timedelta(hours=random.randint(1, 24))
        )
        db.add(shop)
        shops.append(shop)
    
    db.commit()
    print(f"✓ 已创建 {len(shops)} 个店铺")
    return shops


def generate_products(db, shops, products_per_shop=10):
    """生成演示商品"""
    print(f"\n为每个店铺生成 {products_per_shop} 个商品...")
    
    product_names = [
        "无线蓝牙耳机", "智能手表", "手机壳", "充电宝", "数据线",
        "蓝牙音箱", "自拍杆", "手机支架", "屏幕保护膜", "车载充电器",
        "USB转换器", "键盘", "鼠标", "鼠标垫", "笔记本支架",
        "户外背包", "运动水壶", "瑜伽垫", "跳绳", "哑铃"
    ]
    
    # 负责人列表
    managers = [
        "张三", "李四", "王五", "赵六", "钱七",
        "孙八", "周九", "吴十", "郑十一", "陈十二"
    ]
    
    all_products = []
    
    for shop in shops:
        for i in range(products_per_shop):
            product_name = product_names[i % len(product_names)]
            price = Decimal(random.uniform(5, 100)).quantize(Decimal('0.01'))
            cost = (price * Decimal(random.uniform(0.4, 0.7))).quantize(Decimal('0.01'))
            
            product = Product(
                shop_id=shop.id,
                product_id=f"PROD_{shop.id}_{i+1:03d}",
                product_name=f"{product_name} - {shop.region}款",
                sku=f"SKU-{shop.id}-{i+1:04d}",
                current_price=price,
                currency="USD",
                stock_quantity=random.randint(0, 500),
                is_active=random.choice([True, True, True, False]),  # 75%在售
                category=random.choice(["电子产品", "配件", "运动用品", "生活用品"]),
                manager=random.choice(managers),  # 随机分配负责人
                created_at=datetime.now() - timedelta(days=random.randint(10, 100))
            )
            db.add(product)
            all_products.append(product)
            
            # 为商品添加成本记录
            db.flush()  # 确保product有ID
            product_cost = ProductCost(
                product_id=product.id,
                cost_price=cost,
                currency="USD",
                effective_from=product.created_at,
                notes="初始成本"
            )
            db.add(product_cost)
    
    db.commit()
    print(f"✓ 已创建 {len(all_products)} 个商品及其成本记录")
    return all_products


def generate_orders(db, shops, products, orders_per_shop=100):
    """生成演示订单"""
    print(f"\n为每个店铺生成 {orders_per_shop} 个订单...")
    
    all_orders = []
    order_counter = 1
    
    for shop in shops:
        # 获取该店铺的商品
        shop_products = [p for p in products if p.shop_id == shop.id]
        
        for i in range(orders_per_shop):
            product = random.choice(shop_products)
            quantity = random.randint(1, 5)
            
            # 价格可能有小幅波动
            unit_price = product.current_price * Decimal(random.uniform(0.95, 1.05))
            unit_price = unit_price.quantize(Decimal('0.01'))
            total_price = unit_price * quantity
            
            # 获取成本
            cost_record = db.query(ProductCost).filter(
                ProductCost.product_id == product.id
            ).first()
            
            unit_cost = cost_record.cost_price if cost_record else unit_price * Decimal('0.6')
            total_cost = unit_cost * quantity
            profit = total_price - total_cost
            
            # 订单时间：过去90天内随机
            order_time = datetime.now() - timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # 订单状态权重：大部分是已完成
            status = random.choices(
                list(OrderStatus),
                weights=[5, 10, 15, 20, 40, 5, 5]  # completed权重最高
            )[0]
            
            order = Order(
                shop_id=shop.id,
                order_sn=f"ORD{order_counter:08d}",
                temu_order_id=f"TEMU{order_counter:010d}",
                product_id=product.id,
                product_name=product.product_name,
                product_sku=product.sku,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                currency="USD",
                unit_cost=unit_cost,
                total_cost=total_cost,
                profit=profit,
                status=status,
                order_time=order_time,
                payment_time=order_time + timedelta(minutes=random.randint(5, 60)) if status != OrderStatus.PENDING else None,
                shipping_time=order_time + timedelta(days=random.randint(1, 3)) if status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.COMPLETED] else None,
                delivery_time=order_time + timedelta(days=random.randint(5, 15)) if status in [OrderStatus.DELIVERED, OrderStatus.COMPLETED] else None,
                shipping_country=shop.region,
                created_at=order_time
            )
            
            db.add(order)
            all_orders.append(order)
            order_counter += 1
    
    db.commit()
    print(f"✓ 已创建 {len(all_orders)} 个订单")
    return all_orders


def generate_activities(db, shops, activities_per_shop=5):
    """生成演示活动"""
    print(f"\n为每个店铺生成 {activities_per_shop} 个活动...")
    
    activity_names = [
        "新年大促", "春季特惠", "夏日狂欢", "秋季清仓", "双11促销",
        "黑五特卖", "会员专享", "限时抢购", "满减活动", "买一送一"
    ]
    
    all_activities = []
    
    for shop in shops:
        for i in range(activities_per_shop):
            # 随机选择活动类型
            activity_type = random.choice(list(ActivityType))
            
            # 活动时间：过去或未来
            is_past = random.choice([True, False])
            if is_past:
                start_time = datetime.now() - timedelta(days=random.randint(30, 180))
                duration = random.randint(3, 14)
            else:
                start_time = datetime.now() + timedelta(days=random.randint(1, 60))
                duration = random.randint(3, 14)
            
            end_time = start_time + timedelta(days=duration)
            
            activity = Activity(
                shop_id=shop.id,
                activity_id=f"ACT_{shop.id}_{i+1:03d}",
                activity_name=f"{activity_names[i % len(activity_names)]} - {shop.shop_name}",
                activity_type=activity_type,
                start_time=start_time,
                end_time=end_time,
                is_active=datetime.now() >= start_time and datetime.now() <= end_time,
                description=f"这是一个{activity_type.value}活动，持续{duration}天",
                created_at=start_time - timedelta(days=random.randint(1, 7))
            )
            db.add(activity)
            all_activities.append(activity)
    
    db.commit()
    print(f"✓ 已创建 {len(all_activities)} 个活动")
    return all_activities


def print_summary(shops, products, orders):
    """打印数据摘要"""
    print("\n" + "="*60)
    print("演示数据生成完成！")
    print("="*60)
    
    print(f"\n📊 数据统计:")
    print(f"  • 店铺数量: {len(shops)}")
    print(f"  • 商品数量: {len(products)}")
    print(f"  • 订单数量: {len(orders)}")
    
    total_gmv = sum(order.total_price for order in orders)
    total_profit = sum(order.profit for order in orders if order.profit)
    
    print(f"\n💰 财务数据:")
    print(f"  • 总GMV: ${total_gmv:,.2f}")
    print(f"  • 总利润: ${total_profit:,.2f}")
    print(f"  • 利润率: {(total_profit/total_gmv*100):.2f}%")
    
    print(f"\n🏪 店铺列表:")
    for shop in shops:
        shop_orders = [o for o in orders if o.shop_id == shop.id]
        shop_gmv = sum(o.total_price for o in shop_orders)
        print(f"  • {shop.shop_name}: {len(shop_orders)}个订单, GMV ${shop_gmv:,.2f}")
    
    print("\n✅ 现在可以访问系统查看演示数据了！")
    print("   前端: http://localhost:5173")
    print("   API文档: http://localhost:8000/docs")
    print("\n")


def main():
    """主函数"""
    print("="*60)
    print("Temu-Omni 演示数据生成器")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # 清除旧数据
        clear_demo_data(db)
        
        # 生成数据
        shops = generate_shops(db, count=3)
        products = generate_products(db, shops, products_per_shop=15)
        orders = generate_orders(db, shops, products, orders_per_shop=150)
        activities = generate_activities(db, shops, activities_per_shop=5)
        
        # 打印摘要
        print_summary(shops, products, orders)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()

