# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import sys

from tornado.web import StaticFileHandler, Application
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from app import app
import settings
import websocket

import state
import node.server
import oxtornado

from item.icons import IconHandler
from item.handlers import EpubHandler, ReaderHandler, FileHandler
from item.handlers import OMLHandler, serve_static

class MainHandler(OMLHandler):

    def get(self, path):
        path = os.path.join(settings.static_path, 'html/oml.html')
        serve_static(self, path, 'text/html')

def run():
    root_dir = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
    PID = sys.argv[2] if len(sys.argv) > 2 else None

    static_path = os.path.join(root_dir, 'static')

    options = {
        'debug': not PID 
    }

    handlers = [
        (r'/(favicon.ico)', StaticFileHandler, {'path': static_path}),
        (r'/static/(.*)', StaticFileHandler, {'path': static_path}),
        (r'/(.*)/epub/(.*)', EpubHandler, dict(app=app)),
        (r'/(.*?)/reader/', ReaderHandler, dict(app=app)),
        (r'/(.*?)/pdf/', FileHandler, dict(app=app)),
        (r'/(.*?)/txt/', FileHandler, dict(app=app)),
        (r'/(.*)/(cover|preview)(\d*).jpg', IconHandler, dict(app=app)),
        (r'/api/', oxtornado.ApiHandler, dict(app=app)),
        (r'/ws', websocket.Handler),
        (r"(.*)", MainHandler, dict(app=app)),
    ]

    http_server = HTTPServer(Application(handlers, **options))

    http_server.listen(settings.server['port'], settings.server['address'])

    if PID:
        with open(PID, 'w') as pid:
            pid.write('%s' % os.getpid())

    state.main = IOLoop.instance()

    def start_node():
        import user
        import downloads
        import nodes
        state.node = node.server.start(app)
        state.nodes = nodes.Nodes(app)
        state.downloads = downloads.Downloads(app)
        def add_users(app):
            with app.app_context():
                for p in user.models.User.query.filter_by(peered=True):
                    state.nodes.queue('add', p.id)
        state.main.add_callback(add_users, app)
    state.main.add_callback(start_node)
    if ':' in settings.server['address']:
        host = '[%s]' % settings.server['address']
    elif not settings.server['address']:
        host = '[::1]'
    else:
        host = settings.server['address']
    url = 'http://%s:%s/' % (host, settings.server['port'])
    print 'open browser at %s' % url
    state.main.start()
