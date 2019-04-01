"""Merging counterpart funding and forwardspend fixes branches

Revision ID: 460a1cf214a7
Revises: ed668c6d41ed, d7f457367fcd
Create Date: 2019-04-01 16:33:33.124667

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '460a1cf214a7'
down_revision = ('ed668c6d41ed', 'd7f457367fcd')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
