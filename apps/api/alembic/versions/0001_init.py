"""init

Revision ID: 0001_init
Revises:
Create Date: 2026-02-13
"""

from alembic import op
import sqlalchemy as sa

revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table(
        'oauth_accounts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('platform', sa.String(length=32), nullable=False),
        sa.Column('display_name', sa.String(length=255)),
        sa.Column('external_account_id', sa.String(length=255), nullable=False),
        sa.Column('access_token_enc', sa.Text(), nullable=False),
        sa.Column('refresh_token_enc', sa.Text()),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('scopes', sa.String(length=1024)),
        sa.Column('meta_json', sa.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_oauth_accounts_user_id', 'oauth_accounts', ['user_id'])
    op.create_index('ix_oauth_accounts_platform', 'oauth_accounts', ['platform'])

    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('link_url', sa.String(length=2048)),
        sa.Column('media_url', sa.String(length=2048)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_posts_user_id', 'posts', ['user_id'])

    op.create_table(
        'post_targets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('oauth_account_id', sa.Integer(), sa.ForeignKey('oauth_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('platform', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='queued'),
        sa.Column('error_code', sa.String(length=128)),
        sa.Column('error_message', sa.Text()),
        sa.Column('external_post_id', sa.String(length=255)),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_post_targets_post_id', 'post_targets', ['post_id'])
    op.create_index('ix_post_targets_oauth_account_id', 'post_targets', ['oauth_account_id'])

    op.create_table(
        'follower_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('oauth_account_id', sa.Integer(), sa.ForeignKey('oauth_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('follower_count', sa.Integer(), nullable=False),
        sa.Column('snapshot_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_follower_snapshots_oauth_account_id', 'follower_snapshots', ['oauth_account_id'])

    op.create_table(
        'follower_deltas',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('oauth_account_id', sa.Integer(), sa.ForeignKey('oauth_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('snapshot_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('delta', sa.Integer(), nullable=False),
    )
    op.create_index('ix_follower_deltas_oauth_account_id', 'follower_deltas', ['oauth_account_id'])


def downgrade() -> None:
    op.drop_index('ix_follower_deltas_oauth_account_id', table_name='follower_deltas')
    op.drop_table('follower_deltas')
    op.drop_index('ix_follower_snapshots_oauth_account_id', table_name='follower_snapshots')
    op.drop_table('follower_snapshots')
    op.drop_index('ix_post_targets_oauth_account_id', table_name='post_targets')
    op.drop_index('ix_post_targets_post_id', table_name='post_targets')
    op.drop_table('post_targets')
    op.drop_index('ix_posts_user_id', table_name='posts')
    op.drop_table('posts')
    op.drop_index('ix_oauth_accounts_platform', table_name='oauth_accounts')
    op.drop_index('ix_oauth_accounts_user_id', table_name='oauth_accounts')
    op.drop_table('oauth_accounts')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
