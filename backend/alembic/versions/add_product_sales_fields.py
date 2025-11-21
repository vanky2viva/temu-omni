"""add product sales fields

Revision ID: add_product_sales_fields
Revises: 
Create Date: 2024-11-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_product_sales_fields'
down_revision = 'add_default_manager_to_shops'  # 基于add_default_manager_to_shops
branch_labels = None
depends_on = None


def upgrade():
    # 添加累计销量字段
    op.add_column('products', sa.Column('total_sales', sa.Integer(), nullable=True, comment='累计销量'))
    
    # 添加上架日期字段
    op.add_column('products', sa.Column('listed_at', sa.DateTime(), nullable=True, comment='上架日期'))
    
    # 为现有数据设置默认值（使用创建时间作为上架日期）
    op.execute("UPDATE products SET total_sales = 0 WHERE total_sales IS NULL")
    op.execute("UPDATE products SET listed_at = created_at WHERE listed_at IS NULL")


def downgrade():
    # 删除字段
    op.drop_column('products', 'total_sales')
    op.drop_column('products', 'listed_at')

