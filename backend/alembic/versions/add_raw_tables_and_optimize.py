"""add raw tables and optimize business tables

Revision ID: add_raw_tables_optimize
Revises: add_product_sales_fields
Create Date: 2025-01-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_raw_tables_optimize'
down_revision = 'add_product_sales_fields'  # 基于add_product_sales_fields
branch_labels = None
depends_on = None


def upgrade():
    # 检查表是否已存在，如果存在则跳过创建
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # 1. 创建temu_orders_raw表（如果不存在）
    if 'temu_orders_raw' not in existing_tables:
        op.create_table(
            'temu_orders_raw',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('shop_id', sa.Integer(), nullable=False),
            sa.Column('external_order_id', sa.String(length=100), nullable=False),
            sa.Column('raw_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column('fetched_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('external_order_id'),
            comment='Temu订单原始数据表，完整存储API返回数据'
        )
        op.create_index('ix_temu_orders_raw_shop_id', 'temu_orders_raw', ['shop_id'])
        op.create_index('ix_temu_orders_raw_external_order_id', 'temu_orders_raw', ['external_order_id'])
        op.create_index('ix_temu_orders_raw_fetched_at', 'temu_orders_raw', ['fetched_at'])
        op.create_index('idx_temu_orders_raw_shop_fetched', 'temu_orders_raw', ['shop_id', 'fetched_at'])
    
    # 2. 创建temu_products_raw表（如果不存在）
    if 'temu_products_raw' not in existing_tables:
        op.create_table(
            'temu_products_raw',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('shop_id', sa.Integer(), nullable=False),
            sa.Column('external_product_id', sa.String(length=100), nullable=False),
            sa.Column('raw_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column('fetched_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('external_product_id'),
            comment='Temu商品原始数据表，完整存储API返回数据'
        )
        op.create_index('ix_temu_products_raw_shop_id', 'temu_products_raw', ['shop_id'])
        op.create_index('ix_temu_products_raw_external_product_id', 'temu_products_raw', ['external_product_id'])
        op.create_index('ix_temu_products_raw_fetched_at', 'temu_products_raw', ['fetched_at'])
        op.create_index('idx_temu_products_raw_shop_fetched', 'temu_products_raw', ['shop_id', 'fetched_at'])
    
    # 3. 创建order_items表（如果不存在）
    if 'order_items' not in existing_tables:
        op.create_table(
            'order_items',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('sku_id', sa.String(length=200), nullable=True),
            sa.Column('product_name', sa.String(length=500), nullable=True),
            sa.Column('product_sku', sa.String(length=200), nullable=True),
            sa.Column('spu_id', sa.String(length=100), nullable=True),
            sa.Column('quantity', sa.Integer(), nullable=False),
            sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('total_price', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('currency', sa.String(length=10), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_order_items_order_id', 'order_items', ['order_id'])
        op.create_index('ix_order_items_sku_id', 'order_items', ['sku_id'])
        op.create_index('ix_order_items_product_sku', 'order_items', ['product_sku'])
        op.create_index('ix_order_items_spu_id', 'order_items', ['spu_id'])
    
    # 4. 创建payouts表（如果不存在）
    if 'payouts' not in existing_tables:
        op.create_table(
            'payouts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('shop_id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('external_payout_id', sa.String(length=100), nullable=True),
            sa.Column('payout_date', sa.Date(), nullable=False),
            sa.Column('payout_amount', sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column('currency', sa.String(length=10), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('raw_data_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['raw_data_id'], ['temu_orders_raw.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            comment='回款计划表，基于订单签收时间计算回款日期'
        )
        op.create_index('ix_payouts_shop_id', 'payouts', ['shop_id'])
        op.create_index('ix_payouts_order_id', 'payouts', ['order_id'])
        op.create_index('ix_payouts_payout_date', 'payouts', ['payout_date'])
        op.create_index('ix_payouts_status', 'payouts', ['status'])
        op.create_index('idx_payouts_shop_date', 'payouts', ['shop_id', 'payout_date'])
    
    # 5. 创建report_snapshots表（如果不存在）
    if 'report_snapshots' not in existing_tables:
        op.create_table(
            'report_snapshots',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('shop_id', sa.Integer(), nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('type', sa.String(length=20), nullable=False),
            sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column('ai_summary', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('shop_id', 'date', 'type', name='uq_report_shop_date_type'),
            comment='报表快照表，存储每日/每周运营报表'
        )
        op.create_index('ix_report_snapshots_shop_id', 'report_snapshots', ['shop_id'])
        op.create_index('ix_report_snapshots_date', 'report_snapshots', ['date'])
        op.create_index('idx_report_snapshots_shop_date', 'report_snapshots', ['shop_id', 'date'])
    
    # 6. 为orders表添加raw_data_id字段（如果不存在）
    inspector = inspect(op.get_bind())
    orders_columns = [col['name'] for col in inspector.get_columns('orders')]
    if 'raw_data_id' not in orders_columns:
        op.add_column('orders', sa.Column('raw_data_id', sa.Integer(), nullable=True, comment='关联原始数据表ID'))
        try:
            op.create_foreign_key('fk_orders_raw_data_id', 'orders', 'temu_orders_raw', ['raw_data_id'], ['id'], ondelete='SET NULL')
        except Exception:
            pass  # 外键可能已存在
        try:
            op.create_index('ix_orders_raw_data_id', 'orders', ['raw_data_id'])
        except Exception:
            pass  # 索引可能已存在
    
    # 7. 为products表添加raw_data_id字段（如果不存在）
    products_columns = [col['name'] for col in inspector.get_columns('products')]
    if 'raw_data_id' not in products_columns:
        op.add_column('products', sa.Column('raw_data_id', sa.Integer(), nullable=True, comment='关联原始数据表ID'))
        try:
            op.create_foreign_key('fk_products_raw_data_id', 'products', 'temu_products_raw', ['raw_data_id'], ['id'], ondelete='SET NULL')
        except Exception:
            pass  # 外键可能已存在
        try:
            op.create_index('ix_products_raw_data_id', 'products', ['raw_data_id'])
        except Exception:
            pass  # 索引可能已存在


def downgrade():
    # 删除orders表的raw_data_id字段
    op.drop_index('ix_orders_raw_data_id', table_name='orders')
    op.drop_constraint('fk_orders_raw_data_id', 'orders', type_='foreignkey')
    op.drop_column('orders', 'raw_data_id')
    
    # 删除products表的raw_data_id字段
    op.drop_index('ix_products_raw_data_id', table_name='products')
    op.drop_constraint('fk_products_raw_data_id', 'products', type_='foreignkey')
    op.drop_column('products', 'raw_data_id')
    
    # 删除report_snapshots表
    op.drop_index('idx_report_snapshots_shop_date', table_name='report_snapshots')
    op.drop_index('ix_report_snapshots_date', table_name='report_snapshots')
    op.drop_index('ix_report_snapshots_shop_id', table_name='report_snapshots')
    op.drop_table('report_snapshots')
    
    # 删除payouts表
    op.drop_index('idx_payouts_shop_date', table_name='payouts')
    op.drop_index('ix_payouts_status', table_name='payouts')
    op.drop_index('ix_payouts_payout_date', table_name='payouts')
    op.drop_index('ix_payouts_order_id', table_name='payouts')
    op.drop_index('ix_payouts_shop_id', table_name='payouts')
    op.drop_table('payouts')
    
    # 删除order_items表
    op.drop_index('ix_order_items_spu_id', table_name='order_items')
    op.drop_index('ix_order_items_product_sku', table_name='order_items')
    op.drop_index('ix_order_items_sku_id', table_name='order_items')
    op.drop_index('ix_order_items_order_id', table_name='order_items')
    op.drop_table('order_items')
    
    # 删除temu_products_raw表
    op.drop_index('idx_temu_products_raw_shop_fetched', table_name='temu_products_raw')
    op.drop_index('ix_temu_products_raw_fetched_at', table_name='temu_products_raw')
    op.drop_index('ix_temu_products_raw_external_product_id', table_name='temu_products_raw')
    op.drop_index('ix_temu_products_raw_shop_id', table_name='temu_products_raw')
    op.drop_table('temu_products_raw')
    
    # 删除temu_orders_raw表
    op.drop_index('idx_temu_orders_raw_shop_fetched', table_name='temu_orders_raw')
    op.drop_index('ix_temu_orders_raw_fetched_at', table_name='temu_orders_raw')
    op.drop_index('ix_temu_orders_raw_external_order_id', table_name='temu_orders_raw')
    op.drop_index('ix_temu_orders_raw_shop_id', table_name='temu_orders_raw')
    op.drop_table('temu_orders_raw')

