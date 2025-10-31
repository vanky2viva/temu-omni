"""add skc_id and price_status to products

Revision ID: add_skc_price_status
Revises: add_import_history
Create Date: 2025-01-03

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_skc_price_status'
down_revision = 'add_import_history'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 skc_id 字段
    op.add_column('products', sa.Column('skc_id', sa.String(length=100), nullable=True, comment='SKC ID'))
    
    # 添加 price_status 字段
    op.add_column('products', sa.Column('price_status', sa.String(length=50), nullable=True, comment='申报价格状态'))


def downgrade():
    # 删除字段
    op.drop_column('products', 'price_status')
    op.drop_column('products', 'skc_id')

