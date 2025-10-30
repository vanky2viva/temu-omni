"""add import history table

Revision ID: add_import_history
Revises: 
Create Date: 2025-10-31

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_import_history'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建导入历史记录表
    op.create_table(
        'import_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shop_id', sa.Integer(), nullable=False),
        sa.Column('import_type', sa.Enum('orders', 'products', 'activities', name='importtype'), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('total_rows', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('success_rows', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('failed_rows', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('skipped_rows', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('status', sa.Enum('processing', 'success', 'failed', 'partial', name='importstatus'), 
                  nullable=True, server_default='processing'),
        sa.Column('error_log', sa.Text(), nullable=True),
        sa.Column('success_log', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='导入历史记录表'
    )
    op.create_index(op.f('ix_import_history_id'), 'import_history', ['id'], unique=False)
    op.create_index('ix_import_history_shop_id', 'import_history', ['shop_id'], unique=False)


def downgrade():
    op.drop_index('ix_import_history_shop_id', table_name='import_history')
    op.drop_index(op.f('ix_import_history_id'), table_name='import_history')
    op.drop_table('import_history')
    op.execute('DROP TYPE importtype')
    op.execute('DROP TYPE importstatus')

