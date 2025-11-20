"""店铺管理API"""
from typing import List, Optional
import time
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.shop import Shop, ShopRegion
from app.models.user import User
from app.schemas.shop import ShopCreate, ShopUpdate, ShopResponse, ShopDetailResponse

router = APIRouter(prefix="/shops", tags=["shops"])


@router.get("/", response_model=List[ShopResponse])
def get_shops(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取店铺列表（不返回敏感字段）"""
    try:
    shops = db.query(Shop).offset(skip).limit(limit).all()
    # 添加API配置状态
        result = []
    for shop in shops:
        shop.has_api_config = bool(shop.access_token)
            # 创建响应对象，排除敏感字段（列表接口不返回 access_token 和 cn_access_token）
            shop_response = ShopResponse.model_validate(shop)
            # 清除敏感字段
            shop_response.access_token = None
            shop_response.cn_access_token = None
            result.append(shop_response)
        return result
    except Exception as e:
        from loguru import logger
        logger.error(f"获取店铺列表失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取店铺列表失败: {str(e)}"
        )


@router.get("/{shop_id}", response_model=ShopDetailResponse)
def get_shop(shop_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取店铺详情（包含敏感字段，用于编辑）"""
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="店铺不存在"
        )
    shop.has_api_config = bool(shop.access_token)
    # 返回包含敏感字段的完整信息
    return shop


@router.post("/", response_model=ShopResponse, status_code=status.HTTP_201_CREATED)
def create_shop(shop: ShopCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """创建店铺"""
    # 允许未配置应用凭证也可创建店铺；仅在授权/同步时需要
    # 如果提交了shop_id则校验唯一；否则生成占位ID
    if shop.shop_id:
        existing_shop = db.query(Shop).filter(Shop.shop_id == shop.shop_id).first()
        if existing_shop:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="店铺ID已存在"
            )
        shop_id_value = shop.shop_id
    else:
        shop_id_value = f"PENDING_{int(time.time())}"
    
    # 规范化并校验 region
    region_value = (shop.region or '').strip().lower()
    if region_value not in [r.value for r in ShopRegion]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="地区(region)无效，可选值: us / eu / global"
        )
    
    # 根据区域设置 API 基础 URL
    region_urls = {
        'us': 'https://openapi-b-us.temu.com/openapi/router',
        'eu': 'https://openapi-b-eu.temu.com/openapi/router',
        'global': 'https://openapi-b-global.temu.com/openapi/router',
    }
    api_base_url = region_urls.get(region_value, region_urls['us'])
    
    data = shop.model_dump()
    data['region'] = ShopRegion(region_value)
    data['shop_id'] = shop_id_value
    data['api_base_url'] = api_base_url
    
    # 设置 CN API 默认值（如果用户没有填写）
    # 重要：CN 区域的 app_key、secret、access_token 和接口地址必须都来自 CN 区域
    if not data.get('cn_api_base_url'):
        data['cn_api_base_url'] = 'https://openapi.kuajingmaihuo.com/openapi/router'
    # CN App Key和Secret从环境变量读取，不硬编码
    from app.core.config import settings
    if not data.get('cn_app_key'):
        data['cn_app_key'] = settings.TEMU_CN_APP_KEY or ''
    if not data.get('cn_app_secret'):
        data['cn_app_secret'] = settings.TEMU_CN_APP_SECRET or ''
    
    # 验证：如果填写了 cn_access_token，建议同时填写 cn_app_key 和 cn_app_secret
    # 但为了兼容性，如果没有填写，会使用默认值

    db_shop = Shop(**data)
    db.add(db_shop)
    db.commit()
    db.refresh(db_shop)
    db_shop.has_api_config = bool(db_shop.access_token)
    return db_shop


class AuthorizeRequest(BaseModel):
    """授权请求体"""
    access_token: str
    shop_id: Optional[str] = None


@router.post("/{shop_id}/authorize", response_model=ShopResponse)
def authorize_shop(
    shop_id: int,
    body: AuthorizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为店铺配置/更新 Access Token 并进行基本校验"""
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="店铺不存在")

    token = (body.access_token or "").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Access Token 不能为空")

    # 保存 Token（如需可在此加入实际的Temu API验证）
    shop.access_token = token
    
    # 根据区域设置 API 基础 URL（如果还没有设置）
    if not shop.api_base_url:
        region_urls = {
            ShopRegion.US: 'https://openapi-b-us.temu.com/openapi/router',
            ShopRegion.EU: 'https://openapi-b-eu.temu.com/openapi/router',
            ShopRegion.GLOBAL: 'https://openapi-b-global.temu.com/openapi/router',
        }
        shop.api_base_url = region_urls.get(shop.region, region_urls[ShopRegion.US])
    
    # 如传入shop_id则同时更新（并校验唯一）
    if body.shop_id:
        new_shop_id = body.shop_id.strip()
        if not new_shop_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="店铺ID不能为空")
        exists = db.query(Shop).filter(Shop.shop_id == new_shop_id, Shop.id != shop.id).first()
        if exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="店铺ID已存在")
        shop.shop_id = new_shop_id

    db.commit()
    db.refresh(shop)

    shop.has_api_config = True
    return shop


@router.put("/{shop_id}", response_model=ShopResponse)
def update_shop(
    shop_id: int,
    shop_update: ShopUpdate,
    sync_to_products: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新店铺信息
    
    Args:
        shop_id: 店铺ID
        shop_update: 更新数据
        sync_to_products: 是否同步默认负责人到该店铺的所有商品
    """
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="店铺不存在"
        )
    
    update_data = shop_update.model_dump(exclude_unset=True)
    
    # 检查是否更新了 default_manager
    default_manager_changed = 'default_manager' in update_data
    new_manager = update_data.get('default_manager') if default_manager_changed else None
    
    for field, value in update_data.items():
        setattr(shop, field, value)
    
    db.commit()
    
    # 如果需要同步负责人到商品
    if sync_to_products and default_manager_changed and new_manager:
        from app.models.product import Product
        # 更新该店铺下所有没有负责人的商品
        db.query(Product).filter(
            Product.shop_id == shop_id,
            (Product.manager == None) | (Product.manager == '')
        ).update({Product.manager: new_manager})
        db.commit()
    
    db.refresh(shop)
    return shop


@router.post("/{shop_id}/sync-manager")
def sync_manager_to_products(
    shop_id: int,
    update_all: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    同步店铺负责人到商品
    
    Args:
        shop_id: 店铺ID
        update_all: True=更新所有商品，False=只更新没有负责人的商品
    """
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="店铺不存在"
        )
    
    if not shop.default_manager:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="店铺未设置默认负责人"
        )
    
    from app.models.product import Product
    
    if update_all:
        # 更新该店铺下的所有商品
        result = db.query(Product).filter(
            Product.shop_id == shop_id
        ).update({Product.manager: shop.default_manager})
    else:
        # 只更新没有负责人的商品
        result = db.query(Product).filter(
            Product.shop_id == shop_id,
            (Product.manager == None) | (Product.manager == '')
        ).update({Product.manager: shop.default_manager})
    
    db.commit()
    
    return {
        "success": True,
        "message": f"已更新 {result} 个商品的负责人",
        "updated_count": result,
        "manager": shop.default_manager
    }


@router.delete("/{shop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shop(shop_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除店铺（会级联删除相关的订单和商品）"""
    try:
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="店铺不存在"
            )
        
        # 删除店铺（会级联删除关联的订单和商品，因为外键设置了 ondelete="CASCADE"）
        db.delete(shop)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除店铺失败: {str(e)}"
        )

