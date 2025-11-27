#!/usr/bin/env python3
"""
检查并修复店铺的API配置
用于解决商品同步错误 [7000016] type not exists
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.shop import Shop
from loguru import logger

def check_and_fix_shop_config():
    """检查并修复店铺配置"""
    db: Session = SessionLocal()
    
    try:
        shops = db.query(Shop).all()
        
        logger.info(f"找到 {len(shops)} 个店铺，开始检查配置...")
        
        for shop in shops:
            logger.info(f"\n{'='*60}")
            logger.info(f"店铺ID: {shop.id}")
            logger.info(f"店铺名称: {shop.shop_name}")
            logger.info(f"负责人: {shop.default_manager}")
            logger.info(f"地区: {shop.region}")
            
            # 检查CN配置
            has_cn_token = bool(shop.cn_access_token)
            has_cn_app_key = bool(shop.cn_app_key)
            has_cn_app_secret = bool(shop.cn_app_secret)
            cn_api_url = shop.cn_api_base_url or 'https://openapi.kuajingmaihuo.com/openapi/router'
            
            logger.info(f"\nCN区域配置:")
            logger.info(f"  - CN Access Token: {'✅ 已配置' if has_cn_token else '❌ 未配置'}")
            logger.info(f"  - CN App Key: {'✅ 已配置' if has_cn_app_key else '❌ 未配置'}")
            logger.info(f"  - CN App Secret: {'✅ 已配置' if has_cn_app_secret else '❌ 未配置'}")
            logger.info(f"  - CN API URL: {cn_api_url}")
            
            # 判断应该使用的API类型
            if 'openapi-b-partner' in cn_api_url:
                expected_api_type = "bg.glo.goods.list.get"
                logger.info(f"  - 检测到PARTNER区域，应使用: {expected_api_type}")
            else:
                expected_api_type = "bg.goods.list.get"
                logger.info(f"  - 检测到CN区域，应使用: {expected_api_type}")
            
            # 检查配置完整性
            if not has_cn_token:
                logger.warning(f"  ⚠️  店铺 {shop.shop_name} 未配置 CN Access Token，无法同步商品")
                continue
            
            if not has_cn_app_key or not has_cn_app_secret:
                logger.warning(f"  ⚠️  店铺 {shop.shop_name} CN配置不完整，无法同步商品")
                continue
            
            # 如果API URL不正确，提示修复
            if 'openapi-b-partner' in cn_api_url:
                logger.info(f"  ✅ API URL配置正确（PARTNER区域）")
            elif 'openapi.kuajingmaihuo.com' in cn_api_url:
                logger.info(f"  ✅ API URL配置正确（CN区域）")
            else:
                logger.warning(f"  ⚠️  API URL可能不正确: {cn_api_url}")
                logger.info(f"  建议配置为:")
                logger.info(f"    - PARTNER区域: https://openapi-b-partner.temu.com/openapi/router")
                logger.info(f"    - CN区域: https://openapi.kuajingmaihuo.com/openapi/router")
        
        logger.info(f"\n{'='*60}")
        logger.info("检查完成！")
        logger.info("\n如果发现配置问题，请:")
        logger.info("1. 检查店铺的 cn_api_base_url 是否正确")
        logger.info("2. 确认 cn_app_key、cn_app_secret、cn_access_token 都已配置")
        logger.info("3. 根据API端点选择正确的接口类型")
        
    except Exception as e:
        logger.error(f"检查失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    check_and_fix_shop_config()

