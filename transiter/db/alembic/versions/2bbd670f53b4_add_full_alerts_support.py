"""Add full alerts support

Revision ID: 2bbd670f53b4
Revises: 08ce9c5194a4
Create Date: 2020-05-15 09:36:44.069109

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2bbd670f53b4"
down_revision = "08ce9c5194a4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "alert_active_period",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("alert_pk", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("ends_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["alert_pk"], ["alert.pk"],),
        sa.PrimaryKeyConstraint("pk"),
    )
    op.create_index(
        op.f("ix_alert_active_period_alert_pk"),
        "alert_active_period",
        ["alert_pk"],
        unique=False,
    )
    op.create_table(
        "alert_message",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("alert_pk", sa.Integer(), nullable=False),
        sa.Column("header", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("language", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["alert_pk"], ["alert.pk"],),
        sa.PrimaryKeyConstraint("pk"),
    )
    op.create_index(
        op.f("ix_alert_message_alert_pk"), "alert_message", ["alert_pk"], unique=False
    )
    op.create_table(
        "alert_stop",
        sa.Column("alert_pk", sa.Integer(), nullable=True),
        sa.Column("stop_pk", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["alert_pk"], ["alert.pk"],),
        sa.ForeignKeyConstraint(["stop_pk"], ["stop.pk"],),
    )
    op.create_index(
        op.f("ix_alert_stop_alert_pk"), "alert_stop", ["alert_pk"], unique=False
    )
    op.create_index(
        op.f("ix_alert_stop_stop_pk"), "alert_stop", ["stop_pk"], unique=False
    )
    op.create_table(
        "alert_trip",
        sa.Column("alert_pk", sa.Integer(), nullable=True),
        sa.Column("trip_pk", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["alert_pk"], ["alert.pk"],),
        sa.ForeignKeyConstraint(["trip_pk"], ["trip.pk"],),
    )
    op.create_index(
        op.f("ix_alert_trip_alert_pk"), "alert_trip", ["alert_pk"], unique=False
    )
    op.create_index(
        op.f("ix_alert_trip_trip_pk"), "alert_trip", ["trip_pk"], unique=False
    )
    op.add_column(
        "alert", sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True)
    )
    op.add_column("alert", sa.Column("sort_order", sa.Integer(), nullable=True))
    op.add_column(
        "alert", sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True)
    )
    op.drop_column("alert", "creation_time")
    op.drop_column("alert", "url")
    op.drop_column("alert", "description")
    op.drop_column("alert", "header")
    op.drop_column("alert", "start_time")
    op.drop_column("alert", "end_time")
    op.drop_column("alert", "priority")
    op.create_index(
        op.f("ix_alert_agency_alert_pk"), "alert_agency", ["alert_pk"], unique=False
    )
    op.create_index(
        op.f("ix_alert_route_alert_pk"), "alert_route", ["alert_pk"], unique=False
    )
    op.alter_column("stop", "type", existing_type=sa.VARCHAR(length=16), nullable=False)
