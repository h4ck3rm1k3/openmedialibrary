# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division, print_function

import os
import sys

from tornado.web import StaticFileHandler, Application
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

import settings
import websocket
import logging

import db
import state
import node.server
import oxtornado
from cache import Cache
import tasks

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
    #FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
    #logging.basicConfig(format=FORMAT)
    #logger = logging.getLogger('oml.app')
    #logger.warning('test')
    if not PID:
        logging.basicConfig(level=logging.DEBUG)

    options = {
        'debug': False,
        'gzip': True
    }

    handlers = [
        (r'/(favicon.ico)', StaticFileHandler, {'path': static_path}),
        (r'/static/(.*)', StaticFileHandler, {'path': static_path}),
        (r'/(.*)/epub/(.*)', EpubHandler),
        (r'/(.*?)/reader/', ReaderHandler),
        (r'/(.*?)/pdf/', FileHandler),
        (r'/(.*?)/txt/', FileHandler),
        (r'/(.*)/(cover|preview)(\d*).jpg', IconHandler),
        (r'/api/', oxtornado.ApiHandler, dict(context=db.session)),
        (r'/ws', websocket.Handler),
        (r"(.*)", MainHandler),
    ]

    http_server = HTTPServer(Application(handlers, **options))

    http_server.listen(settings.server['port'], settings.server['address'])

    if PID:
        with open(PID, 'w') as pid:
            pid.write('%s' % os.getpid())

    state.main = IOLoop.instance()
    state.cache = Cache(ttl=10)
    state.tasks = tasks.Tasks()

    def start_node():
        import user
        import downloads
        import nodes
        import db
        state.node = node.server.start()
        state.nodes = nodes.Nodes()
        state.downloads = downloads.Downloads()
        def add_users():
            with db.session():
                for p in user.models.User.query.filter_by(peered=True):
                    state.nodes.queue('add', p.id)
        state.main.add_callback(add_users)
    state.main.add_callback(start_node)
    if ':' in settings.server['address']:
        host = '[%s]' % settings.server['address']
    elif not settings.server['address']:
        host = '[::1]'
    else:
        host = settings.server['address']
    url = 'http://%s:%s/' % (host, settings.server['port'])
    print('open browser at %s', url)
    try:
        state.main.start()
    except:
        print('shutting down...')

    if state.downloads:
        state.downloads.join()
    if state.tasks:
        state.tasks.join()
    if state.nodes:
        state.nodes.join()
