"""
Add a non-null constraint to trip_stop_time.

Revision ID: be93cf805bb4
Revises: 14fa42915420
Create Date: 2020-03-14 19:26:57.258062

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "be93cf805bb4"
down_revision = "14fa42915420"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "trip_stop_time",
        "future",
        existing_type=sa.BOOLEAN(),
        nullable=False,
        # The server default is just set for the migration to update existing
        # records and not fail on adding the constraint.
        server_default="True",
    )
    op.alter_column("trip_stop_time", "future", server_default=None)


def downgrade():
    pass
