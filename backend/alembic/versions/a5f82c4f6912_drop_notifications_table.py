"""drop_notifications_table

Revision ID: a5f82c4f6912
Revises: 3fca5c006215
Create Date: 2026-07-28 14:44:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a5f82c4f6912'
down_revision: Union[str, None] = '3fca5c006215'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('notifications')


def downgrade() -> None:
    op.create_table('notifications',
    sa.Column('id', sa.UUID(), nullable=False, comment='Unique notification identifier'),
    sa.Column('user_id', sa.UUID(), nullable=False, comment='ID of candidate user recipient'),
    sa.Column('job_id', sa.UUID(), nullable=True, comment='Associated job posting ID (if applicable)'),
    sa.Column('type', sa.String(length=50), nullable=False, comment="Notification category: 'high_match_job', 'saved_search_alert', 'application_update'"),
    sa.Column('title', sa.String(length=255), nullable=False, comment='Notification title header'),
    sa.Column('message', sa.Text(), nullable=False, comment='Notification body text description'),
    sa.Column('read', sa.Boolean(), nullable=False, comment='Whether candidate has marked notification as read'),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, comment='Timestamp when notification was created'),
    sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notifications_read', 'notifications', ['read'], unique=False)
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'], unique=False)
    op.create_index('ix_notifications_job_id', 'notifications', ['job_id'], unique=False)
