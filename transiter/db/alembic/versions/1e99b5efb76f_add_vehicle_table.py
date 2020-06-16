"""Add vehicle table

Revision ID: 1e99b5efb76f
Revises: 2bbd670f53b4
Create Date: 2020-05-24 15:29:19.928946

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "1e99b5efb76f"
down_revision = "2bbd670f53b4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "vehicle",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(), nullable=True),
        sa.Column("source_pk", sa.Integer(), nullable=False),
        sa.Column("system_pk", sa.Integer(), nullable=False),
        sa.Column("trip_pk", sa.Integer(), nullable=True),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("license_plate", sa.String(), nullable=True),
        sa.Column(
            "current_status",
            sa.Enum(
                "INCOMING_AT",
                "STOPPED_AT",
                "IN_TRANSIT_TO",
                name="status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("bearing", sa.Float(), nullable=True),
        sa.Column("odometer", sa.Float(), nullable=True),
        sa.Column("speed", sa.Float(), nullable=True),
        sa.Column(
            "congestion_level",
            sa.Enum(
                "UNKNOWN_CONGESTION_LEVEL",
                "RUNNING_SMOOTHLY",
                "STOP_AND_GO",
                "CONGESTION",
                "SEVERE_CONGESTION",
                name="congestionlevel",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["source_pk"], ["feed_update.pk"],),
        sa.ForeignKeyConstraint(["system_pk"], ["system.pk"],),
        sa.PrimaryKeyConstraint("pk"),
        sa.UniqueConstraint("system_pk", "id"),
    )
    op.create_index(
        op.f("ix_vehicle_source_pk"), "vehicle", ["source_pk"], unique=False
    )
    op.create_index(
        op.f("ix_vehicle_system_pk"), "vehicle", ["system_pk"], unique=False
    )
    op.create_index(op.f("ix_vehicle_trip_pk"), "vehicle", ["trip_pk"], unique=True)
    op.create_foreign_key(None, "vehicle", "trip", ["trip_pk"], ["pk"])
    op.alter_column("alert", "cause", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("alert", "effect", existing_type=sa.VARCHAR(), nullable=False)
    op.add_column("trip", sa.Column("delay", sa.Integer(), nullable=True))
    op.add_column(
        "trip", sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True)
    )
    op.add_column(
        "trip", sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True)
    )
    op.drop_column("trip", "current_stop_sequence")
    op.drop_column("trip", "vehicle_id")
    op.drop_column("trip", "last_update_time")
    op.drop_column("trip", "start_time")
    op.drop_column("trip", "current_status")

    op.add_column("vehicle", sa.Column("current_stop_pk", sa.Integer(), nullable=True))
    op.add_column(
        "vehicle", sa.Column("current_stop_sequence", sa.Integer(), nullable=True)
    )
    op.add_column(
        "vehicle",
        sa.Column(
            "occupancy_status",
            sa.Enum(
                "EMPTY",
                "MANY_SEATS_AVAILABLE",
                "FEW_SEATS_AVAILABLE",
                "STANDING_ROOM_ONLY",
                "CRUSHED_STANDING_ROOM_ONLY",
                "FULL",
                "NOT_ACCEPTING_PASSENGERS",
                "UNKNOWN",
                name="occupancystatus",
                native_enum=False,
            ),
            nullable=False,
        ),
    )
    op.create_foreign_key(None, "vehicle", "stop", ["current_stop_pk"], ["pk"])


def downgrade():
    pass
