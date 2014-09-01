# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division, with_statement

from StringIO import StringIO
from PIL import Image
import sqlite3

import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.web

from oxtornado import run_async
from settings import icons_db_path
from utils import resize_image
import db

import logging
logger = logging.getLogger('oml.item.icons')


class Icons(dict):
    def __init__(self, db):
        self._db = db
        self.create()

    def connect(self):
        conn = sqlite3.connect(self._db, timeout=10)
        return conn

    def create(self):
        conn = self.connect()
        c = conn.cursor()
        c.execute(u'CREATE TABLE IF NOT EXISTS icon (id varchar(64) unique, data blob)')
        c.execute(u'CREATE TABLE IF NOT EXISTS setting (key varchar(256) unique, value text)')
        if int(self.get_setting(c, 'version', 0)) < 1:
            self.set_setting(c, 'version', 1)

    def get_setting(self, c, key, default=None):
        c.execute(u'SELECT value FROM setting WHERE key = ?', (key, ))
        for row in c:
            return row[0]
        return default

    def set_setting(self, c, key, value):
        c.execute(u'INSERT OR REPLACE INTO setting values (?, ?)', (key, str(value)))

    def black(self):
        img = Image.new('RGB', (80, 128))
        o = StringIO()
        img.save(o, format='jpeg')
        data = o.getvalue()
        o.close()
        return data

    def __getitem__(self, id, default=None):
        sql = u'SELECT data FROM icon WHERE id=?'
        conn = self.connect()
        c = conn.cursor()
        c.execute(sql, (id, ))
        data = default
        for row in c:
            data = row[0]
            break
        c.close()
        conn.close()
        return data

    def __setitem__(self, id, data):
        sql = u'INSERT OR REPLACE INTO icon values (?, ?)'
        conn = self.connect()
        c = conn.cursor()
        data = sqlite3.Binary(data)
        c.execute(sql, (id, data))
        conn.commit()
        c.close()
        conn.close()

    def __delitem__(self, id):
        sql = u'DELETE FROM icon WHERE id = ?'
        conn = self.connect()
        c = conn.cursor()
        c.execute(sql, (id, ))
        conn.commit()
        c.close()
        conn.close()

icons = Icons(icons_db_path)

@run_async
def get_icon(id, type_, size, callback):
    if size:
        skey = '%s:%s:%s' % (type_, id, size)
        data = icons[skey]
        if data:
            callback(str(data))
            return
    key = '%s:%s' % (type_, id)
    data = icons[key]
    if not data:
        type_ = 'preview' if type_ == 'cover' else 'cover'
        key = '%s:%s' % (type_, id)
    if size:
        skey = '%s:%s:%s' % (type_, id, size)
    if size:
        data = icons[skey]
        if data:
            size = None
    if not data:
        data = icons[key]
    if not data:
        data = icons.black()
        size = None
    if size:
        data = icons[skey] = resize_image(data, size=size)
    data = str(data) or ''
    callback(data)

@run_async
def get_icon_app(id, type_, size, callback):
    with db.session():
        from item.models import Item
        item = Item.get(id)
        if not item:
            callback('')
        else:
            if type_ == 'cover' and not item.meta.get('cover'):
                type_ = 'preview'
            if type_ == 'preview' and not item.files.count():
                type_ = 'cover'
            if size:
                skey = '%s:%s:%s' % (type_, id, size)
            key = '%s:%s' % (type_, id)
            data = None
            if size:
                data = icons[skey]
                if data:
                    size = None
            if not data:
                data = icons[key]
            if not data:
                data = icons.black()
                size = None
            if size:
                data = icons[skey] = resize_image(data, size=size)
            data = str(data) or ''
            callback(data)

class IconHandler(tornado.web.RequestHandler):

    def initialize(self):
        pass

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self, id, type_, size=None):

        size = int(size) if size else None

        if type_ not in ('cover', 'preview'):
            self.set_status(404)
            return

        self.set_header('Content-Type', 'image/jpeg')

        response = yield tornado.gen.Task(get_icon, id, type_, size)
        if not response:
            self.set_status(404)
            return
        if self._finished:
            return
        self.write(response)
