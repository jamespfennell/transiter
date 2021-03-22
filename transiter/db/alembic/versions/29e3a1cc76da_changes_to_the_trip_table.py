"""Changes to the trip table

Revision ID: 29e3a1cc76da
Revises: 455692a5a808
Create Date: 2020-06-11 10:20:35.482987

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "29e3a1cc76da"
down_revision = "455692a5a808"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "trip", sa.Column("current_stop_sequence", sa.Integer(), nullable=True)
    )
    # Set the current stop sequence for trips with future stop times
    op.get_bind().execute(
        sa.text(
            """
        UPDATE trip
        SET current_stop_sequence = (
            SELECT MAX(trip_stop_time.stop_sequence)
            FROM trip_stop_time
            WHERE trip_stop_time.trip_pk = trip.pk
            AND trip_stop_time.future
        )
        """
        )
    )
    # Set the current stop sequence for all other trips
    op.get_bind().execute(
        sa.text(
            """
        UPDATE trip
        SET current_stop_sequence = 100000
        WHERE current_stop_sequence IS NULL
        """
        )
    )
    op.alter_column("trip", "current_stop_sequence", nullable=False)
    op.drop_column("trip_stop_time", "future")


def downgrade():
    pass
