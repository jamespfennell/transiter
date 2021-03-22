"""Add extra columns to stop table

Revision ID: 08ce9c5194a4
Revises: 36e00f5e2f0e
Create Date: 2020-05-08 10:13:29.558910

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "08ce9c5194a4"
down_revision = "36e00f5e2f0e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("stop", sa.Column("code", sa.String(), nullable=True))
    op.add_column("stop", sa.Column("description", sa.String(), nullable=True))
    op.add_column("stop", sa.Column("platform_code", sa.String(), nullable=True))
    op.add_column("stop", sa.Column("timezone", sa.String(), nullable=True))
    op.add_column(
        "stop",
        sa.Column(
            "type",
            sa.Enum(
                "PLATFORM",
                "STATION",
                "ENTRANCE_OR_EXIT",
                "GENERIC_NODE",
                "BOARDING_AREA",
                "GROUPED_STATION",
                name="type",
                native_enum=False,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "stop",
        sa.Column(
            "wheelchair_boarding",
            sa.Enum(
                "NOT_SPECIFIED",
                "ACCESSIBLE",
                "NOT_ACCESSIBLE",
                name="wheelchairboarding",
                native_enum=False,
            ),
            nullable=True,
        ),
    )
    op.add_column("stop", sa.Column("zone_id", sa.String(), nullable=True))

    # Migrate data from the is_station column to the type column
    op.get_bind().execute(
        sa.text("update stop set type = 'PLATFORM' where not stop.is_station")
    )
    op.get_bind().execute(
        sa.text("update stop set type = 'STATION' where stop.is_station")
    )

    op.alter_column("stop", "type", nullable=False)
    op.drop_column("stop", "is_station")


def downgrade():
    pass
