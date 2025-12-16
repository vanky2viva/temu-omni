"""add sync fields to shops table

Revision ID: add_sync_fields_to_shops
Revises: add_package_sn_to_orders
Create Date: 2025-01-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'add_sync_fields_to_shops'
down_revision = 'add_package_sn_to_orders'
branch_labels = None
depends_on = None


def upgrade():
    # 检查表是否已存在
    inspector = inspect(op.get_bind())
    existing_tables = inspector.get_table_names()
    
    # 为shops表添加同步相关字段（如果不存在）
    if 'shops' in existing_tables:
        shops_columns = [col['name'] for col in inspector.get_columns('shops')]
        
        # 订单同步字段
        if 'last_full_sync_at' not in shops_columns:
            try:
                op.add_column('shops', sa.Column('last_full_sync_at', sa.DateTime(), nullable=True, comment='最后订单全量同步时间'))
            except Exception:
                pass  # 字段可能已存在
        
        if 'sync_status' not in shops_columns:
            try:
                op.add_column('shops', sa.Column('sync_status', sa.String(20), nullable=True, server_default='idle', comment='订单同步状态：idle, syncing, error'))
            except Exception:
                pass  # 字段可能已存在
        
        # 商品同步字段
        if 'last_product_sync_at' not in shops_columns:
            try:
                op.add_column('shops', sa.Column('last_product_sync_at', sa.DateTime(), nullable=True, comment='最后商品同步时间'))
            except Exception:
                pass  # 字段可能已存在
        
        if 'last_product_full_sync_at' not in shops_columns:
            try:
                op.add_column('shops', sa.Column('last_product_full_sync_at', sa.DateTime(), nullable=True, comment='最后商品全量同步时间'))
            except Exception:
                pass  # 字段可能已存在
        
        if 'product_sync_status' not in shops_columns:
            try:
                op.add_column('shops', sa.Column('product_sync_status', sa.String(20), nullable=True, server_default='idle', comment='商品同步状态：idle, syncing, error'))
            except Exception:
                pass  # 字段可能已存在


def downgrade():
    # 删除shops表的同步相关字段
    try:
        op.drop_column('shops', 'product_sync_status')
    except Exception:
        pass
    
    try:
        op.drop_column('shops', 'last_product_full_sync_at')
    except Exception:
        pass
    
    try:
        op.drop_column('shops', 'last_product_sync_at')
    except Exception:
        pass
    
    try:
        op.drop_column('shops', 'sync_status')
    except Exception:
        pass
    
    try:
        op.drop_column('shops', 'last_full_sync_at')
    except Exception:
        pass

