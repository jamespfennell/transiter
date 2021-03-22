"""Add system update table

Revision ID: 055583d82811
Revises: 65146f234144
Create Date: 2020-03-24 11:14:28.985576

"""
import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "055583d82811"
down_revision = "65146f234144"
branch_labels = None
depends_on = None


def upgrade():
    # (1) Create the new table
    table = op.create_table(
        "system_update",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("system_pk", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "SCHEDULED",
                "IN_PROGRESS",
                "SUCCESS",
                "FAILED",
                name="status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("status_message", sa.String(), nullable=True),
        sa.Column("total_duration", sa.Float(), nullable=True),
        sa.Column("scheduled_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("config", sa.String(), nullable=True),
        sa.Column("config_template", sa.String(), nullable=True),
        sa.Column("config_parameters", sa.String(), nullable=True),
        sa.Column("config_source_url", sa.String(), nullable=True),
        sa.Column("transiter_version", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["system_pk"], ["system.pk"]),
        sa.PrimaryKeyConstraint("pk"),
    )
    op.create_index(
        "system_update_system_pk_system_update_pk_idx",
        "system_update",
        ["system_pk", "pk"],
        unique=False,
    )

    # (2) Migrate some of the data from the system table over
    statement = sa.sql.select(
        *[sa.text("system.pk"), sa.text("system.raw_config"), sa.text("system.status")]
    ).select_from(sa.text("system"))
    data_dicts = []
    for system_pk, raw_config, system_status in op.get_bind().execute(statement):
        if system_status == "ACTIVE":
            status = "SUCCESS"
        else:
            status = "FAILED"
        data_dicts.append(
            {
                "system_pk": system_pk,
                "config_template": raw_config,
                "status": status,
                "status_message": "update data added as part of migration 0555",
                "scheduled_at": datetime.datetime.utcnow(),
                "completed_at": datetime.datetime.utcnow(),
                "transiter_version": "0.4.1",
            }
        )
    op.bulk_insert(table, data_dicts)

    # (3) Drop the old columns in the system table
    op.drop_column("system", "error_message")
    op.drop_column("system", "raw_config")

    # (4) Other operations as part of this branch
    op.add_column(
        "feed",
        sa.Column(
            "required_for_install", sa.Boolean(), nullable=False, server_default="false"
        ),
    )


def downgrade():
    op.drop_table("system_update")
