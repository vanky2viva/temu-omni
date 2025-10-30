"""
初始化沙盒店铺
使用官方提供的测试凭据创建一个沙盒店铺
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.shop import Shop, ShopEnvironment, ShopRegion


def init_sandbox_shop():
    """初始化沙盒店铺"""
    db: Session = SessionLocal()
    
    try:
        # 测试凭据（来自官方文档）
        sandbox_credentials = {
            "shop_id": "635517726820718",  # Mall ID
            "shop_name": "Temu沙盒测试店铺（US）",
            "region": ShopRegion.US,
            "environment": ShopEnvironment.SANDBOX,
            "app_key": "4ebbc9190ae410443d65b4c2faca981f",
            "app_secret": "4782d2d827276688bf4758bed55dbdd4bbe79a79",
            "access_token": "uplv3hfyt5kcwoymrgnajnbl1ow5qxlz4sqhev6hl3xosz5dejrtyl2jre7",
            "api_base_url": "https://openapi-b-us.temu.com/openapi/router",
            "token_expires_at": datetime(2026, 10, 10),  # Token过期时间
            "is_active": True,
            "description": """
官方沙盒测试店铺
- 包含6,020个测试订单
- 包含3,015条售后记录
- 包含24个商品分类
- Token固定不变，有效期到2026-10-10
- 适合前端开发和功能测试
            """.strip()
        }
        
        # 检查是否已存在
        existing_shop = db.query(Shop).filter(
            Shop.shop_id == sandbox_credentials["shop_id"]
        ).first()
        
        if existing_shop:
            print(f"✅ 沙盒店铺已存在: {existing_shop.shop_name}")
            print(f"   ID: {existing_shop.id}")
            print(f"   环境: {existing_shop.environment.value}")
            print(f"   区域: {existing_shop.region.value}")
            
            # 更新凭据（以防有变化）
            for key, value in sandbox_credentials.items():
                if hasattr(existing_shop, key):
                    setattr(existing_shop, key, value)
            
            db.commit()
            print("   凭据已更新")
            
            return existing_shop
        
        # 创建新店铺
        shop = Shop(**sandbox_credentials)
        db.add(shop)
        db.commit()
        db.refresh(shop)
        
        print("🎉 沙盒店铺创建成功！")
        print(f"   ID: {shop.id}")
        print(f"   店铺名称: {shop.shop_name}")
        print(f"   Mall ID: {shop.shop_id}")
        print(f"   环境: {shop.environment.value}")
        print(f"   区域: {shop.region.value}")
        print(f"   Token过期: {shop.token_expires_at}")
        print("")
        print("📊 沙盒数据统计:")
        print("   - 6,020个订单")
        print("   - 3,015条售后记录")
        print("   - 24个商品分类")
        print("")
        print("🔧 下一步:")
        print("   1. 启动后端服务: uvicorn app.main:app --reload")
        print("   2. 访问同步端点: POST /api/sync/shops/{shop_id}/all")
        print("   3. 查看数据: GET /api/orders?shop_id={shop_id}")
        
        return shop
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建失败: {e}")
        raise
    finally:
        db.close()


def add_more_regions():
    """添加其他区域的沙盒店铺模板（可选）"""
    db: Session = SessionLocal()
    
    try:
        # 欧洲区域模板（待配置真实凭据）
        eu_shop = {
            "shop_id": "EU_MALL_ID_HERE",  # 待填写
            "shop_name": "Temu沙盒测试店铺（EU）",
            "region": ShopRegion.EU,
            "environment": ShopEnvironment.SANDBOX,
            "api_base_url": "https://openapi-b-eu.temu.com/openapi/router",
            "is_active": False,  # 默认禁用，等配置好凭据后启用
            "description": "欧洲区域沙盒店铺（待配置凭据）"
        }
        
        # 全球区域模板（待配置真实凭据）
        global_shop = {
            "shop_id": "GLOBAL_MALL_ID_HERE",  # 待填写
            "shop_name": "Temu沙盒测试店铺（Global）",
            "region": ShopRegion.GLOBAL,
            "environment": ShopEnvironment.SANDBOX,
            "api_base_url": "https://openapi-b-global.temu.com/openapi/router",
            "is_active": False,  # 默认禁用，等配置好凭据后启用
            "description": "全球区域沙盒店铺（待配置凭据）"
        }
        
        # 这里暂时不创建，只是提供模板
        print("\n📝 其他区域模板:")
        print("   - EU区域: 待配置凭据")
        print("   - Global区域: 待配置凭据")
        print("   - 可在店铺管理界面手动添加")
        
    finally:
        db.close()


if __name__ == "__main__":
    print("="*60)
    print("Temu沙盒店铺初始化")
    print("="*60)
    print("")
    
    shop = init_sandbox_shop()
    add_more_regions()
    
    print("")
    print("="*60)
    print("初始化完成！")
    print("="*60)

