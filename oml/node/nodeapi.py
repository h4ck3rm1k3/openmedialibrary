# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


from changelog import Changelog
from user.models import User
from websocket import trigger_event
import settings
import state

import logging
logger = logging.getLogger(__name__)

def api_pullChanges(remote_id, user_id=None, from_=None, to=None):
    if user_id and not from_ and not to:
        from_ = user_id
        user_id = None
    if user_id and from_ and not to:
        if isinstance(user_id, int):
            to = from_
            from_ = user_id
            user_id = None
    from_ = from_ or 0
    if user_id:
        return []
    if not user_id:
        user_id = settings.USER_ID
    qs = Changelog.query.filter_by(user_id=user_id)
    if from_:
        qs = qs.filter(Changelog.revision>=from_)
    if to:
        qs = qs.filter(Changelog.revision<to)
    state.nodes.queue('add', remote_id)
    return [c.json() for c in qs]

def api_pushChanges(user_id, changes):
    logger.debug('pushChanges no longer used, ignored')
    return True
    user = User.get(user_id)
    if not Changelog.apply_changes(user, changes):
        logger.debug('FAILED TO APPLY CHANGE')
        state.nodes.queue(user_id, 'pullChanges')
        return False
    return True

def api_requestPeering(user_id, username, message):
    user = User.get_or_create(user_id)
    if not user.info:
        user.info = {}
    if not user.peered:
        if user.pending == 'sent':
            user.info['message'] = message
            user.update_peering(True, username)
            user.update_name()
        else:
            user.pending = 'received'
            user.info['username'] = username
            user.info['message'] = message
            user.update_name()
        user.save()
        trigger_event('peering.request', user.json())
        return True
    return False

def api_acceptPeering(user_id, username, message):
    user = User.get(user_id)
    logger.debug('incoming acceptPeering event: pending: %s', user.pending)
    if user and user.pending == 'sent':
        if not user.info:
            user.info = {}
        user.info['username'] = username
        user.info['message'] = message
        user.update_name()
        user.update_peering(True, username)
        state.nodes.queue('add', user.id)
        trigger_event('peering.accept', user.json())
        return True
    elif user and user.peered:
        return True
    return False

def api_rejectPeering(user_id, message):
    user = User.get(user_id)
    if user:
        if not user.info:
            user.info = {}
        user.info['message'] = message
        user.update_peering(False)
        trigger_event('peering.reject', user.json())
        return True
    return False

def api_removePeering(user_id, message):
    user = User.get(user_id)
    if user:
        user.info['message'] = message
        user.update_peering(False)
        trigger_event('peering.remove', user.json())
        return True
    return False

def api_cancelPeering(user_id, message):
    user = User.get(user_id)
    if user:
        user.info['message'] = message
        user.update_peering(False)
        trigger_event('peering.cancel', user.json())
        return True
    return False
