"""Add some DB constraints

Revision ID: 123df9e95dda
Revises: 1e99b5efb76f
Create Date: 2020-06-02 11:53:42.233162

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "123df9e95dda"
down_revision = "1e99b5efb76f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(None, "direction_name_rule", ["source_pk", "id"])
    op.create_unique_constraint(None, "scheduled_service", ["system_pk", "id"])


def downgrade():
    pass
