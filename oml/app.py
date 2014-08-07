# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

from flask import Flask
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand
import logging



import settings
from settings import db

import changelog
import item.models
import user.models
import item.person

import api

import commands

app = Flask('openmedialibrary', static_folder=settings.static_path)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////%s' % settings.db_path
db.init_app(app)

migrate = Migrate(app, db)

manager = Manager(app, with_default_commands=False)
manager.add_command('db', MigrateCommand)
manager.add_command('release', commands.Release)
manager.add_command('debug', commands.Debug)
manager.add_command('update', commands.Update)
manager.add_command('install_update', commands.InstallUpdate)
manager.add_command('start', commands.Start)
manager.add_command('stop', commands.Stop)
manager.add_command('setup', commands.Setup)
manager.add_command('version', commands.Version)
manager.add_command('postupdate', commands.PostUpdate)
manager.add_command('shell', Shell)
manager.add_command('update_static', commands.UpdateStatic)

@app.route('/')
@app.route('/<path:path>')
def main(path=None):
    return app.send_static_file('html/oml.html')

