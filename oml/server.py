# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


import os
import sys
import signal
import time

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import StaticFileHandler, Application

from cache import Cache
from item.handlers import EpubHandler, ReaderHandler, FileHandler
from item.handlers import OMLHandler
from item.icons import IconHandler
import db
import node.server
import oxtornado
import settings
import setup
import state
import tasks
import websocket

import logging

class MainHandler(OMLHandler):

    def get(self, path):
        path = os.path.join(settings.static_path, 'html', 'oml.html')
        with open(path) as fd:
            content = fd.read()
        version = settings.MINOR_VERSION
        if version == 'git':
            version = int(time.mktime(time.gmtime()))
        content = content.replace('oml.js?1', 'oml.js?%s' % version)
        self.set_header('Content-Type', 'text/html')
        self.set_header('Content-Length', str(len(content)))
        self.write(content)

def run():
    setup.create_db()
    PID = sys.argv[2] if len(sys.argv) > 2 else None

    if not PID:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.DEBUG,
            filename=settings.log_path, filemode='w',
            format='%(asctime)s %(levelname)s %(message)s')
    options = {
        'debug': False,
        'gzip': True
    }

    handlers = [
        (r'/(favicon.ico)', StaticFileHandler, {'path': settings.static_path}),
        (r'/static/oxjs/(.*)', StaticFileHandler, {'path': os.path.join(settings.base_dir, '..', 'oxjs')}),
        (r'/static/epub.js/(.*)', StaticFileHandler, {'path': os.path.join(settings.base_dir, '..', 'reader', 'epub.js')}),
        (r'/static/pdf.js/(.*)', StaticFileHandler, {'path': os.path.join(settings.base_dir, '..', 'reader', 'pdf.js')}),
        (r'/static/txt.js/(.*)', StaticFileHandler, {'path': os.path.join(settings.base_dir, '..', 'reader', 'txt.js')}),
        (r'/static/(.*)', StaticFileHandler, {'path': settings.static_path}),
        (r'/(.*)/epub/(.*)', EpubHandler),
        (r'/(.*?)/reader/', ReaderHandler),
        (r'/(.*?)/pdf/', FileHandler),
        (r'/(.*?)/txt/', FileHandler),
        (r'/(.*?)/get/', FileHandler, {
            'download': True
        }),
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
        state.node = node.server.start()
        state.nodes = nodes.Nodes()
        state.downloads = downloads.Downloads()
        state.scraping = downloads.ScrapeThread()
        def add_users():
            with db.session():
                for p in user.models.User.query.filter_by(peered=True):
                    state.nodes.queue('add', p.id)
        state.main.add_callback(add_users)
    state.main.add_callback(start_node)
    if ':' in settings.server['address']:
        host = '[%s]' % settings.server['address']
    elif not settings.server['address']:
        host = '127.0.0.1'
    else:
        host = settings.server['address']
    url = 'http://%s:%s/' % (host, settings.server['port'])
    print('open browser at %s' % url)

    def shutdown():
        if state.downloads:
            state.downloads.join()
        if state.tasks:
            state.tasks.join()
        if state.nodes:
            state.nodes.join()
        if state.scraping:
            state.scraping.join()
        http_server.stop()
        if PID and os.path.exists(PID):
            os.unlink(PID)

    signal.signal(signal.SIGTERM, shutdown)

    try:
        state.main.start()
    except:
        print('shutting down...')
    shutdown()
