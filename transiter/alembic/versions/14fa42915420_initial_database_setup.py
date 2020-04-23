"""
Initial database setup.

Revision ID: 14fa42915420
Revises:
Create Date: 2020-03-08 20:18:55.140759

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "14fa42915420"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "system",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "SCHEDULED",
                "INSTALLING",
                "ACTIVE",
                "INSTALL_FAILED",
                "DELETING",
                name="systemstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("timezone", sa.String(), nullable=True),
        sa.Column("raw_config", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("pk"),
    )
    op.create_index(op.f("ix_system_id"), "system", ["id"], unique=True)
    op.create_table(
        "feed",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(), nullable=True),
        sa.Column("system_pk", sa.Integer(), nullable=True),
        sa.Column(
            "built_in_parser",
            sa.Enum(
                "GTFS_STATIC", "GTFS_REALTIME", name="builtinparser", native_enum=False
            ),
            nullable=True,
        ),
        sa.Column("custom_parser", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("headers", sa.String(), nullable=True),
        sa.Column("auto_update_on", sa.Boolean(), nullable=True),
        sa.Column("auto_update_period", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["system_pk"], ["system.pk"],),
        sa.PrimaryKeyConstraint("pk"),
        sa.UniqueConstraint("system_pk", "id"),
    )
    op.create_table(
        "service_map_group",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("system_pk", sa.Integer(), nullable=False),
        sa.Column(
            "source",
            sa.Enum("SCHEDULE", "REALTIME", name="servicemapsource", native_enum=False),
            nullable=False,
        ),
        sa.Column("conditions", sa.String(), nullable=True),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("use_for_routes_at_stop", sa.Boolean(), nullable=False),
        sa.Column("use_for_stops_in_route", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["system_pk"], ["system.pk"],),
        sa.PrimaryKeyConstraint("pk"),
    )
    op.create_table(
        "feed_update",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("feed_pk", sa.Integer(), nullable=True),
        sa.Column(
            "update_type",
            sa.Enum("REGULAR", "FLUSH", name="update_type", native_enum=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "SCHEDULED",
                "IN_PROGRESS",
                "SUCCESS",
                "FAILURE",
                name="status",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "explanation",
            sa.Enum(
                "UPDATED",
                "NOT_NEEDED",
                "PARSE_ERROR",
                "DOWNLOAD_ERROR",
                "INVALID_PARSER",
                "EMPTY_FEED",
                "SYNC_ERROR",
                "UNEXPECTED_ERROR",
                name="explanation",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column("failure_message", sa.String(), nullable=True),
        sa.Column("raw_data_hash", sa.String(), nullable=True),
        sa.Column("content_length", sa.Integer(), nullable=True),
        sa.Column("execution_duration", sa.Float(), nullable=True),
        sa.Column(
            "last_action_time",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("feed_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["feed_pk"], ["feed.pk"],),
        sa.PrimaryKeyConstraint("pk"),
    )
    op.create_index(
        "feed_updates_last_successful_idx",
        "feed_update",
        ["feed_pk", "last_action_time", "status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_feed_update_last_action_time"),
        "feed_update",
        ["last_action_time"],
        unique=False,
    )
    op.create_table(
        "alert",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(), nullable=True),
        sa.Column("source_pk", sa.Integer(), nullable=True),
        sa.Column("header", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column(
            "cause",
            sa.Enum(
                "UNKNOWN_CAUSE",
                "OTHER_CAUSE",
                "TECHNICAL_PROBLEM",
                "STRIKE",
                "DEMONSTRATION",
                "ACCIDENT",
                "HOLIDAY",
                "WEATHER",
                "MAINTENANCE",
                "CONSTRUCTION",
                "POLICE_ACTIVITY",
                "MEDICAL_EMERGENCY",
                name="cause",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "effect",
            sa.Enum(
                "NO_SERVICE",
                "REDUCED_SERVICE",
                "SIGNIFICANT_DELAYS",
                "DETOUR",
                "ADDITIONAL_SERVICE",
                "MODIFIED_SERVICE",
                "OTHER_EFFECT",
                "UNKNOWN_EFFECT",
                "STOP_MOVED",
                name="effect",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("end_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("creation_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("system_pk", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["source_pk"], ["feed_update.pk"],),
        sa.ForeignKeyConstraint(["system_pk"], ["system.pk"],),
        sa.PrimaryKeyConstraint("pk"),
    )
    op.create_index(op.f("ix_alert_source_pk"), "alert", ["source_pk"], unique=False)
    op.create_index(op.f("ix_alert_system_pk"), "alert", ["system_pk"], unique=False)
    op.create_table(
        "route",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(), nullable=True),
        sa.Column("system_pk", sa.Integer(), nullable=False),
        sa.Column("source_pk", sa.Integer(), nullable=True),
        sa.Column("color", sa.String(), nullable=True),
        sa.Column("text_color", sa.String(), nullable=True),
        sa.Column("short_name", sa.String(), nullable=True),
        sa.Column("long_name", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column(
            "type",
            sa.Enum(
                "LIGHT_RAIL",
                "SUBWAY",
                "RAIL",
                "BUS",
                "FERRY",
                "CABLE_CAR",
                "GONDOLA",
                "FUNICULAR",
                name="route_type",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["source_pk"], ["feed_update.pk"],),
        sa.ForeignKeyConstraint(["system_pk"], ["system.pk"],),
        sa.PrimaryKeyConstraint("pk"),
        sa.UniqueConstraint("system_pk", "id"),
    )
    op.create_index(op.f("ix_route_source_pk"), "route", ["source_pk"], unique=False)
    op.create_table(
        "scheduled_service",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("system_pk", sa.Integer(), nullable=True),
        sa.Column("source_pk", sa.Integer(), nullable=True),
        sa.Column("monday", sa.Boolean(), nullable=True),
        sa.Column("tuesday", sa.Boolean(), nullable=True),
        sa.Column("wednesday", sa.Boolean(), nullable=True),
        sa.Column("thursday", sa.Boolean(), nullable=True),
        sa.Column("friday", sa.Boolean(), nullable=True),
        sa.Column("saturday", sa.Boolean(), nullable=True),
        sa.Column("sunday", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["source_pk"], ["feed_update.pk"],),
        sa.ForeignKeyConstraint(["system_pk"], ["system.pk"],),
        sa.PrimaryKeyConstraint("pk"),
    )
    op.create_index(
        op.f("ix_scheduled_service_source_pk"),
        "scheduled_service",
        ["source_pk"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scheduled_service_system_pk"),
        "scheduled_service",
        ["system_pk"],
        unique=False,
    )
    op.create_table(
        "stop",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(), nullable=True),
        sa.Column("system_pk", sa.Integer(), nullable=False),
        sa.Column("source_pk", sa.Integer(), nullable=True),
        sa.Column("parent_stop_pk", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("is_station", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["parent_stop_pk"], ["stop.pk"],),
        sa.ForeignKeyConstraint(["source_pk"], ["feed_update.pk"],),
        sa.ForeignKeyConstraint(["system_pk"], ["system.pk"],),
        sa.PrimaryKeyConstraint("pk"),
        sa.UniqueConstraint("system_pk", "id"),
    )
    op.create_index(
        op.f("ix_stop_parent_stop_pk"), "stop", ["parent_stop_pk"], unique=False
    )
    op.create_index(op.f("ix_stop_source_pk"), "stop", ["source_pk"], unique=False)
    op.create_table(
        "alert_route",
        sa.Column("alert_pk", sa.Integer(), nullable=True),
        sa.Column("route_pk", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["alert_pk"], ["alert.pk"],),
        sa.ForeignKeyConstraint(["route_pk"], ["route.pk"],),
    )
    op.create_index(
        op.f("ix_alert_route_route_pk"), "alert_route", ["route_pk"], unique=False
    )
    op.create_table(
        "direction_name_rule",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(), nullable=True),
        sa.Column("stop_pk", sa.Integer(), nullable=True),
        sa.Column("source_pk", sa.Integer(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("direction_id", sa.Boolean(), nullable=True),
        sa.Column("track", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["source_pk"], ["feed_update.pk"],),
        sa.ForeignKeyConstraint(["stop_pk"], ["stop.pk"],),
        sa.PrimaryKeyConstraint("pk"),
    )
    op.create_index(
        "direction_name_rule_stop_pk_priority_idx",
        "direction_name_rule",
        ["stop_pk", "priority"],
        unique=False,
    )
    op.create_index(
        op.f("ix_direction_name_rule_source_pk"),
        "direction_name_rule",
        ["source_pk"],
        unique=False,
    )
    op.create_table(
        "scheduled_trip",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("route_pk", sa.Integer(), nullable=False),
        sa.Column("service_pk", sa.Integer(), nullable=False),
        sa.Column("direction_id", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["route_pk"], ["route.pk"],),
        sa.ForeignKeyConstraint(["service_pk"], ["scheduled_service.pk"],),
        sa.PrimaryKeyConstraint("pk"),
    )
    op.create_table(
        "service_map",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("route_pk", sa.Integer(), nullable=False),
        sa.Column("group_pk", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["group_pk"], ["service_map_group.pk"],),
        sa.ForeignKeyConstraint(["route_pk"], ["route.pk"],),
        sa.PrimaryKeyConstraint("pk"),
        sa.UniqueConstraint("route_pk", "group_pk"),
    )
    op.create_index(
        op.f("ix_service_map_route_pk"), "service_map", ["route_pk"], unique=False
    )
    op.create_table(
        "trip",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(), nullable=True),
        sa.Column("route_pk", sa.Integer(), nullable=False),
        sa.Column("source_pk", sa.Integer(), nullable=True),
        sa.Column("direction_id", sa.Boolean(), nullable=True),
        sa.Column("start_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_update_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("vehicle_id", sa.String(), nullable=True),
        sa.Column(
            "current_status",
            sa.Enum(
                "SCHEDULED",
                "INCOMING_AT",
                "STOPPED_AT",
                "IN_TRANSIT_TO",
                name="tripstatus",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column("current_stop_sequence", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["route_pk"], ["route.pk"],),
        sa.ForeignKeyConstraint(["source_pk"], ["feed_update.pk"],),
        sa.PrimaryKeyConstraint("pk"),
        sa.UniqueConstraint("route_pk", "id"),
    )
    op.create_index(op.f("ix_trip_source_pk"), "trip", ["source_pk"], unique=False)
    op.create_table(
        "scheduled_trip_stop_time",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("trip_pk", sa.Integer(), nullable=False),
        sa.Column("stop_pk", sa.Integer(), nullable=False),
        sa.Column("arrival_time", sa.Time(), nullable=True),
        sa.Column("departure_time", sa.Time(), nullable=True),
        sa.Column("stop_sequence", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["stop_pk"], ["stop.pk"],),
        sa.ForeignKeyConstraint(["trip_pk"], ["scheduled_trip.pk"],),
        sa.PrimaryKeyConstraint("pk"),
        sa.UniqueConstraint("trip_pk", "stop_sequence"),
    )
    op.create_index(
        "scheduled_trip_stop_time_trip_pk_departure_time_idx",
        "scheduled_trip_stop_time",
        ["trip_pk", "departure_time"],
        unique=False,
    )
    op.create_table(
        "service_map_vertex",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("stop_pk", sa.Integer(), nullable=True),
        sa.Column("map_pk", sa.Integer(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["map_pk"], ["service_map.pk"],),
        sa.ForeignKeyConstraint(["stop_pk"], ["stop.pk"],),
        sa.PrimaryKeyConstraint("pk"),
    )
    op.create_index(
        "service_map_vertex_map_pk_position",
        "service_map_vertex",
        ["map_pk", "position"],
        unique=False,
    )
    op.create_table(
        "trip_stop_time",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("stop_pk", sa.Integer(), nullable=False),
        sa.Column("trip_pk", sa.Integer(), nullable=False),
        sa.Column("future", sa.Boolean(), nullable=True),
        sa.Column("arrival_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("arrival_delay", sa.Integer(), nullable=True),
        sa.Column("arrival_uncertainty", sa.Integer(), nullable=True),
        sa.Column("departure_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("departure_delay", sa.Integer(), nullable=True),
        sa.Column("departure_uncertainty", sa.Integer(), nullable=True),
        sa.Column("stop_sequence", sa.Integer(), nullable=False),
        sa.Column("track", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["stop_pk"], ["stop.pk"],),
        sa.ForeignKeyConstraint(["trip_pk"], ["trip.pk"],),
        sa.PrimaryKeyConstraint("pk"),
        sa.UniqueConstraint("trip_pk", "stop_sequence"),
    )
    op.create_index(
        "trip_stop_time_stop_pk_arrival_time_idx",
        "trip_stop_time",
        ["stop_pk", "arrival_time"],
        unique=False,
    )


def downgrade():
    # op.drop_table("trip_stop_time")
    pass
