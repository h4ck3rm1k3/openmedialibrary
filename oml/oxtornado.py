# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division, with_statement

import inspect
import sys
import json
import datetime

import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.concurrent
from threading import Thread
from functools import wraps

import logging
logger = logging.getLogger('oxtornado')

import db

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

def run_async(func):
  @wraps(func)
  def async_func(*args, **kwargs):
    func_hl = Thread(target = func, args = args, kwargs = kwargs)
    func_hl.start()
    return func_hl

  return async_func

def trim(docstring):
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxint
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxint:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)


@run_async
def api_task(app, request, callback):
    action = request.arguments.get('action', [None])[0]
    data = request.arguments.get('data', ['{}'])[0]
    data = json.loads(data) if data else {}
    if not action:
        methods = actions.keys()
        api = []
        for f in sorted(methods):
            api.append({'name': f,
                        'doc': actions.doc(f).replace('\n', '<br>\n')})
        response = json_response(api)
    else:
        logger.debug('API %s %s', action, data)
        f = actions.get(action)
        if f:
            with db.session():
                try:
                    response = f(data)
                except:
                    logger.debug('FAILED %s %s', action, data, exc_info=1)
                    response = json_response(status=500, text='%s failed' % action)
        else:
            response = json_response(status=400, text='Unknown action %s' % action)
    callback(response)

class ApiHandler(tornado.web.RequestHandler):
    def initialize(self, app):
        self._app = app

    def get(self):
        self.write('use POST')

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        if 'origin' in self.request.headers and self.request.host not in self.request.headers['origin']:
            logger.debug('reject cross site attempt to access api %s', self.request)
            self.set_status(403)
            self.write('')
            return

        response = yield tornado.gen.Task(api_task, self._app, self.request)
        if not 'status' in response:
            response = json_response(response)
        response = json_dumps(response)
        self.set_header('Content-Type', 'application/json')
        self.write(response)

class ApiActions(dict):
    properties = {}
    versions = {}
    def __init__(self):

        def api(data):
            '''
                returns list of all known api actions
                takes {
                    docs: bool
                }
                if docs is true, action properties contain docstrings
                returns {
                    actions: {
                        'api': {
                            cache: true,
                            doc: 'recursion'
                        },
                        'hello': {
                            cache: true,
                            ..
                        }
                        ...
                    }
                }
            '''
            data = data or {}
            docs = data.get('docs', False)
            code = data.get('code', False)
            _actions = self.keys()
            _actions.sort()
            actions = {}
            for a in _actions:
                actions[a] = self.properties[a]
                if docs:
                    actions[a]['doc'] = self.doc(a)
                if code:
                    actions[a]['code'] = self.code(a)
            return {'actions': actions}
        self.register(api)

    def doc(self, name):
        f = self[name]
        return trim(f.__doc__)

    def code(self, name, version=None):
        f = self[name]
        if name != 'api' and hasattr(f, 'func_closure') and f.func_closure:
            fc = filter(lambda c: hasattr(c.cell_contents, '__call__'), f.func_closure)
            f = fc[len(fc)-1].cell_contents 
        info = f.func_code.co_filename
        info = u'%s:%s' % (info, f.func_code.co_firstlineno)
        return info, trim(inspect.getsource(f))

    def register(self, method, action=None, cache=True, version=None):
        if not action:
            action = method.func_name
        if version:
            if not version in self.versions:
                self.versions[version] = {}
            self.versions[version][action] = method
        else:
            self[action] = method
        self.properties[action] = {'cache': cache}

    def unregister(self, action):
        if action in self:
            del self[action]

actions = ApiActions()
