"""add spu_id to products

Revision ID: add_spu_id
Revises: add_skc_price_status
Create Date: 2025-10-31

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_spu_id'
down_revision = 'add_skc_price_status'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 spu_id 字段
    op.add_column('products', sa.Column('spu_id', sa.String(length=100), nullable=True, comment='SPU ID'))
    
    # 创建索引以优化查询
    op.create_index('ix_products_spu_id', 'products', ['spu_id'])


def downgrade():
    # 删除索引
    op.drop_index('ix_products_spu_id', table_name='products')
    
    # 删除字段
    op.drop_column('products', 'spu_id')

