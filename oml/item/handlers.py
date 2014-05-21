# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division, with_statement

import os
import zipfile
import mimetypes
from datetime import datetime

import tornado.web
from models import Item
import settings

class OMLHandler(tornado.web.RequestHandler):

    def initialize(self, app):
        self._app = app

class EpubHandler(OMLHandler):

    def get(self, id, filename):
        with self._app.app_context():
            item = Item.get(id)
            path = item.get_path()
            if not item or item.info['extension'] != 'epub' or not path:
                self.set_status(404)
                self.write('')
            else:
                z = zipfile.ZipFile(path)
                if filename == '':
                    self.write('<br>\n'.join([f.filename for f in z.filelist]))
                elif filename not in [f.filename for f in z.filelist]:
                    self.set_status(404)
                    self.write('')
                else:
                    content_type = {
                        'xpgt': 'application/vnd.adobe-page-template+xml'
                    }.get(filename.split('.')[0], mimetypes.guess_type(filename)[0]) or 'text/plain'
                    self.set_header('Content-Type', content_type)
                    self.write(z.read(filename))
            self.finish()

def serve_static(handler, path, mimetype):
    #fixme use static file handler
    handler.set_header('Content-Type', mimetype)
    with open(path) as fd:
        handler.write(fd.read())
    handler.finish()
    return

class FileHandler(OMLHandler):

    def get(self, id):
        with self._app.app_context():
            item = Item.get(id)
            if not item:
                self.set_status(404)
                self.finish()
                return
            path = item.get_path()
            mimetype={
                'epub': 'application/epub+zip',
                'pdf': 'application/pdf',
            }.get(path.split('.')[-1], None)
            return serve_static(self, path, mimetype)

class ReaderHandler(OMLHandler):

    def get(self, id):
        with self._app.app_context():
            item = Item.get(id)
            if not item:
                self.set_status(404)
                self.finish()
                return
            if item.info['extension'] == 'epub':
                html = 'html/epub.html'
            elif item.info['extension'] == 'pdf':
                html = 'html/pdf.html'
            elif item.info['extension'] == 'txt':
                html = 'html/txt.html'
            else:
                self.set_status(404)
                self.finish()
                return
            item.accessed = datetime.utcnow()
            item.timesaccessed = (item.timesaccessed or 0) + 1
            item.update_sort()
            item.save()
            return serve_static(self, os.path.join(settings.static_path, html), 'text/html')
