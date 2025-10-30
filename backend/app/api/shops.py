"""店铺管理API"""
from typing import List, Optional
import time
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.shop import Shop, ShopRegion
from app.schemas.shop import ShopCreate, ShopUpdate, ShopResponse

router = APIRouter(prefix="/shops", tags=["shops"])


@router.get("/", response_model=List[ShopResponse])
def get_shops(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取店铺列表"""
    shops = db.query(Shop).offset(skip).limit(limit).all()
    # 添加API配置状态
    for shop in shops:
        shop.has_api_config = bool(shop.access_token)
    return shops


@router.get("/{shop_id}", response_model=ShopResponse)
def get_shop(shop_id: int, db: Session = Depends(get_db)):
    """获取店铺详情"""
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="店铺不存在"
        )
    shop.has_api_config = bool(shop.access_token)
    return shop


@router.post("/", response_model=ShopResponse, status_code=status.HTTP_201_CREATED)
def create_shop(shop: ShopCreate, db: Session = Depends(get_db)):
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
    
    data = shop.model_dump()
    data['region'] = ShopRegion(region_value)
    data['shop_id'] = shop_id_value

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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
    """更新店铺信息"""
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="店铺不存在"
        )
    
    update_data = shop_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(shop, field, value)
    
    db.commit()
    db.refresh(shop)
    return shop


@router.delete("/{shop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shop(shop_id: int, db: Session = Depends(get_db)):
    """删除店铺"""
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="店铺不存在"
        )
    
    db.delete(shop)
    db.commit()
    return None

