"""Add transfers config table

Revision ID: 455692a5a808
Revises: 65551af9cd46
Create Date: 2020-06-08 10:19:11.374129

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "455692a5a808"
down_revision = "65551af9cd46"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("type", "transfer")
    op.create_table(
        "transfers_config",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("distance", sa.Numeric(), nullable=False),
        sa.PrimaryKeyConstraint("pk"),
    )
    op.create_table(
        "transfers_config_system",
        sa.Column("transfers_config_pk", sa.Integer(), nullable=True),
        sa.Column("system_pk", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["system_pk"], ["system.pk"],),
        sa.ForeignKeyConstraint(["transfers_config_pk"], ["transfers_config.pk"],),
    )
    op.create_index(
        op.f("ix_transfers_config_system_system_pk"),
        "transfers_config_system",
        ["system_pk"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transfers_config_system_transfers_config_pk"),
        "transfers_config_system",
        ["transfers_config_pk"],
        unique=False,
    )
    op.create_index(
        "idx_stop_system_pk_latitude", "stop", ["system_pk", "latitude"], unique=False
    )
    op.create_index(
        "idx_stop_system_pk_longitude", "stop", ["system_pk", "longitude"], unique=False
    )
    op.create_index(op.f("ix_stop_latitude"), "stop", ["latitude"], unique=False)
    op.create_index(op.f("ix_stop_longitude"), "stop", ["longitude"], unique=False)
    op.add_column(
        "transfer", sa.Column("config_source_pk", sa.Integer(), nullable=True)
    )
    op.add_column("transfer", sa.Column("distance", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_transfer_config_source_pk"),
        "transfer",
        ["config_source_pk"],
        unique=False,
    )
    op.create_foreign_key(
        None, "transfer", "transfers_config", ["config_source_pk"], ["pk"]
    )


def downgrade():
    pass
