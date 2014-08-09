# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import os

import settings
from db import session

from user.models import List, User


def create_db():
    if not os.path.exists(settings.db_path):
        print 'create db'
        session.connection().execute("PRAGMA journal_mode=WAL")
        session.commit()
        upgrade_db('0')

def upgrade_db(old):
    if old <= '20140527-120-3cb9819':
        create_index('ix_find_findvalue', 'find', ['findvalue'], unique=False)

def create_default_lists(user_id=None):
    user_id = user_id or settings.USER_ID
    user = User.get_or_create(user_id)
    user.update_name()
    for list in settings.config['lists']:
        l = List.get(user_id, list['title'])
        if not l:
            l = List.create(user_id, list['title'], list.get('query'))

