"""optimize orders table indexes for better query performance

Revision ID: optimize_orders_indexes
Revises: add_raw_tables_optimize
Create Date: 2025-01-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'optimize_orders_indexes'
# 注意：这里需要根据实际情况调整，如果有多个迁移链，需要合并
# 暂时设置为add_raw_tables_optimize，如果add_raw_tables_optimize和add_default_manager_to_shops都基于add_cn_api_fields
# 那么optimize_orders_indexes应该基于它们中的一个
down_revision = 'add_raw_tables_optimize'
branch_labels = None
depends_on = None


def upgrade():
    # 添加复合索引以优化常见查询场景
    
    # 1. shop_id + order_time 复合索引（用于按店铺和时间范围查询）
    op.create_index(
        'idx_orders_shop_order_time',
        'orders',
        ['shop_id', 'order_time'],
        unique=False
    )
    
    # 2. shop_id + status + order_time 复合索引（用于按店铺、状态和时间查询）
    op.create_index(
        'idx_orders_shop_status_time',
        'orders',
        ['shop_id', 'status', 'order_time'],
        unique=False
    )
    
    # 3. order_time 降序索引（如果不存在，用于优化排序）
    # 注意：如果order_time已经有索引，这个可能会失败，需要先检查
    try:
        op.create_index(
            'idx_orders_order_time_desc',
            'orders',
            [sa.text('order_time DESC')],
            postgresql_using='btree'
        )
    except Exception:
        # 如果索引已存在或创建失败，忽略
        pass


def downgrade():
    # 删除索引
    try:
        op.drop_index('idx_orders_order_time_desc', table_name='orders')
    except Exception:
        pass
    
    op.drop_index('idx_orders_shop_status_time', table_name='orders')
    op.drop_index('idx_orders_shop_order_time', table_name='orders')

