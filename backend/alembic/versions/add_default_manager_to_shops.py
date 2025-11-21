"""add default_manager to shops

Revision ID: add_default_manager_to_shops
Revises: 
Create Date: 2025-10-30
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_default_manager_to_shops'
down_revision = 'add_cn_api_fields'  # 合并到主迁移链
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.add_column('shops', sa.Column('default_manager', sa.String(length=100), nullable=True, comment='默认负责人'))
    except Exception:
        # 列已存在则忽略
        pass


def downgrade():
    try:
        op.drop_column('shops', 'default_manager')
    except Exception:
        pass


