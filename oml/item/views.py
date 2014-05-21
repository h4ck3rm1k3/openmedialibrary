# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

from datetime import datetime

from flask import Blueprint
from flask import abort, send_file

import settings

from models import Item

app = Blueprint('item', __name__, static_folder=settings.static_path)


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
    item.accessed = datetime.utcnow()
    item.timesaccessed = (item.timesaccessed or 0) + 1
    item.update_sort()
    item.save()
    return app.send_static_file(html)
