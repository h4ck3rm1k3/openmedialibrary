# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

from flask import Flask
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
import logging


import oxflask.api

import settings
from settings import db

import changelog
import item.models
import user.models
import item.person

import item.api
import user.api

import item.views
import commands

#FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
#logging.basicConfig(format=FORMAT)
#logger = logging.getLogger('oml.app')
#logger.warning('test')
logging.basicConfig(level=logging.DEBUG)

app = Flask('openmedialibrary', static_folder=settings.static_path)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////%s' % settings.db_path
app.register_blueprint(oxflask.api.app)
app.register_blueprint(item.views.app)
db.init_app(app)

migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)
manager.add_command('setup', commands.Setup)
manager.add_command('update_static', commands.UpdateStatic)
manager.add_command('release', commands.Release)

@app.route('/')
@app.route('/<path:path>')
def main(path=None):
    return app.send_static_file('html/oml.html')

