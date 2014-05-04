import settings
from changelog import Changelog
from user.models import User

import state
from websocket import trigger_event

def api_pullChanges(app, remote_id, user_id=None, from_=None, to=None):
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

def api_pushChanges(app, user_id, changes):
    user = User.get(user_id)
    for change in changes:
        if not Changelog.apply_change(user, change):
            print 'FAILED TO APPLY CHANGE', change
            state.nodes.queue(user_id, 'pullChanges')
            return False
    return True

def api_requestPeering(app, user_id, username, message):
    user = User.get_or_create(user_id)
    if not user.info:
        user.info = {}
    if not user.peered:
        if user.pending == 'sent':
            user.info['message'] = message
            user.update_peering(True, username)
        else:
            user.pending = 'received'
            user.info['username'] = username
            user.info['message'] = message
        user.save()
        trigger_event('peering', user.json())
        return True
    return False

def api_acceptPeering(app, user_id, username, message):
    user = User.get(user_id)
    if user and user.pending == 'sent':
        if not user.info:
            user.info = {}
        user.info['username'] = username
        user.info['message'] = message
        user.update_peering(True, username)
        trigger_event('peering', user.json())
        return True
    return False

def api_rejectPeering(app, user_id, message):
    user = User.get(user_id)
    if user:
        if not user.info:
            user.info = {}
        user.info['message'] = message
        user.update_peering(False)
        trigger_event('peering', user.json())
        return True
    return False

def api_removePeering(app, user_id, message):
    user = User.get(user_id)
    if user:
        user.peered = False
        user.info['message'] = message
        user.save()
        trigger_event('peering', {'id': user.id, 'peered': user.peered})
        return True
    return False
