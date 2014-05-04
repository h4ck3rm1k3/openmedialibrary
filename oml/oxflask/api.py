# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division, with_statement
import inspect
import sys
import json

from flask import request, Blueprint
from .shortcuts import render_to_json_response, json_response

app = Blueprint('oxflask', __name__)

@app.route('/api/', methods=['POST', 'OPTIONS'])
def api():
    if request.method == "OPTIONS":
        response = render_to_json_response({'status': {'code': 200, 'text': 'use POST'}})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    if not 'action' in request.form:
        methods = actions.keys()
        api = []
        for f in sorted(methods):
            api.append({'name': f,
                        'doc': actions.doc(f).replace('\n', '<br>\n')})
        return render_to_json_response(api)
    action = request.form['action']
    f = actions.get(action)
    if f:
        response = f(request)
    else:
        response = render_to_json_response(json_response(status=400,
                                text='Unknown action %s' % action))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

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


class ApiActions(dict):
    properties = {}
    versions = {}
    def __init__(self):

        def api(request):
            '''
                returns list of all known api actions
                param data {
                    docs: bool
                }
                if docs is true, action properties contain docstrings
                return {
                    status: {'code': int, 'text': string},
                    data: {
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
                }
            '''
            data = json.loads(request.form.get('data', '{}'))
            docs = data.get('docs', False)
            code = data.get('code', False)
            version = getattr(request, 'version', None)
            if version:
                _actions = self.versions.get(version, {}).keys()
                _actions = list(set(_actions + self.keys()))
            else:
                _actions = self.keys()
            _actions.sort()
            actions = {}
            for a in _actions:
                actions[a] = self.properties[a]
                if docs:
                    actions[a]['doc'] = self.doc(a, version)
                if code:
                    actions[a]['code'] = self.code(a, version)
            response = json_response({'actions': actions})
            return render_to_json_response(response)
        self.register(api)

    def doc(self, name, version=None):
        if version:
            f = self.versions[version].get(name, self.get(name))
        else:
            f = self[name]
        return trim(f.__doc__)

    def code(self, name, version=None):
        if version:
            f = self.versions[version].get(name, self.get(name))
        else:
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

def error(request):
    '''
     this action is used to test api error codes, it should return a 503 error
    '''
    success = error_is_success
    return render_to_json_response({})
actions.register(error)
