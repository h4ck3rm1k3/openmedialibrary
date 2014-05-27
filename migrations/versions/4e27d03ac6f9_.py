"""empty message

Revision ID: 4e27d03ac6f9
Revises: 3c8686a285f5
Create Date: 2014-05-27 01:37:54.288697

"""

# revision identifiers, used by Alembic.
revision = '4e27d03ac6f9'
down_revision = '3c8686a285f5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_find_findvalue'), 'find', ['findvalue'], unique=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_find_findvalue'), table_name='find')
    ### end Alembic commands ###