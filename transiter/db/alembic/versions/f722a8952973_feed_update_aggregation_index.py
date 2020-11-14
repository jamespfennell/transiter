"""Feed update aggregation index

Revision ID: f722a8952973
Revises: 8068ba0ab781
Create Date: 2020-11-13 19:11:35.351171

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f722a8952973"
down_revision = "8068ba0ab781"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "feed_update_status_result_completed_at_idx",
        "feed_update",
        ["feed_pk", "status", "result", "completed_at"],
        unique=False,
    )


def downgrade():
    pass
