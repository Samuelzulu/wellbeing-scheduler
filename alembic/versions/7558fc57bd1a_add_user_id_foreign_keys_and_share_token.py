"""add user_id foreign keys and share token

Revision ID: 7558fc57bd1a
Revises: 96e188c70d73
Create Date: 2026-05-04

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '7558fc57bd1a'
down_revision: Union[str, None] = '96e188c70d73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))

    with op.batch_alter_table('plans', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('share_token', sa.String(), nullable=True))
        batch_op.create_index('ix_plans_share_token', ['share_token'], unique=True)

    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_column('user_id')

    with op.batch_alter_table('plans', schema=None) as batch_op:
        batch_op.drop_index('ix_plans_share_token')
        batch_op.drop_column('share_token')
        batch_op.drop_column('user_id')

    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_column('user_id')
