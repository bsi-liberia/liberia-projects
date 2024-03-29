"""empty message

Revision ID: ac4a76c46e3e
Revises: 613aa1ee10a8
Create Date: 2021-08-10 18:45:33.228002

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ac4a76c46e3e'
down_revision = '613aa1ee10a8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("activityfinances") as batch_op:
        batch_op.add_column(sa.Column('fiscal_period_id', sa.UnicodeText(), nullable=True))
        batch_op.create_foreign_key('fk_activityfinances__fiscal_period_id', 'fiscal_period', ['fiscal_period_id'], ['id'])
    with op.batch_alter_table("forwardspend") as batch_op:
        batch_op.add_column(sa.Column('fiscal_period_id', sa.UnicodeText(), nullable=True))
        batch_op.create_foreign_key('fk_forwardspend__fiscal_period_id', 'fiscal_period', ['fiscal_period_id'], ['id'])
    with op.batch_alter_table("activitycounterpartfunding") as batch_op:
        batch_op.add_column(sa.Column('fiscal_period_id', sa.UnicodeText(), nullable=True))
        batch_op.create_foreign_key('fk_factivitycounterpartfunding__fiscal_period_id', 'fiscal_period', ['fiscal_period_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("activityfinances") as batch_op:
        batch_op.drop_constraint('fk_activityfinances__fiscal_period_id', type_='foreignkey')
        batch_op.drop_column('fiscal_period_id')
    with op.batch_alter_table("forwardspend") as batch_op:
        batch_op.drop_constraint('fk_forwardspend__fiscal_period_id', type_='foreignkey')
        batch_op.drop_column('fiscal_period_id')
    with op.batch_alter_table("activitycounterpartfunding") as batch_op:
        batch_op.drop_constraint('fk_factivitycounterpartfunding__fiscal_period_id', type_='foreignkey')
        batch_op.drop_column('fiscal_period_id')
    # ### end Alembic commands ###
