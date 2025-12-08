"""添加实时计算所需的索引

Revision ID: add_realtime_calc_indexes
Revises: 
Create Date: 2025-11-22 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_realtime_calc_indexes'
down_revision = None  # 需要根据实际情况设置
branch_labels = None
depends_on = None


def upgrade():
    # 为订单表添加索引，优化实时计算查询
    op.create_index(
        'idx_orders_product_time',
        'orders',
        ['product_id', 'order_time'],
        unique=False
    )
    
    # 为商品成本表添加索引，优化成本查询
    op.create_index(
        'idx_product_costs_product_effective',
        'product_costs',
        ['product_id', 'effective_from', 'effective_to'],
        unique=False
    )
    
    # 为商品表添加索引（如果还没有）
    # op.create_index(
    #     'idx_products_id_created',
    #     'products',
    #     ['id', 'created_at'],
    #     unique=False
    # )


def downgrade():
    op.drop_index('idx_orders_product_time', table_name='orders')
    op.drop_index('idx_product_costs_product_effective', table_name='product_costs')
    # op.drop_index('idx_products_id_created', table_name='products')












