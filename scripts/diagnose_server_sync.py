#!/usr/bin/env python3
"""
服务器端同步问题诊断脚本
用于诊断同步进度无反应和订单列表为空的问题
"""

import os
import sys
import requests
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# 检查环境变量
BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def check_login():
    """检查登录"""
    print_section("1. 检查登录状态")
    try:
        login_url = f"{BASE_URL}/api/auth/login"
        response = requests.post(
            login_url,
            data={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            },
            timeout=10
        )
        if response.status_code == 200:
            token = response.json().get('access_token')
            print(f"✅ 登录成功，Token: {token[:20]}...")
            return token
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None

def check_shops(token):
    """检查店铺列表"""
    print_section("2. 检查店铺列表")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/shops/", headers=headers, timeout=10)
        if response.status_code == 200:
            shops = response.json()
            print(f"✅ 店铺数量: {len(shops)}")
            for shop in shops:
                print(f"  - {shop.get('shop_name')} (ID: {shop.get('id')}, 授权: {shop.get('has_api_config')})")
            return shops
        else:
            print(f"❌ 获取店铺失败: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ 获取店铺异常: {e}")
        return []

def check_orders(token):
    """检查订单列表"""
    print_section("3. 检查订单列表")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/orders/?skip=0&limit=10",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            items = data.get('items', [])
            print(f"✅ 订单总数: {total}")
            print(f"✅ 当前页订单数: {len(items)}")
            if items:
                print("前5条订单:")
                for order in items[:5]:
                    print(f"  - {order.get('order_sn')} ({order.get('shop_id')})")
            else:
                print("⚠️  订单列表为空")
            return total
        else:
            print(f"❌ 获取订单失败: {response.status_code} - {response.text}")
            return 0
    except Exception as e:
        print(f"❌ 获取订单异常: {e}")
        return 0

def check_sync_progress(token, shop_id):
    """检查同步进度"""
    print_section(f"4. 检查店铺 {shop_id} 的同步进度")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/sync/shops/{shop_id}/progress",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            progress = response.json()
            print(f"✅ 同步进度状态: {progress.get('status', 'unknown')}")
            print(f"✅ 进度: {progress.get('progress', 0)}%")
            print(f"✅ 当前步骤: {progress.get('current_step', 'N/A')}")
            if progress.get('error'):
                print(f"❌ 错误: {progress.get('error')}")
            return progress
        else:
            print(f"❌ 获取同步进度失败: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.Timeout:
        print(f"❌ 获取同步进度超时（可能API响应慢或卡住）")
        return None
    except Exception as e:
        print(f"❌ 获取同步进度异常: {e}")
        return None

def check_redis_connection():
    """检查Redis连接"""
    print_section("5. 检查Redis连接")
    try:
        import redis
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True, socket_timeout=5)
        client.ping()
        print(f"✅ Redis连接正常 ({redis_host}:{redis_port})")
        
        # 检查同步进度key
        keys = client.keys("sync_progress:*")
        print(f"✅ 同步进度Key数量: {len(keys)}")
        for key in keys[:5]:
            value = client.get(key)
            print(f"  - {key}: {value[:100] if value else 'None'}...")
        return True
    except ImportError:
        print("⚠️  Redis模块未安装")
        return False
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        print("   这将导致多worker环境下同步进度丢失")
        return False

def check_database_connection():
    """检查数据库连接"""
    print_section("6. 检查数据库连接")
    try:
        from app.core.database import SessionLocal
        from app.models.order import Order
        from app.models.shop import Shop
        
        db = SessionLocal()
        try:
            shop_count = db.query(Shop).count()
            order_count = db.query(Order).count()
            print(f"✅ 数据库连接正常")
            print(f"✅ 店铺数量: {shop_count}")
            print(f"✅ 订单数量: {order_count}")
            
            # 检查每个店铺的订单数
            if shop_count > 0:
                print("\n各店铺订单统计:")
                shops = db.query(Shop).all()
                for shop in shops:
                    shop_orders = db.query(Order).filter(Order.shop_id == shop.id).count()
                    print(f"  - {shop.shop_name} (ID: {shop.id}): {shop_orders} 个订单")
            
            return True
        finally:
            db.close()
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sync_start(token, shop_id):
    """测试启动同步"""
    print_section(f"7. 测试启动店铺 {shop_id} 的同步")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{BASE_URL}/api/sync/shops/{shop_id}/all?full_sync=false",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 同步任务已启动: {data.get('message')}")
            return True
        else:
            print(f"❌ 启动同步失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 启动同步异常: {e}")
        return False

def main():
    print_section("服务器端同步问题诊断工具")
    print(f"API地址: {BASE_URL}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 登录
    token = check_login()
    if not token:
        print("\n❌ 无法登录，请检查用户名密码和API地址")
        return
    
    # 2. 检查店铺
    shops = check_shops(token)
    if not shops:
        print("\n⚠️  没有店铺，请先添加店铺")
        return
    
    # 3. 检查订单
    order_count = check_orders(token)
    
    # 4. 检查Redis
    redis_ok = check_redis_connection()
    
    # 5. 检查数据库
    db_ok = check_database_connection()
    
    # 6. 检查第一个有授权的店铺的同步进度
    authorized_shops = [s for s in shops if s.get('has_api_config')]
    if authorized_shops:
        shop_id = authorized_shops[0].get('id')
        progress = check_sync_progress(token, shop_id)
        
        # 如果同步进度卡住，测试重新启动
        if progress and progress.get('status') == 'running':
            print("\n⚠️  检测到同步任务可能卡住（状态为running但没有更新）")
            print("   建议检查后端日志")
    
    # 7. 总结
    print_section("诊断总结")
    print(f"✅ 登录: 正常")
    print(f"{'✅' if shops else '❌'} 店铺: {len(shops)} 个")
    print(f"{'✅' if order_count > 0 else '⚠️ '} 订单: {order_count} 个")
    print(f"{'✅' if redis_ok else '⚠️ '} Redis: {'正常' if redis_ok else '连接失败（多worker环境可能有问题）'}")
    print(f"{'✅' if db_ok else '❌'} 数据库: {'正常' if db_ok else '连接失败'}")
    
    if order_count == 0:
        print("\n💡 建议:")
        print("  1. 确保店铺已配置Access Token")
        print("  2. 尝试手动触发同步")
        print("  3. 检查后端日志中的错误信息")
        print("  4. 检查代理服务器是否正常运行")
    
    if not redis_ok:
        print("\n💡 Redis问题建议:")
        print("  1. 确保Redis服务正在运行: docker ps | grep redis")
        print("  2. 检查Redis连接配置: docker-compose.yml")
        print("  3. 如果没有Redis，单worker环境仍可使用内存存储")

if __name__ == '__main__':
    main()

