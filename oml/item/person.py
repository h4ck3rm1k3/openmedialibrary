# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import unicodedata

import ox

import db
import sqlalchemy as sa

def get_sort_name(name, sortname=None):
    name = unicodedata.normalize('NFKD', name).strip()
    if name:
        person = Person.get(name)
        if not person:
            person = Person(name=name, sortname=sortname)
            person.save()
        sortname = unicodedata.normalize('NFKD', person.sortname)
    else:
        sortname = u''
    return sortname

class Person(db.Model):
    __tablename__ = 'person'

    name = sa.Column(sa.String(1024), primary_key=True)
    sortname = sa.Column(sa.String())
    numberofnames = sa.Column(sa.Integer())

    def __repr__(self):
        return self.name

    @classmethod
    def get(cls, name):
        return cls.query.filter_by(name=name).first()

    def save(self):
        if not self.sortname:
            self.sortname = ox.get_sort_name(self.name)
            self.sortname = unicodedata.normalize('NFKD', self.sortname)
        self.sortsortname = ox.sort_string(self.sortname)
        self.numberofnames = len(self.name.split(' '))
        db.session.add(self)
        db.session.commit()

