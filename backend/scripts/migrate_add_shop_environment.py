"""
数据库迁移：为Shop表添加环境和区域支持

新增字段：
- environment: 环境类型（sandbox/production）
- region: 区域（us/eu/global）
- api_base_url: API基础URL

运行方法：
  python scripts/migrate_add_shop_environment.py
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import inspect, text
from app.core.database import engine, SessionLocal
from app.models.shop import Shop, ShopEnvironment, ShopRegion


def check_column_exists(table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate():
    """执行迁移"""
    print("="*60)
    print("数据库迁移：Shop表环境和区域支持")
    print("="*60)
    print("")
    
    db = SessionLocal()
    
    try:
        # 检查并添加 environment 列
        if not check_column_exists('shops', 'environment'):
            print("📝 添加 environment 列...")
            db.execute(text(
                "ALTER TABLE shops ADD COLUMN environment VARCHAR(20) DEFAULT 'sandbox'"
            ))
            db.commit()
            print("   ✅ environment 列添加成功")
        else:
            print("   ℹ️  environment 列已存在")
        
        # 检查并添加 api_base_url 列
        if not check_column_exists('shops', 'api_base_url'):
            print("📝 添加 api_base_url 列...")
            db.execute(text(
                "ALTER TABLE shops ADD COLUMN api_base_url VARCHAR(200)"
            ))
            db.commit()
            print("   ✅ api_base_url 列添加成功")
        else:
            print("   ℹ️  api_base_url 列已存在")
        
        # 更新现有店铺的region类型（如果需要）
        print("📝 检查 region 列类型...")
        
        # 对于SQLite，region可能需要手动转换
        # 对于PostgreSQL/MySQL，可以使用ALTER COLUMN
        
        # 更新现有店铺的默认值
        print("📝 更新现有店铺的默认值...")
        shops = db.query(Shop).all()
        
        for shop in shops:
            updated = False
            
            # 设置默认环境
            if not hasattr(shop, 'environment') or not shop.environment:
                # 如果店铺ID包含DEMO，设置为sandbox
                if 'DEMO' in shop.shop_id:
                    shop.environment = ShopEnvironment.SANDBOX
                else:
                    shop.environment = ShopEnvironment.SANDBOX  # 默认沙盒
                updated = True
            
            # 设置默认API URL（基于区域）
            if not shop.api_base_url:
                region_urls = {
                    'us': 'https://openapi-b-us.temu.com/openapi/router',
                    'eu': 'https://openapi-b-eu.temu.com/openapi/router',
                    'global': 'https://openapi-b-global.temu.com/openapi/router',
                }
                
                # 获取region值
                region_value = shop.region.value if hasattr(shop.region, 'value') else shop.region
                shop.api_base_url = region_urls.get(region_value, region_urls['us'])
                updated = True
            
            if updated:
                print(f"   ✅ 更新店铺: {shop.shop_name}")
        
        db.commit()
        
        print("")
        print("="*60)
        print("✅ 迁移完成！")
        print("="*60)
        print("")
        print("📊 当前店铺列表:")
        
        shops = db.query(Shop).all()
        for shop in shops:
            env = shop.environment.value if hasattr(shop.environment, 'value') else shop.environment
            region = shop.region.value if hasattr(shop.region, 'value') else shop.region
            print(f"   - {shop.shop_name}")
            print(f"     环境: {env}, 区域: {region}")
            print(f"     API: {shop.api_base_url or 'Not set'}")
        
        print("")
        print("🔧 下一步:")
        print("   1. 运行: python scripts/init_sandbox_shop.py")
        print("   2. 启动后端: uvicorn app.main:app --reload")
        print("   3. 同步数据: POST /api/sync/shops/1/all")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 迁移失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()

