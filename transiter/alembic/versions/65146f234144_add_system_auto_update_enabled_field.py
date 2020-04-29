"""
Add system auto update enabled field.

Revision ID: 65146f234144
Revises: b521e2a9055a
Create Date: 2020-03-23 21:57:11.720810

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "65146f234144"
down_revision = "b521e2a9055a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "system",
        sa.Column(
            "auto_update_enabled", sa.Boolean(), nullable=False, server_default="True"
        ),
    )

    # For consistency, change the column name on the feed table
    op.alter_column(
        "feed", "auto_update_on", new_column_name="auto_update_enabled", nullable=False
    )


def downgrade():
    pass
