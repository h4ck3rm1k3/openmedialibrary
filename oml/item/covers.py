# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import sqlite3
import Image
from StringIO import StringIO

from settings import covers_db_path

class Covers(dict):
    def __init__(self, db):
        self._db = db

    def connect(self):
        self.conn = sqlite3.connect(self._db, timeout=10)
        self.create()

    def create(self):
        c = self.conn.cursor()
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
        self.connect()
        c = self.conn.cursor()
        c.execute(sql, (id, ))
        data = default
        for row in c:
            data = row[0]
            break
        c.close()
        self.conn.close()
        return data

    def __setitem__(self, id, data):
        sql = u'INSERT OR REPLACE INTO cover values (?, ?)'
        self.connect()
        c = self.conn.cursor()
        data = sqlite3.Binary(data)
        c.execute(sql, (id, data))
        self.conn.commit()
        c.close()
        self.conn.close()

    def __delitem__(self, id):
        sql = u'DELETE FROM cover WHERE id = ?'
        self.connect()
        c = self.conn.cursor()
        c.execute(sql, (id, ))
        self.conn.commit()
        c.close()
        self.conn.close()

covers = Covers(covers_db_path)
