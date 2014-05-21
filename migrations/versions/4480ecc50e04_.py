"""empty message

Revision ID: 4480ecc50e04
Revises: 3169519dc1e5
Create Date: 2014-05-20 02:20:20.283739

"""

# revision identifiers, used by Alembic.
revision = '4480ecc50e04'
down_revision = '3169519dc1e5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('changelog', sa.Column('timestamp', sa.BigInteger(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('changelog', 'timestamp')
    ### end Alembic commands ###