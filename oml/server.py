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
from item.handlers import OMLHandler, UploadHandler
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

logger = logging.getLogger(__name__)

class MainHandler(OMLHandler):

    def get(self, path):
        path = os.path.join(settings.static_path, 'html', 'oml.html')
        with open(path) as fd:
            content = fd.read()
        version = settings.MINOR_VERSION.split('-')[0]
        if version == 'git':
            version = int(time.mktime(time.gmtime()))
        content = content.replace('oml.js?1', 'oml.js?%s' % version)
        self.set_header('Content-Type', 'text/html')
        self.set_header('Content-Length', str(len(content)))
        self.write(content)

def log_request(handler):
    if settings.DEBUG_HTTP:
        if handler.get_status() < 400:
            log_method = logger.info
        elif handler.get_status() < 500:
            log_method = logger.warning
        else:
            log_method = logger.error
        request_time = 1000.0 * handler.request.request_time()
        log_method("%d %s %.2fms", handler.get_status(),
                   handler._request_summary(), request_time)

def run():
    setup.create_db()
    PID = sys.argv[2] if len(sys.argv) > 2 else None

    log_format='%(asctime)s:%(levelname)s:%(name)s:%(message)s'
    if not PID:
        logging.basicConfig(level=logging.DEBUG, format=log_format)
    else:
        logging.basicConfig(level=logging.DEBUG,
            filename=settings.log_path, filemode='w',
            format=log_format)
    options = {
        'debug': False,
        'log_function': log_request,
        'gzip': True
    }

    handlers = [
        (r'/(favicon.ico)', StaticFileHandler, {'path': settings.static_path}),
        (r'/static/oxjs/(.*)', StaticFileHandler, {'path': os.path.join(settings.base_dir, '..', 'oxjs')}),
        (r'/static/cbr.js/(.*)', StaticFileHandler, {'path': os.path.join(settings.base_dir, '..', 'reader', 'cbr.js')}),
        (r'/static/epub.js/(.*)', StaticFileHandler, {'path': os.path.join(settings.base_dir, '..', 'reader', 'epub.js')}),
        (r'/static/pdf.js/(.*)', StaticFileHandler, {'path': os.path.join(settings.base_dir, '..', 'reader', 'pdf.js')}),
        (r'/static/txt.js/(.*)', StaticFileHandler, {'path': os.path.join(settings.base_dir, '..', 'reader', 'txt.js')}),
        (r'/static/(.*)', StaticFileHandler, {'path': settings.static_path}),
        (r'/(.*)/epub/(.*)', EpubHandler),
        (r'/(.*?)/reader/', ReaderHandler),
        (r'/(.*?)/cbr/', FileHandler),
        (r'/(.*?)/pdf/', FileHandler),
        (r'/(.*?)/txt/', FileHandler),
        (r'/(.*?)/get/', FileHandler, {
            'attachment': True
        }),
        (r'/(.*)/(cover|preview)(\d*).jpg', IconHandler),
        (r'/api/upload/', UploadHandler, dict(context=db.session)),
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
        import downloads
        import nodes
        import tor
        import bandwidth
        state.bandwidth = bandwidth.Bandwidth()
        state.tor = tor.Tor()
        state.node = node.server.start()
        state.downloads = downloads.Downloads()
        state.scraping = downloads.ScrapeThread()
        state.nodes = nodes.Nodes()
        def publish():
            if not state.tor.is_online():
                state.main.call_later(1, publish)
            else:
                nodes.publish_node()
        state.main.add_callback(publish)
    state.main.add_callback(start_node)
    if ':' in settings.server['address']:
        host = '[%s]' % settings.server['address']
    elif not settings.server['address']:
        host = '127.0.0.1'
    else:
        host = settings.server['address']
    url = 'http://%s:%s/' % (host, settings.server['port'])
    print('open browser at %s' % url)
    logger.debug('Starting OML %s at %s', settings.VERSION, url)

    def shutdown():
        if state.tor:
            state.tor._shutdown = True
        if state.downloads:
            logger.debug('shutdown downloads')
            state.downloads.join()
        if state.scraping:
            logger.debug('shutdown scraping')
            state.scraping.join()
        logger.debug('shutdown http_server')
        http_server.stop()
        if state.tasks:
            logger.debug('shutdown tasks')
            state.tasks.join()
        if state.nodes:
            logger.debug('shutdown nodes')
            state.nodes.join()
        if state.node:
            state.node.stop()
        if state.tor:
            logger.debug('shutdown tor')
            state.tor.shutdown()
        if PID and os.path.exists(PID):
            logger.debug('remove %s', PID)
            os.unlink(PID)

    signal.signal(signal.SIGTERM, shutdown)

    try:
        state.main.start()
    except:
        print('shutting down...')
    shutdown()
