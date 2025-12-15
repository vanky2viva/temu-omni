"""add order_detail_tasks table

Revision ID: add_order_detail_tasks_table
Revises: add_sync_fields_to_shops
Create Date: 2025-01-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_order_detail_tasks_table'
down_revision = 'add_sync_fields_to_shops'
branch_labels = None
depends_on = None


def upgrade():
    # 检查表是否已存在
    from sqlalchemy import inspect
    inspector = inspect(op.get_bind())
    existing_tables = inspector.get_table_names()
    
    # 创建订单详情补齐任务表（如果不存在）
    if 'order_detail_tasks' not in existing_tables:
        op.create_table(
            'order_detail_tasks',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('shop_id', sa.Integer(), nullable=False, comment='店铺ID'),
            sa.Column('parent_order_sn', sa.String(100), nullable=False, comment='父订单号'),
            sa.Column('order_ids', postgresql.ARRAY(sa.Integer()), nullable=False, comment='该父订单下的所有子订单ID列表'),
            sa.Column('status', sa.String(20), nullable=False, server_default='pending', comment='任务状态'),
            sa.Column('package_sn', sa.String(200), nullable=True, comment='获取到的包裹号'),
            sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
            sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0', comment='重试次数'),
            sa.Column('max_retries', sa.Integer(), nullable=False, server_default='5', comment='最大重试次数'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='创建时间'),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新时间'),
            sa.Column('completed_at', sa.DateTime(), nullable=True, comment='完成时间'),
            sa.PrimaryKeyConstraint('id')
        )
    
    # 检查并创建索引（如果不存在）
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('order_detail_tasks')] if 'order_detail_tasks' in existing_tables else []
    
    if 'ix_order_detail_tasks_shop_id' not in existing_indexes:
        try:
            op.create_index('ix_order_detail_tasks_shop_id', 'order_detail_tasks', ['shop_id'])
        except Exception:
            pass
    
    if 'ix_order_detail_tasks_parent_order_sn' not in existing_indexes:
        try:
            op.create_index('ix_order_detail_tasks_parent_order_sn', 'order_detail_tasks', ['parent_order_sn'])
        except Exception:
            pass
    
    if 'ix_order_detail_tasks_status' not in existing_indexes:
        try:
            op.create_index('ix_order_detail_tasks_status', 'order_detail_tasks', ['status'])
        except Exception:
            pass
    
    if 'ix_order_detail_tasks_created_at' not in existing_indexes:
        try:
            op.create_index('ix_order_detail_tasks_created_at', 'order_detail_tasks', ['created_at'])
        except Exception:
            pass
    
    if 'idx_order_detail_tasks_shop_status' not in existing_indexes:
        try:
            op.create_index('idx_order_detail_tasks_shop_status', 'order_detail_tasks', ['shop_id', 'status'])
        except Exception:
            pass
    
    if 'idx_order_detail_tasks_status_created' not in existing_indexes:
        try:
            op.create_index('idx_order_detail_tasks_status_created', 'order_detail_tasks', ['status', 'created_at'])
        except Exception:
            pass


def downgrade():
    # 删除索引
    try:
        op.drop_index('idx_order_detail_tasks_status_created', table_name='order_detail_tasks')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_order_detail_tasks_shop_status', table_name='order_detail_tasks')
    except Exception:
        pass
    
    try:
        op.drop_index('ix_order_detail_tasks_created_at', table_name='order_detail_tasks')
    except Exception:
        pass
    
    try:
        op.drop_index('ix_order_detail_tasks_status', table_name='order_detail_tasks')
    except Exception:
        pass
    
    try:
        op.drop_index('ix_order_detail_tasks_parent_order_sn', table_name='order_detail_tasks')
    except Exception:
        pass
    
    try:
        op.drop_index('ix_order_detail_tasks_shop_id', table_name='order_detail_tasks')
    except Exception:
        pass
    
    # 删除表
    op.drop_table('order_detail_tasks')
