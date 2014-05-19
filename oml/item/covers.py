# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division, with_statement

import sqlite3
from StringIO import StringIO
import Image

import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.concurrent

from oxtornado import run_async

from utils import resize_image


from settings import covers_db_path

class Covers(dict):
    def __init__(self, db):
        self._db = db
        self.create()

    def connect(self):
        conn = sqlite3.connect(self._db, timeout=10)
        return conn

    def create(self):
        conn = self.connect()
        c = conn.cursor()
        c.execute(u'CREATE TABLE IF NOT EXISTS cover (id varchar(64) unique, data blob)')
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
        sql = u'SELECT data FROM cover WHERE id=?'
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
        sql = u'INSERT OR REPLACE INTO cover values (?, ?)'
        conn = self.connect()
        c = conn.cursor()
        data = sqlite3.Binary(data)
        c.execute(sql, (id, data))
        conn.commit()
        c.close()
        conn.close()

    def __delitem__(self, id):
        sql = u'DELETE FROM cover WHERE id = ?'
        conn = self.connect()
        c = conn.cursor()
        c.execute(sql, (id, ))
        conn.commit()
        c.close()
        conn.close()

covers = Covers(covers_db_path)

@run_async
def get_cover(app, id, size, callback):
    with app.app_context():
        from item.models import Item
        item = Item.get(id)
        if not item:
            callback('')
        else:
            data = None
            if size:
                data = covers['%s:%s' % (id, size)]
                if data:
                    size = None
            if not data:
                data = covers[id]
            if not data:
                data = item.update_cover()
                if not data:
                    data = covers.black()
            if size:
                data = covers['%s:%s' % (id, size)] = resize_image(data, size=size)
            data = str(data)
            if not 'coverRatio' in item.info:
                img = Image.open(StringIO(data))
                item.info['coverRatio'] = img.size[0]/img.size[1]
                item.save()
            data = data or ''
            callback(data)

class CoverHandler(tornado.web.RequestHandler):

    def initialize(self, app):
        self._app = app

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self, id, size=None):
        size = int(size) if size else None
        response = yield tornado.gen.Task(get_cover, self._app, id, size)
        if not response:
            self.set_status(404)
            self.write('')
        else:
            self.set_header('Content-Type', 'image/jpeg')
            self.write(response)
        self.finish()
