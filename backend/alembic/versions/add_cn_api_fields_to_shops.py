"""add cn api fields to shops

Revision ID: add_cn_api_fields
Revises: add_spu_id_to_products
Create Date: 2024-11-20 20:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_cn_api_fields'
down_revision = 'add_spu_id'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 CN 区域 API 配置字段
    op.add_column('shops', sa.Column('cn_access_token', sa.Text(), nullable=True, comment='CN区域访问令牌'))
    op.add_column('shops', sa.Column('cn_app_key', sa.String(200), nullable=True, comment='CN区域App Key'))
    op.add_column('shops', sa.Column('cn_app_secret', sa.Text(), nullable=True, comment='CN区域App Secret'))
    op.add_column('shops', sa.Column('cn_api_base_url', sa.String(200), nullable=True, comment='CN区域API基础URL'))
    
    # 设置默认值
    op.execute("""
        UPDATE shops 
        SET cn_api_base_url = 'https://openapi.kuajingmaihuo.com/openapi/router',
            cn_app_key = 'af5bcf5d4bd5a492fa09c2ee302d75b9',
            cn_app_secret = 'e4f229bb9c4db21daa999e73c8683d42ba0a7094'
        WHERE cn_api_base_url IS NULL
    """)


def downgrade():
    # 删除 CN 区域 API 配置字段
    op.drop_column('shops', 'cn_api_base_url')
    op.drop_column('shops', 'cn_app_secret')
    op.drop_column('shops', 'cn_app_key')
    op.drop_column('shops', 'cn_access_token')

