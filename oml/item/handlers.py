# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


from datetime import datetime
import mimetypes
import os
from urllib.request import quote
import zipfile

import ox

from .models import Item, File
from user.models import List
from .scan import add_file
import db
import settings
import tornado.web
import tornado.gen
import tornado.concurrent

from oxtornado import json_dumps, json_response

from media import get_id

import logging
logger = logging.getLogger('item.handlers')

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

def serve_static(handler, path, mimetype, include_body=True, disposition=None):
    handler.set_header('Content-Type', mimetype)
    size = os.stat(path).st_size
    handler.set_header('Accept-Ranges', 'bytes')
    if disposition:
        handler.set_header('Content-Disposition', "attachment; filename*=UTF-8''%s" % quote(disposition.encode('utf-8')))
    if include_body:
        if 'Range' in handler.request.headers:
            handler.set_status(206)
            r = handler.request.headers.get('Range').split('=')[-1].split('-')
            start = int(r[0])
            end = int(r[1]) if r[1] else size
            length = end - start + 1
            handler.set_header('Content-Length', str(length))
            handler.set_header('Content-Range', 'bytes %s-%s/%s' % (start, end, size))
            with open(path, 'rb') as fd:
                fd.seek(start)
                handler.write(fd.read(length))
        else:
            handler.set_header('Content-Length', str(size))
            with open(path, 'rb') as fd:
                handler.write(fd.read())
    else:
        handler.set_header('Content-Length', str(size))
    return

class FileHandler(OMLHandler):

    def initialize(self, attachment=False):
        self._attachment = attachment

    def head(self, id):
        self.get(id, include_body=False)

    def get(self, id, include_body=True):
        with db.session():
            item = Item.get(id)
            path = item.get_path() if item else None
            if not item or not path:
                self.set_status(404)
                return
            mimetype = {
                'cbr': 'application/x-cbr',
                'cbz': 'application/x-cbz',
                'epub': 'application/epub+zip',
                'pdf': 'application/pdf',
                'txt': 'text/plain',
            }.get(path.split('.')[-1], None)
            if mimetype == 'text/plain':
                try:
                    open(path, 'rb').read().decode('utf-8')
                    mimetype = 'text/plain; charset=utf-8'
                except:
                    mimetype = 'text/plain; charset=latin-1'
            if self._attachment:
                disposition = os.path.basename(path)
            else:
                disposition = None
            return serve_static(self, path, mimetype, include_body, disposition=disposition)

class ReaderHandler(OMLHandler):

    def get(self, id):
        with db.session():
            item = Item.get(id)
            if not item:
                self.set_status(404)
                return
            if item.info['extension'] in ('cbr', 'cbz'):
                html = 'html/cbr.html'
            elif item.info['extension'] == 'epub':
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

class UploadHandler(tornado.web.RequestHandler):

    def initialize(self, context=None):
        self._context = context

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
        def save_files(context, request, callback):
            listname = request.arguments.get('list', None)
            if listname:
                listname = listname[0]
                if isinstance(listname, bytes):
                    listname = listname.decode('utf-8')
            with context():
                prefs = settings.preferences
                ids = []
                for upload in request.files.get('files', []):
                    filename = upload.filename
                    id = get_id(data=upload.body)
                    ids.append(id)
                    file = File.get(id)
                    if not file:
                        prefix_books = os.path.join(os.path.expanduser(prefs['libraryPath']), 'Books/')
                        prefix_imported = os.path.join(prefix_books, 'Imported/')
                        ox.makedirs(prefix_imported)
                        import_name = os.path.join(prefix_imported, filename)
                        n = 1
                        while os.path.exists(import_name):
                            n += 1
                            name, extension = filename.rsplit('.', 1)
                            import_name = os.path.join(prefix_imported, '%s [%d].%s' % (name, n, extension))
                        with open(import_name, 'wb') as fd:
                            fd.write(upload.body)
                        file = add_file(id, import_name, prefix_books)
            if listname and ids:
                l = List.get(settings.USER_ID, listname)
                if l:
                    l.add_items(ids)
            response = json_response({'ids': ids})
            callback(response)

        response = yield tornado.gen.Task(save_files, self._context, self.request)
        if not 'status' in response:
            response = json_response(response)
        response = json_dumps(response)
        self.set_header('Content-Type', 'application/json')
        self.write(response)
