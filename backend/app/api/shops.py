"""店铺管理API"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.shop import Shop
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
    from app.api.system import get_app_credentials
    
    # 检查shop_id是否已存在
    existing_shop = db.query(Shop).filter(Shop.shop_id == shop.shop_id).first()
    if existing_shop:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="店铺ID已存在"
        )
    
    # 获取应用凭证
    try:
        credentials = get_app_credentials(db)
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先在系统设置中配置Temu应用的App Key和App Secret"
        )
    
    # TODO: 验证access_token（需要调用Temu API）
    # 这里可以添加真实的token验证逻辑
    # 例如：尝试使用token获取店铺信息来验证token是否有效
    
    db_shop = Shop(**shop.model_dump())
    db.add(db_shop)
    db.commit()
    db.refresh(db_shop)
    db_shop.has_api_config = bool(db_shop.access_token)
    return db_shop


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

