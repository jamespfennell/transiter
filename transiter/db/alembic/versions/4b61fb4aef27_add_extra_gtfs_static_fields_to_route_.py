"""Add extra GTFS static fields to route etc

Revision ID: 4b61fb4aef27
Revises: 29e3a1cc76da
Create Date: 2020-06-12 11:46:26.807218

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4b61fb4aef27"
down_revision = "29e3a1cc76da"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "route",
        sa.Column(
            "continuous_drop_off",
            sa.Enum(
                "ALLOWED",
                "NOT_ALLOWED",
                "COORDINATE_WITH_AGENCY",
                "COORDINATE_WITH_DRIVER",
                name="boardingpolicy_1",
                native_enum=False,
            ),
            nullable=False,
            server_default="NOT_ALLOWED",
        ),
    )
    op.add_column(
        "route",
        sa.Column(
            "continuous_pickup",
            sa.Enum(
                "ALLOWED",
                "NOT_ALLOWED",
                "COORDINATE_WITH_AGENCY",
                "COORDINATE_WITH_DRIVER",
                name="boardingpolicy_2",
                native_enum=False,
            ),
            nullable=False,
            server_default="NOT_ALLOWED",
        ),
    )
    op.add_column(
        "scheduled_trip",
        sa.Column(
            "bikes_allowed",
            sa.Enum(
                "UNKNOWN",
                "ALLOWED",
                "NOT_ALLOWED",
                name="bikesallowed",
                native_enum=False,
            ),
            nullable=False,
            server_default="UNKNOWN",
        ),
    )
    op.add_column("scheduled_trip", sa.Column("block_id", sa.String(), nullable=True))
    op.add_column("scheduled_trip", sa.Column("headsign", sa.String(), nullable=True))
    op.add_column("scheduled_trip", sa.Column("short_name", sa.String(), nullable=True))
    op.add_column(
        "scheduled_trip",
        sa.Column(
            "wheelchair_accessible",
            sa.Enum(
                "UNKNOWN",
                "ACCESSIBLE",
                "NOT_ACCESSIBLE",
                name="wheelchairaccessible_3",
                native_enum=False,
            ),
            nullable=False,
            server_default="UNKNOWN",
        ),
    )
    op.add_column(
        "scheduled_trip_stop_time",
        sa.Column(
            "continuous_drop_off",
            sa.Enum(
                "ALLOWED",
                "NOT_ALLOWED",
                "COORDINATE_WITH_AGENCY",
                "COORDINATE_WITH_DRIVER",
                name="boardingpolicy_4",
                native_enum=False,
            ),
            nullable=False,
            server_default="NOT_ALLOWED",
        ),
    )
    op.add_column(
        "scheduled_trip_stop_time",
        sa.Column(
            "continuous_pickup",
            sa.Enum(
                "ALLOWED",
                "NOT_ALLOWED",
                "COORDINATE_WITH_AGENCY",
                "COORDINATE_WITH_DRIVER",
                name="boardingpolicy_5",
                native_enum=False,
            ),
            nullable=False,
            server_default="NOT_ALLOWED",
        ),
    )
    op.add_column(
        "scheduled_trip_stop_time",
        sa.Column(
            "drop_off_type",
            sa.Enum(
                "ALLOWED",
                "NOT_ALLOWED",
                "COORDINATE_WITH_AGENCY",
                "COORDINATE_WITH_DRIVER",
                name="boardingpolicy_6",
                native_enum=False,
            ),
            nullable=False,
            server_default="ALLOWED",
        ),
    )
    op.add_column(
        "scheduled_trip_stop_time",
        sa.Column("exact_times", sa.Boolean(), server_default="FALSE", nullable=False),
    )
    op.add_column(
        "scheduled_trip_stop_time", sa.Column("headsign", sa.String(), nullable=True)
    )
    op.add_column(
        "scheduled_trip_stop_time",
        sa.Column(
            "pickup_type",
            sa.Enum(
                "ALLOWED",
                "NOT_ALLOWED",
                "COORDINATE_WITH_AGENCY",
                "COORDINATE_WITH_DRIVER",
                name="boardingpolicy_7",
                native_enum=False,
            ),
            nullable=False,
            server_default="ALLOWED",
        ),
    )
    op.add_column(
        "scheduled_trip_stop_time",
        sa.Column("shape_distance_traveled", sa.Float(), nullable=True),
    )
    op.alter_column(
        "trip", "current_stop_sequence", existing_type=sa.INTEGER(), nullable=True
    )


def downgrade():
    pass
