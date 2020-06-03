"""DB changes for system config updates

Revision ID: 423495a41dd6
Revises: 123df9e95dda
Create Date: 2020-06-03 10:11:26.161183

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "423495a41dd6"
down_revision = "123df9e95dda"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("feed", sa.Column("http_timeout", sa.Float(), nullable=True))
    op.add_column("feed", sa.Column("parser_options", sa.String(), nullable=True))
    op.alter_column("system", "name", existing_type=sa.VARCHAR(), nullable=False)


def downgrade():
    pass
