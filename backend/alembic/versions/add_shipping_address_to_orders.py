"""add shipping_address to orders

Revision ID: add_shipping_address_to_orders
Revises: add_sync_fields_to_shops
Create Date: 2025-01-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'add_shipping_address_to_orders'
down_revision = 'add_sync_fields_to_shops'
branch_labels = None
depends_on = None


def upgrade():
    # 检查表是否已存在
    inspector = inspect(op.get_bind())
    existing_tables = inspector.get_table_names()
    
    # 为orders表添加shipping_address字段（如果不存在）
    if 'orders' in existing_tables:
        orders_columns = [col['name'] for col in inspector.get_columns('orders')]
        if 'shipping_address' not in orders_columns:
            op.add_column('orders', sa.Column('shipping_address', sa.Text(), nullable=True, comment='收货详细地址'))


def downgrade():
    # 删除orders表的shipping_address字段
    try:
        op.drop_column('orders', 'shipping_address')
    except Exception:
        pass

