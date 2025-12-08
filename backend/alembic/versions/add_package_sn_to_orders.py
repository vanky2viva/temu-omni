"""add package_sn to orders

Revision ID: add_package_sn_to_orders
Revises: add_raw_data_id_fields
Create Date: 2025-01-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'add_package_sn_to_orders'
down_revision = 'add_raw_data_id_fields'
branch_labels = None
depends_on = None


def upgrade():
    # 检查表是否已存在
    inspector = inspect(op.get_bind())
    existing_tables = inspector.get_table_names()
    
    # 为orders表添加package_sn字段（如果不存在）
    if 'orders' in existing_tables:
        orders_columns = [col['name'] for col in inspector.get_columns('orders')]
        if 'package_sn' not in orders_columns:
            op.add_column('orders', sa.Column('package_sn', sa.String(200), nullable=True, comment='包裹号'))
            try:
                op.create_index('ix_orders_package_sn', 'orders', ['package_sn'])
            except Exception:
                pass  # 索引可能已存在


def downgrade():
    # 删除orders表的package_sn字段
    try:
        op.drop_index('ix_orders_package_sn', table_name='orders')
    except Exception:
        pass
    try:
        op.drop_column('orders', 'package_sn')
    except Exception:
        pass
