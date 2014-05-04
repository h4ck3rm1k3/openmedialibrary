# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import settings
from user.models import List, User

def create_default_lists(user_id=None):
    user_id = user_id or settings.USER_ID
    user = User.get_or_create(user_id)
    for list in settings.config['lists']:
        l = List.get(user_id, list['title'])
        if not l:
            l = List.create(user_id, list['title'], list.get('query'))

