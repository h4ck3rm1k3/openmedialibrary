# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

from flask.ext.sqlalchemy import SQLAlchemy
import json
import os
import ed25519

from pdict import pdict

base_dir = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
static_path = os.path.join(base_dir, 'static')
updates_path = os.path.join(base_dir, 'updates')

oml_config_path = os.path.join(base_dir, 'config.json')

config_dir = os.path.normpath(os.path.join(base_dir, '..', 'config'))
if not os.path.exists(config_dir):
    os.makedirs(config_dir)

db_path = os.path.join(config_dir, 'data.db')
icons_db_path = os.path.join(config_dir, 'icons.db')
key_path = os.path.join(config_dir, 'node.key')
ssl_cert_path = os.path.join(config_dir, 'node.ssl.crt')
ssl_key_path = os.path.join(config_dir, 'node.ssl.key')

db = SQLAlchemy()

if os.path.exists(oml_config_path):
    with open(oml_config_path) as fd:
        config = json.load(fd)
else:
    config = {}

preferences = pdict(os.path.join(config_dir, 'preferences.json'), config['user']['preferences'])
ui = pdict(os.path.join(config_dir, 'ui.json'), config['user']['ui'])

server = pdict(os.path.join(config_dir, 'server.json'))
server_defaults = {
    'port': 9842,
    'address': '::1',
    'node_port': 9851,
    'node_address': '',
    'extract_text': True,
    'localnode_discovery': True,
    'directory_service': 'http://[2a01:4f8:120:3201::3]:25519',
    'meta_service': 'http://meta.openmedialibrary.com/api/',
}

for key in server_defaults:
    if key not in server:
        server[key] = server_defaults[key]

release = pdict(os.path.join(config_dir, 'release.json'))

if os.path.exists(key_path):
    with open(key_path) as fd:
        sk = ed25519.SigningKey(fd.read())
        vk = sk.get_verifying_key()
else:
    sk, vk = ed25519.create_keypair()
    with open(key_path, 'w') as fd:
        os.chmod(key_path, 0600)
        fd.write(sk.to_bytes())
        os.chmod(key_path, 0400)

USER_ID = vk.to_ascii(encoding='base64')

if 'modules' in release and 'openmedialibrary' in release['modules']:
    MINOR_VERSION = release['modules']['openmedialibrary']['version']
else:
    MINOR_VERSION = 'git'

NODE_PROTOCOL="0.1"
VERSION="%s.%s" % (NODE_PROTOCOL, MINOR_VERSION)


USER_AGENT = 'OpenMediaLibrary/%s' % VERSION
