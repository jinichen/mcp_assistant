"""add_file_model

Revision ID: a0b25f4e6721
Revises: 6a9e6178b087
Create Date: 2023-04-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a0b25f4e6721'
down_revision = '6a9e6178b087'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建文件表
    op.create_table(
        'files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=False),
        sa.Column('stored_filename', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('file_type', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 添加索引
    op.create_index(op.f('ix_files_id'), 'files', ['id'], unique=False)
    op.create_index(op.f('ix_files_original_filename'), 'files', ['original_filename'], unique=False)
    op.create_index(op.f('ix_files_stored_filename'), 'files', ['stored_filename'], unique=True)


def downgrade() -> None:
    # 删除索引
    op.drop_index(op.f('ix_files_stored_filename'), table_name='files')
    op.drop_index(op.f('ix_files_original_filename'), table_name='files')
    op.drop_index(op.f('ix_files_id'), table_name='files')
    
    # 删除文件表
    op.drop_table('files') 