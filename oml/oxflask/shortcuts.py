from functools import wraps
import datetime
import json

from flask import Response

def json_response(data=None, status=200, text='ok'):
    if not data:
        data = {}
    return {'status': {'code': status, 'text': text}, 'data': data}

def _to_json(python_object):
    if isinstance(python_object, datetime.datetime):
        if python_object.year < 1900:
            tt = python_object.timetuple()
            return '%d-%02d-%02dT%02d:%02d%02dZ' % tuple(list(tt)[:6])
        return python_object.strftime('%Y-%m-%dT%H:%M:%SZ')
    raise TypeError(u'%s %s is not JSON serializable' % (repr(python_object), type(python_object)))

def json_dumps(obj):
    indent = 2
    return json.dumps(obj, indent=indent, default=_to_json, ensure_ascii=False).encode('utf-8')

def render_to_json_response(obj, content_type="text/json", status=200):
    resp = Response(json_dumps(obj), status=status, content_type=content_type)
    return resp

def returns_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        r = f(*args, **kwargs)
        return render_to_json_response(json_response(r))
    return decorated_function

