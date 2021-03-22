"""
Feed update column clean up.

Revision ID: b521e2a9055a
Revises: be93cf805bb4
Create Date: 2020-03-19 22:17:03.347841

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b521e2a9055a"
down_revision = "be93cf805bb4"
branch_labels = None
depends_on = None


def upgrade():
    # (1) Remove indices
    op.drop_index("feed_updates_last_successful_idx", table_name="feed_update")
    op.drop_index("ix_feed_update_last_action_time", table_name="feed_update")

    # (2) Remove existing columns
    op.drop_column("feed_update", "failure_message")
    op.drop_column("feed_update", "execution_duration")
    op.drop_column("feed_update", "feed_time")
    op.drop_column("feed_update", "explanation")
    op.drop_column("feed_update", "raw_data_hash")

    # (3) Rename last_action_time to completed_at
    op.alter_column(
        "feed_update",
        "last_action_time",
        new_column_name="completed_at",
        server_default=None,
    )

    # (4) Add new columns
    op.add_column(
        "feed_update",
        sa.Column("content_created_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column("feed_update", sa.Column("content_hash", sa.String(), nullable=True))
    op.add_column(
        "feed_update", sa.Column("download_duration", sa.Float(), nullable=True)
    )
    op.add_column(
        "feed_update",
        sa.Column(
            "result",
            sa.Enum(
                "UPDATED",
                "NOT_NEEDED",
                "PARSE_ERROR",
                "DOWNLOAD_ERROR",
                "INVALID_PARSER",
                "EMPTY_FEED",
                "SYNC_ERROR",
                "UNEXPECTED_ERROR",
                name="result",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "feed_update", sa.Column("num_parsed_entities", sa.Integer(), nullable=True)
    )
    op.add_column(
        "feed_update", sa.Column("num_added_entities", sa.Integer(), nullable=True)
    )
    op.add_column(
        "feed_update", sa.Column("num_updated_entities", sa.Integer(), nullable=True)
    )
    op.add_column(
        "feed_update", sa.Column("num_deleted_entities", sa.Integer(), nullable=True)
    )
    op.add_column(
        "feed_update", sa.Column("result_message", sa.String(), nullable=True)
    )
    op.add_column(
        "feed_update",
        sa.Column("scheduled_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column("feed_update", sa.Column("total_duration", sa.Float(), nullable=True))

    # (5) Add multi-column indices
    op.create_index(
        "feed_update_success_pk_completed_at_idx",
        "feed_update",
        ["feed_pk", "completed_at"],
        unique=False,
        postgresql_where=sa.text("status = 'SUCCESS'"),
    )
    op.create_index(
        "feed_update_feed_pk_feed_update_pk_idx",
        "feed_update",
        ["feed_pk", "pk"],
        unique=False,
    )


def downgrade():
    pass
