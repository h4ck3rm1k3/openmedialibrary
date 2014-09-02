# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


from datetime import datetime
import mimetypes
import os
import zipfile

from .models import Item
import db
import settings
import tornado.web


class OMLHandler(tornado.web.RequestHandler):

    def initialize(self):
        pass

class EpubHandler(OMLHandler):

    def get(self, id, filename):
        with db.session():
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

def serve_static(handler, path, mimetype, include_body=True):
    #fixme use static file handler / serve ranges
    handler.set_header('Content-Type', mimetype)
    handler.set_header('Content-Length', str(os.stat(path).st_size))
    if include_body:
        with open(path, 'rb') as fd:
            handler.write(fd.read())
    return

class FileHandler(OMLHandler):

    def head(self, id):
        self.get(id, include_body=False)

    def get(self, id, include_body=True):
        with db.session():
            item = Item.get(id)
            path = item.get_path() if item else None
            if not item or not path:
                self.set_status(404)
                return
            mimetype={
                'epub': 'application/epub+zip',
                'pdf': 'application/pdf',
                'txt': 'text/plain',
            }.get(path.split('.')[-1], None)
            return serve_static(self, path, mimetype, include_body)

class ReaderHandler(OMLHandler):

    def get(self, id):
        with db.session():
            item = Item.get(id)
            if not item:
                self.set_status(404)
                return
            if item.info['extension'] == 'epub':
                html = 'html/epub.html'
            elif item.info['extension'] == 'pdf':
                html = 'html/pdf.html'
            elif item.info['extension'] == 'txt':
                html = 'html/txt.html'
            else:
                self.set_status(404)
                return
            item.accessed = datetime.utcnow()
            item.timesaccessed = (item.timesaccessed or 0) + 1
            item.update_sort()
            item.save()
            return serve_static(self, os.path.join(settings.static_path, html), 'text/html')
