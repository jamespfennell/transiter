"""Add non-null source contraints

Revision ID: 8068ba0ab781
Revises: 4b61fb4aef27
Create Date: 2020-07-08 10:24:32.328201

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8068ba0ab781"
down_revision = "4b61fb4aef27"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("agency", "source_pk", existing_type=sa.INTEGER(), nullable=False)
    op.alter_column("alert", "source_pk", existing_type=sa.INTEGER(), nullable=False)
    op.alter_column(
        "direction_name_rule", "source_pk", existing_type=sa.INTEGER(), nullable=False
    )
    op.alter_column("route", "source_pk", existing_type=sa.INTEGER(), nullable=False)
    op.alter_column(
        "scheduled_service", "source_pk", existing_type=sa.INTEGER(), nullable=False
    )
    op.alter_column("stop", "source_pk", existing_type=sa.INTEGER(), nullable=False)
    op.alter_column("trip", "source_pk", existing_type=sa.INTEGER(), nullable=False)
    op.create_check_constraint(
        "transfer_source_constraint",
        "transfer",
        "NOT(source_pk IS NULL AND config_source_pk IS NULL)",
    )


def downgrade():
    pass
