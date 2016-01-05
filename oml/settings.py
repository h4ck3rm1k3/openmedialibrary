# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import json
import os
import ed25519

from pdict import pdict
from utils import get_user_id

base_dir = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
static_path = os.path.join(base_dir, 'static')
updates_path = os.path.normpath(os.path.join(base_dir, '..', 'updates'))

oml_config_path = os.path.join(base_dir, 'config.json')

config_path = os.path.normpath(os.path.join(base_dir, '..', 'config'))
if not os.path.exists(config_path):
    os.makedirs(config_path)

db_path = os.path.join(config_path, 'data.db')
log_path = os.path.join(config_path, 'debug.log')
icons_db_path = os.path.join(config_path, 'icons.db')
key_path = os.path.join(config_path, 'node.key')
ssl_cert_path = os.path.join(config_path, 'node.ssl.crt')
ssl_key_path = os.path.join(config_path, 'tor', 'private_key')


if os.path.exists(oml_config_path):
    with open(oml_config_path) as fd:
        config = json.load(fd)
else:
    config = {}

preferences = pdict(os.path.join(config_path, 'preferences.json'), config['user']['preferences'])
ui = pdict(os.path.join(config_path, 'ui.json'), config['user']['ui'])
lists_cache = pdict(os.path.join(config_path, 'lists_cache.json'), {})

server = pdict(os.path.join(config_path, 'server.json'))
server_defaults = {
    'port': 9842,
    'address': '127.0.0.1',
    'node_port': 9851,
    'node_address': '',
    'extract_text': True,
    'localnode_discovery': True,
    'directory_service': 'http://[2a01:4f8:120:3201::3]:25519',
    'meta_service': 'http://meta.openmedialibrary.com/api/',
    'release_url': 'http://downloads.openmedialibrary.com/release.json',
}

for key in server_defaults:
    if key not in server:
        server[key] = server_defaults[key]

release = pdict(os.path.join(config_path, 'release.json'))

if os.path.exists(key_path):
    with open(key_path, 'rb') as fd:
        sk = ed25519.SigningKey(fd.read())
        vk = sk.get_verifying_key()
else:
    sk, vk = ed25519.create_keypair()
    with open(key_path, 'wb') as fd:
        os.chmod(key_path, 0o600)
        fd.write(sk.to_bytes())
        os.chmod(key_path, 0o400)

USER_ID = get_user_id(ssl_key_path, ssl_cert_path)
OLD_USER_ID = vk.to_ascii(encoding='base64').decode()

OML_UPDATE_KEY='K55EZpPYbP3X+3mA66cztlw1sSaUMqGwfTDKQyP2qOU'

if 'modules' in release and 'openmedialibrary' in release['modules']:
    MINOR_VERSION = release['modules']['openmedialibrary']['version']
else:
    MINOR_VERSION = 'git'

NODE_PROTOCOL="0.2"
VERSION="%s.%s" % (NODE_PROTOCOL, MINOR_VERSION)


USER_AGENT = 'OpenMediaLibrary/%s' % VERSION

DEBUG_HTTP = server.get('debug_http', False)
