"""empty message

Revision ID: e69272b623ed
Revises: 6526a8ddff19
Create Date: 2019-12-07 12:14:25.860226

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e69272b623ed'
down_revision = '6526a8ddff19'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE userpermission SET permission_name = 'view' WHERE permission_name = 'domestic_external';")
    op.execute("UPDATE userpermission SET permission_name = 'edit' WHERE permission_name = 'domestic_external_edit';")
    op.execute("UPDATE role SET name = 'AMCU Desk Officer' WHERE slug='desk-officer';")
    op.execute("UPDATE role SET name = 'Manager' WHERE slug='manager';")
    op.execute("UPDATE role SET name = 'Administrator' WHERE slug='admin';")
    op.execute("INSERT INTO role (slug, name) VALUES ('results-data-entry','Results Data Entry');")


def downgrade():
    op.execute("UPDATE userpermission SET permission_name = 'domestic_external' WHERE permission_name = 'view';")
    op.execute("UPDATE userpermission SET permission_name = 'domestic_external_edit' WHERE permission_name = 'edit';")
    op.execute("UPDATE role SET name = 'desk-officer' WHERE slug='desk-officer';")
    op.execute("UPDATE role SET name = 'manager' WHERE slug='manager';")
    op.execute("UPDATE role SET name = 'admin' WHERE slug='admin';")
    op.execute("DELETE FROM role WHERE slug = 'results-data-entry';")
