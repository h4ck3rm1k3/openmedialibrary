"""empty message

Revision ID: 3169519dc1e5
Revises: 1a7c813a17c2
Create Date: 2014-05-18 03:28:03.950996

"""

# revision identifiers, used by Alembic.
revision = '3169519dc1e5'
down_revision = '1a7c813a17c2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('queued', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'queued')
    ### end Alembic commands ###
