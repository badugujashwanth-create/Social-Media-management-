"""oauth states

Revision ID: 0002_oauth_states
Revises: 0001_init
Create Date: 2026-02-20
"""

from alembic import op
import sqlalchemy as sa

revision = '0002_oauth_states'
down_revision = '0001_init'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'oauth_states',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('platform', sa.String(length=32), nullable=False),
        sa.Column('state', sa.String(length=255), nullable=False),
        sa.Column('code_verifier', sa.String(length=255)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_oauth_states_user_id', 'oauth_states', ['user_id'])
    op.create_index('ix_oauth_states_platform', 'oauth_states', ['platform'])
    op.create_index('ix_oauth_states_state', 'oauth_states', ['state'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_oauth_states_state', table_name='oauth_states')
    op.drop_index('ix_oauth_states_platform', table_name='oauth_states')
    op.drop_index('ix_oauth_states_user_id', table_name='oauth_states')
    op.drop_table('oauth_states')
