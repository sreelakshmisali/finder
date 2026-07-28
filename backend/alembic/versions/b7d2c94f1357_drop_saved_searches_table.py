"""drop_saved_searches_table

Revision ID: b7d2c94f1357
Revises: a5f82c4f6912
Create Date: 2026-07-28 15:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b7d2c94f1357'
down_revision: Union[str, None] = 'a5f82c4f6912'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('saved_searches')


def downgrade() -> None:
    op.create_table('saved_searches',
    sa.Column('id', sa.UUID(), nullable=False, comment='Unique identifier for saved search entry'),
    sa.Column('user_id', sa.UUID(), nullable=False, comment='ID of owning user account'),
    sa.Column('name', sa.String(length=150), nullable=False, comment="Human-readable title for the search rule (e.g. 'Python Remote Jobs')"),
    sa.Column('query', sa.String(length=255), nullable=True, comment="Keyword search string (e.g. 'Python Backend')"),
    sa.Column('filters', sa.JSON(), nullable=False, comment='Filter rules dictionary (location, remote_only, sources, min_salary, etc.)'),
    sa.Column('mode', sa.String(length=20), nullable=False, comment='Search mode used for this saved search (NORMAL or SMART)'),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, comment='Timestamp when search rule was saved'),
    sa.Column('last_run', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when search rule was last executed'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_saved_searches_user_id', 'saved_searches', ['user_id'], unique=False)
