# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
# DHT placeholder
from __future__ import division

import logging

import requests
import ed25519
import json
import settings

logger = logging.getLogger('oml.directory')

base = settings.server['directory_service']

def get(vk):
    id = vk.to_ascii(encoding='base64')
    url ='%s/%s' % (base, id)
    headers = {
        'User-Agent': settings.USER_AGENT
    }
    r = requests.get(url, headers=headers)
    sig = r.headers.get('X-Ed25519-Signature')
    data = r.content
    if sig and data:
        vk = ed25519.VerifyingKey(id, encoding='base64')
        try:
            vk.verify(sig, data, encoding='base64')
            data = json.loads(data)
        except ed25519.BadSignatureError:
            logger.debug('invalid signature')

            data = None
    return data

def put(sk, data):
    id = sk.get_verifying_key().to_ascii(encoding='base64')
    data = json.dumps(data)
    sig = sk.sign(data, encoding='base64')
    url ='%s/%s' % (base, id)
    headers = {
        'User-Agent': settings.USER_AGENT,
        'X-Ed25519-Signature': sig
    }
    try:
        r = requests.put(url, data, headers=headers, timeout=2)
    except:
        import traceback
        logger.info('directory.put failed: %s', data)
        traceback.print_exc()
        return False
    return r.status_code == 200
