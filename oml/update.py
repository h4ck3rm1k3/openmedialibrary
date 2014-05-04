#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


from __future__ import division
#https://github.com/hiroakis/tornado-websocket-example/blob/master/app.py
#http://stackoverflow.com/questions/5892895/tornado-websocket-question

#possibly get https://github.com/methane/wsaccel


#possibly run the full django app throw tornado instead of gunicorn
#https://github.com/bdarnell/django-tornado-demo/blob/master/testsite/tornado_main.py
#http://stackoverflow.com/questions/7190431/tornado-with-django
#http://www.tornadoweb.org/en/stable/wsgi.html


from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.websocket import WebSocketHandler
from Queue import Queue
import urllib2
import os
from contextlib import closing
import json
from threading import Thread


class Background:

    def __init__(self, handler):
        self.handler = handler
        self.q = Queue()

    def worker(self):
        while True:
            message = self.q.get()
            action, data = json.loads(message)
            if action == 'get':
                if 'url' in data and data['url'].startswith('http'):
                    self.download(data['url'], '/tmp/test.data')
            elif action == 'update':
                self.post({'error': 'not implemented'})
            else:
                self.post({'error': 'unknown action'})
            self.q.task_done()

    def join(self):
        self.q.join()

    def put(self, data):
        self.q.put(data)

    def post(self, data):
        if not isinstance(data, basestring):
            data = json.dumps(data)
        main.add_callback(lambda: self.handler.write_message(data))

    def download(self, url, filename):
        dirname = os.path.dirname(filename)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filename, 'w') as f:
            with closing(urllib2.urlopen(url)) as u:
                size = int(u.headers.get('content-length', 0))
                done = 0
                chunk_size = max(min(1024*1024, int(size/100)), 4096)
                print 'chunksize', chunk_size
                for data in iter(lambda: u.read(chunk_size), ''):
                    f.write(data)
                    done += len(data)
                    if size:
                        percent = done/size
                    self.post({'url': url, 'size': size, 'done': done, 'percent': percent})

class Handler(WebSocketHandler):
    def open(self):
        print "New connection opened."
        self.background = Background(self)
        self.t = Thread(target=self.background.worker)
        self.t.daemon = True
        self.t.start()

    #websocket calls
    def on_message(self, message):
        self.background.put(message)

    def on_close(self):
        print "Connection closed."
        self.background.join()

print "Server started."
HTTPServer(Application([("/", Handler)])).listen(28161)
main = IOLoop.instance()
main.start()
