"""add raw_data_id to orders and products

Revision ID: add_raw_data_id_fields
Revises: optimize_orders_indexes
Create Date: 2025-01-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'add_raw_data_id_fields'
down_revision = 'optimize_orders_indexes'
branch_labels = None
depends_on = None


def upgrade():
    # 检查表是否已存在
    inspector = inspect(op.get_bind())
    existing_tables = inspector.get_table_names()
    
    # 1. 为orders表添加raw_data_id字段（如果不存在）
    if 'orders' in existing_tables:
        orders_columns = [col['name'] for col in inspector.get_columns('orders')]
        if 'raw_data_id' not in orders_columns:
            op.add_column('orders', sa.Column('raw_data_id', sa.Integer(), nullable=True, comment='关联原始数据表ID'))
            try:
                op.create_foreign_key('fk_orders_raw_data_id', 'orders', 'temu_orders_raw', ['raw_data_id'], ['id'], ondelete='SET NULL')
            except Exception:
                pass  # 外键可能已存在
            try:
                op.create_index('ix_orders_raw_data_id', 'orders', ['raw_data_id'])
            except Exception:
                pass  # 索引可能已存在
    
    # 2. 为products表添加raw_data_id字段（如果不存在）
    if 'products' in existing_tables:
        products_columns = [col['name'] for col in inspector.get_columns('products')]
        if 'raw_data_id' not in products_columns:
            op.add_column('products', sa.Column('raw_data_id', sa.Integer(), nullable=True, comment='关联原始数据表ID'))
            try:
                op.create_foreign_key('fk_products_raw_data_id', 'products', 'temu_products_raw', ['raw_data_id'], ['id'], ondelete='SET NULL')
            except Exception:
                pass  # 外键可能已存在
            try:
                op.create_index('ix_products_raw_data_id', 'products', ['raw_data_id'])
            except Exception:
                pass  # 索引可能已存在


def downgrade():
    # 删除orders表的raw_data_id字段
    try:
        op.drop_index('ix_orders_raw_data_id', table_name='orders')
    except Exception:
        pass
    try:
        op.drop_constraint('fk_orders_raw_data_id', 'orders', type_='foreignkey')
    except Exception:
        pass
    try:
        op.drop_column('orders', 'raw_data_id')
    except Exception:
        pass
    
    # 删除products表的raw_data_id字段
    try:
        op.drop_index('ix_products_raw_data_id', table_name='products')
    except Exception:
        pass
    try:
        op.drop_constraint('fk_products_raw_data_id', 'products', type_='foreignkey')
    except Exception:
        pass
    try:
        op.drop_column('products', 'raw_data_id')
    except Exception:
        pass

