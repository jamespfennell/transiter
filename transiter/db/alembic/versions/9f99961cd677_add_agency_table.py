"""Add agency table

Revision ID: 9f99961cd677
Revises: 5bc1207e7593
Create Date: 2020-05-05 09:20:36.415430

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9f99961cd677"
down_revision = "5bc1207e7593"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agency",
        sa.Column("pk", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("system_pk", sa.Integer(), nullable=False),
        sa.Column("source_pk", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("timezone", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("fare_url", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["source_pk"], ["feed_update.pk"],),
        sa.ForeignKeyConstraint(["system_pk"], ["system.pk"],),
        sa.PrimaryKeyConstraint("pk"),
        sa.UniqueConstraint("system_pk", "id"),
    )
    op.create_index(op.f("ix_agency_source_pk"), "agency", ["source_pk"], unique=False)
    op.create_table(
        "alert_agency",
        sa.Column("alert_pk", sa.Integer(), nullable=True),
        sa.Column("agency_pk", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["agency_pk"], ["agency.pk"],),
        sa.ForeignKeyConstraint(["alert_pk"], ["alert.pk"],),
    )
    op.create_index(
        op.f("ix_alert_agency_agency_pk"), "alert_agency", ["agency_pk"], unique=False
    )
    op.create_index(
        "feed_update_success_pk_completed_at_idx",
        "feed_update",
        ["feed_pk", "completed_at"],
        unique=False,
        postgresql_where=sa.text("status = 'SUCCESS'"),
    )
    op.add_column("route", sa.Column("agency_pk", sa.Integer(), nullable=True))
    op.create_foreign_key(None, "route", "agency", ["agency_pk"], ["pk"])
    op.create_unique_constraint(None, "alert", ["system_pk", "id"])


def downgrade():
    pass
