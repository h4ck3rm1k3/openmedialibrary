# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

from datetime import datetime
import zipfile
import mimetypes
from StringIO import StringIO
import Image

from flask import Blueprint
from flask import make_response, abort, send_file
from covers import covers

import settings

from models import Item, db

from utils import resize_image

app = Blueprint('item', __name__, static_folder=settings.static_path)

@app.route('/<string:id>/epub/')
@app.route('/<string:id>/epub/<path:filename>')
def epub(id, filename=''):
    item = Item.get(id)
    if not item or item.info['extension'] != 'epub':
        abort(404)

    path = item.get_path()
    z = zipfile.ZipFile(path)
    if filename == '':
        return '<br>\n'.join([f.filename for f in z.filelist])
    if filename not in [f.filename for f in z.filelist]:
        abort(404)
    resp = make_response(z.read(filename))
    resp.content_type = {
        'xpgt': 'application/vnd.adobe-page-template+xml'
    }.get(filename.split('.')[0], mimetypes.guess_type(filename)[0]) or 'text/plain'
    return resp

@app.route('/<string:id>/get')
@app.route('/<string:id>/txt/')
@app.route('/<string:id>/pdf')
def get(id):
    item = Item.get(id)
    if not item:
        abort(404)
    path = item.get_path()
    mimetype={
        'epub': 'application/epub+zip',
        'pdf': 'application/pdf',
    }.get(path.split('.')[-1], None)
    return send_file(path, mimetype=mimetype)

@app.route('/<string:id>/reader/')
def reader(id, filename=''):
    item = Item.get(id)
    if item.info['extension'] == 'epub':
        html = 'html/epub.html'
    elif item.info['extension'] == 'pdf':
        html = 'html/pdf.html'
    elif item.info['extension'] == 'txt':
        html = 'html/txt.html'
    else:
        abort(404)
    item.sort_accessed = item.accessed = datetime.now()
    item.sort_timesaccessed = item.timesaccessed = (item.timesaccessed or 0) + 1
    item.save()
    return app.send_static_file(html)
