"""empty message

Revision ID: 3822b1700859
Revises: 1fe914156ac0
Create Date: 2014-05-20 23:25:34.942115

"""

# revision identifiers, used by Alembic.
revision = '3822b1700859'
down_revision = '1fe914156ac0'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('metadata',
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('modified', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=256), nullable=True),
    sa.Column('value', sa.String(length=256), nullable=True),
    sa.Column('data', sa.PickleType(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    #op.drop_column(u'item', 'sort_isbn13')
    #op.drop_column(u'item', 'sort_isbn10')
    #op.create_index(op.f('ix_item_sort_isbn'), 'item', ['sort_isbn'], unique=False)
    #op.drop_index('ix_item_sort_isbn10', table_name='item')
    #op.drop_index('ix_item_sort_isbn13', table_name='item')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_item_sort_isbn13', 'item', ['sort_isbn13'], unique=False)
    op.create_index('ix_item_sort_isbn10', 'item', ['sort_isbn10'], unique=False)
    op.drop_index(op.f('ix_item_sort_isbn'), table_name='item')
    op.add_column(u'item', sa.Column('sort_isbn10', sa.VARCHAR(length=1000), nullable=True))
    op.add_column(u'item', sa.Column('sort_isbn13', sa.VARCHAR(length=1000), nullable=True))
    op.drop_table('metadata')
    ### end Alembic commands ###