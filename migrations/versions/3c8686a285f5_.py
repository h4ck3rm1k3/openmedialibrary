"""empty message

Revision ID: 3c8686a285f5
Revises: None
Create Date: 2014-05-21 23:43:13.065858

"""

# revision identifiers, used by Alembic.
revision = '3c8686a285f5'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('item',
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('modified', sa.DateTime(), nullable=True),
    sa.Column('id', sa.String(length=32), nullable=False),
    sa.Column('info', sa.PickleType(), nullable=True),
    sa.Column('meta', sa.PickleType(), nullable=True),
    sa.Column('added', sa.DateTime(), nullable=True),
    sa.Column('accessed', sa.DateTime(), nullable=True),
    sa.Column('timesaccessed', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('changelog',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('timestamp', sa.BigInteger(), nullable=True),
    sa.Column('user_id', sa.String(length=43), nullable=True),
    sa.Column('revision', sa.BigInteger(), nullable=True),
    sa.Column('data', sa.Text(), nullable=True),
    sa.Column('sig', sa.String(length=96), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('modified', sa.DateTime(), nullable=True),
    sa.Column('id', sa.String(length=43), nullable=False),
    sa.Column('info', sa.PickleType(), nullable=True),
    sa.Column('nickname', sa.String(length=256), nullable=True),
    sa.Column('pending', sa.String(length=64), nullable=True),
    sa.Column('queued', sa.Boolean(), nullable=True),
    sa.Column('peered', sa.Boolean(), nullable=True),
    sa.Column('online', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nickname')
    )
    op.create_table('metadata',
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('modified', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=256), nullable=True),
    sa.Column('value', sa.String(length=256), nullable=True),
    sa.Column('data', sa.PickleType(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('person',
    sa.Column('name', sa.String(length=1024), nullable=False),
    sa.Column('sortname', sa.String(), nullable=True),
    sa.Column('numberofnames', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('name')
    )
    op.create_table('transfer',
    sa.Column('item_id', sa.String(length=32), nullable=False),
    sa.Column('added', sa.DateTime(), nullable=True),
    sa.Column('progress', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['item.id'], ),
    sa.PrimaryKeyConstraint('item_id')
    )
    op.create_table('find',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('item_id', sa.String(length=32), nullable=True),
    sa.Column('key', sa.String(length=200), nullable=True),
    sa.Column('value', sa.Text(), nullable=True),
    sa.Column('findvalue', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['item.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_find_key'), 'find', ['key'], unique=False)
    op.create_table('list',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('index_', sa.Integer(), nullable=True),
    sa.Column('type', sa.String(length=64), nullable=True),
    sa.Column('query', sa.PickleType(), nullable=True),
    sa.Column('user_id', sa.String(length=43), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('useritem',
    sa.Column('user_id', sa.String(length=43), nullable=True),
    sa.Column('item_id', sa.String(length=32), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['item.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.create_table('sort',
    sa.Column('item_id', sa.String(length=32), nullable=False),
    sa.Column('title', sa.String(length=1000), nullable=True),
    sa.Column('author', sa.String(length=1000), nullable=True),
    sa.Column('publisher', sa.String(length=1000), nullable=True),
    sa.Column('place', sa.String(length=1000), nullable=True),
    sa.Column('country', sa.String(length=1000), nullable=True),
    sa.Column('date', sa.String(length=1000), nullable=True),
    sa.Column('language', sa.String(length=1000), nullable=True),
    sa.Column('pages', sa.BigInteger(), nullable=True),
    sa.Column('classification', sa.String(length=1000), nullable=True),
    sa.Column('extension', sa.String(length=1000), nullable=True),
    sa.Column('size', sa.BigInteger(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('added', sa.DateTime(), nullable=True),
    sa.Column('modified', sa.DateTime(), nullable=True),
    sa.Column('accessed', sa.DateTime(), nullable=True),
    sa.Column('timesaccessed', sa.BigInteger(), nullable=True),
    sa.Column('mediastate', sa.String(length=1000), nullable=True),
    sa.Column('transferadded', sa.DateTime(), nullable=True),
    sa.Column('transferprogress', sa.Float(), nullable=True),
    sa.Column('id', sa.String(length=1000), nullable=True),
    sa.Column('isbn', sa.String(length=1000), nullable=True),
    sa.Column('asin', sa.String(length=1000), nullable=True),
    sa.Column('lccn', sa.String(length=1000), nullable=True),
    sa.Column('olid', sa.String(length=1000), nullable=True),
    sa.Column('oclc', sa.String(length=1000), nullable=True),
    sa.Column('random', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['item.id'], ),
    sa.PrimaryKeyConstraint('item_id')
    )
    op.create_index(op.f('ix_sort_accessed'), 'sort', ['accessed'], unique=False)
    op.create_index(op.f('ix_sort_added'), 'sort', ['added'], unique=False)
    op.create_index(op.f('ix_sort_asin'), 'sort', ['asin'], unique=False)
    op.create_index(op.f('ix_sort_author'), 'sort', ['author'], unique=False)
    op.create_index(op.f('ix_sort_classification'), 'sort', ['classification'], unique=False)
    op.create_index(op.f('ix_sort_country'), 'sort', ['country'], unique=False)
    op.create_index(op.f('ix_sort_created'), 'sort', ['created'], unique=False)
    op.create_index(op.f('ix_sort_date'), 'sort', ['date'], unique=False)
    op.create_index(op.f('ix_sort_extension'), 'sort', ['extension'], unique=False)
    op.create_index(op.f('ix_sort_id'), 'sort', ['id'], unique=False)
    op.create_index(op.f('ix_sort_isbn'), 'sort', ['isbn'], unique=False)
    op.create_index(op.f('ix_sort_language'), 'sort', ['language'], unique=False)
    op.create_index(op.f('ix_sort_lccn'), 'sort', ['lccn'], unique=False)
    op.create_index(op.f('ix_sort_mediastate'), 'sort', ['mediastate'], unique=False)
    op.create_index(op.f('ix_sort_modified'), 'sort', ['modified'], unique=False)
    op.create_index(op.f('ix_sort_oclc'), 'sort', ['oclc'], unique=False)
    op.create_index(op.f('ix_sort_olid'), 'sort', ['olid'], unique=False)
    op.create_index(op.f('ix_sort_pages'), 'sort', ['pages'], unique=False)
    op.create_index(op.f('ix_sort_place'), 'sort', ['place'], unique=False)
    op.create_index(op.f('ix_sort_publisher'), 'sort', ['publisher'], unique=False)
    op.create_index(op.f('ix_sort_random'), 'sort', ['random'], unique=False)
    op.create_index(op.f('ix_sort_size'), 'sort', ['size'], unique=False)
    op.create_index(op.f('ix_sort_timesaccessed'), 'sort', ['timesaccessed'], unique=False)
    op.create_index(op.f('ix_sort_title'), 'sort', ['title'], unique=False)
    op.create_index(op.f('ix_sort_transferadded'), 'sort', ['transferadded'], unique=False)
    op.create_index(op.f('ix_sort_transferprogress'), 'sort', ['transferprogress'], unique=False)
    op.create_table('file',
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('modified', sa.DateTime(), nullable=True),
    sa.Column('sha1', sa.String(length=32), nullable=False),
    sa.Column('path', sa.String(length=2048), nullable=True),
    sa.Column('info', sa.PickleType(), nullable=True),
    sa.Column('item_id', sa.String(length=32), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['item.id'], ),
    sa.PrimaryKeyConstraint('sha1')
    )
    op.create_table('listitem',
    sa.Column('list_id', sa.Integer(), nullable=True),
    sa.Column('item_id', sa.String(length=32), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['item.id'], ),
    sa.ForeignKeyConstraint(['list_id'], ['list.id'], )
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('listitem')
    op.drop_table('file')
    op.drop_index(op.f('ix_sort_transferprogress'), table_name='sort')
    op.drop_index(op.f('ix_sort_transferadded'), table_name='sort')
    op.drop_index(op.f('ix_sort_title'), table_name='sort')
    op.drop_index(op.f('ix_sort_timesaccessed'), table_name='sort')
    op.drop_index(op.f('ix_sort_size'), table_name='sort')
    op.drop_index(op.f('ix_sort_random'), table_name='sort')
    op.drop_index(op.f('ix_sort_publisher'), table_name='sort')
    op.drop_index(op.f('ix_sort_place'), table_name='sort')
    op.drop_index(op.f('ix_sort_pages'), table_name='sort')
    op.drop_index(op.f('ix_sort_olid'), table_name='sort')
    op.drop_index(op.f('ix_sort_oclc'), table_name='sort')
    op.drop_index(op.f('ix_sort_modified'), table_name='sort')
    op.drop_index(op.f('ix_sort_mediastate'), table_name='sort')
    op.drop_index(op.f('ix_sort_lccn'), table_name='sort')
    op.drop_index(op.f('ix_sort_language'), table_name='sort')
    op.drop_index(op.f('ix_sort_isbn'), table_name='sort')
    op.drop_index(op.f('ix_sort_id'), table_name='sort')
    op.drop_index(op.f('ix_sort_extension'), table_name='sort')
    op.drop_index(op.f('ix_sort_date'), table_name='sort')
    op.drop_index(op.f('ix_sort_created'), table_name='sort')
    op.drop_index(op.f('ix_sort_country'), table_name='sort')
    op.drop_index(op.f('ix_sort_classification'), table_name='sort')
    op.drop_index(op.f('ix_sort_author'), table_name='sort')
    op.drop_index(op.f('ix_sort_asin'), table_name='sort')
    op.drop_index(op.f('ix_sort_added'), table_name='sort')
    op.drop_index(op.f('ix_sort_accessed'), table_name='sort')
    op.drop_table('sort')
    op.drop_table('useritem')
    op.drop_table('list')
    op.drop_index(op.f('ix_find_key'), table_name='find')
    op.drop_table('find')
    op.drop_table('transfer')
    op.drop_table('person')
    op.drop_table('metadata')
    op.drop_table('user')
    op.drop_table('changelog')
    op.drop_table('item')
    ### end Alembic commands ###