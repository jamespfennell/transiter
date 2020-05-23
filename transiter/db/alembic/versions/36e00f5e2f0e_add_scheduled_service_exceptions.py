"""Add scheduled service exceptions

Revision ID: 36e00f5e2f0e
Revises: 9f99961cd677
Create Date: 2020-05-07 09:14:44.982479

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "36e00f5e2f0e"
down_revision = "9f99961cd677"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "scheduled_service_addition",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("service_pk", sa.Integer(), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["service_pk"], ["scheduled_service.pk"],),
        sa.PrimaryKeyConstraint("pk"),
    )
    op.create_index(
        op.f("ix_scheduled_service_addition_service_pk"),
        "scheduled_service_addition",
        ["service_pk"],
        unique=False,
    )
    op.create_table(
        "scheduled_service_removal",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("service_pk", sa.Integer(), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["service_pk"], ["scheduled_service.pk"],),
        sa.PrimaryKeyConstraint("pk"),
    )
    op.create_index(
        op.f("ix_scheduled_service_removal_service_pk"),
        "scheduled_service_removal",
        ["service_pk"],
        unique=False,
    )
    op.add_column("scheduled_service", sa.Column("end_date", sa.Date(), nullable=True))
    op.add_column(
        "scheduled_service", sa.Column("start_date", sa.Date(), nullable=True)
    )

    op.create_table(
        "scheduled_trip_frequency",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("trip_pk", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(timezone=True), nullable=False),
        sa.Column("end_time", sa.Time(timezone=True), nullable=False),
        sa.Column("headway", sa.Integer(), nullable=False),
        sa.Column("frequency_based", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["trip_pk"], ["scheduled_trip.pk"],),
        sa.PrimaryKeyConstraint("pk"),
    )


def downgrade():
    pass
