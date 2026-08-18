"""Add discovery_provider to jobs

Adds the discovery_provider column that was present in the SQLAlchemy ORM model
(app/models/job.py) but was never captured in a migration, causing every
SELECT/INSERT on the jobs table to fail with:

    asyncpg.exceptions.UndefinedColumnError:
    column jobs.discovery_provider does not exist

This migration is the smallest correct fix: add the nullable VARCHAR(50) column
and its btree index, matching the model definition exactly.

Revision ID: c2a1d8f3e047
Revises: b529badbe324
Create Date: 2026-08-18 17:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2a1d8f3e047'
down_revision: Union[str, None] = 'b529badbe324'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the missing column — nullable so existing rows need no backfill.
    op.add_column(
        'jobs',
        sa.Column(
            'discovery_provider',
            sa.String(length=50),
            nullable=True,
            comment="Discovery pipeline provider name (e.g. 'search_engine', 'lever', 'greenhouse', 'ashby')"
        )
    )
    # Create the btree index matching the model's index=True declaration.
    op.create_index(
        op.f('ix_jobs_discovery_provider'),
        'jobs',
        ['discovery_provider'],
        unique=False
    )


def downgrade() -> None:
    # Drop index before dropping column (PostgreSQL requires this ordering).
    op.drop_index(op.f('ix_jobs_discovery_provider'), table_name='jobs')
    op.drop_column('jobs', 'discovery_provider')
