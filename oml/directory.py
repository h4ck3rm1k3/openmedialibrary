# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
# DHT placeholder


import logging

import ed25519
import json
import tor_request

import settings

logger = logging.getLogger(__name__)

base = settings.server['directory_service']
base = 'http://hpjats6xixrleoqg.onion:25519'

def get(vk):
    id = vk.to_ascii(encoding='base64').decode()
    url = '%s/%s' % (base, id)
    headers = {
        'User-Agent': settings.USER_AGENT
    }
    try:
        opener = tor_request.get_opener()
        opener.addheaders = list(zip(headers.keys(), headers.values()))
        r = opener.open(url)
    except:
        logger.info('get failed %s', url, exc_info=1)
        return None
    sig = r.headers.get('X-Ed25519-Signature')
    data = r.read()
    if sig and data:
        vk = ed25519.VerifyingKey(id, encoding='base64')
        try:
            vk.verify(sig, data, encoding='base64')
            data = json.loads(data.decode('utf-8'))
        except ed25519.BadSignatureError:
            logger.debug('invalid signature')

            data = None
    return data

def put(sk, data):
    id = sk.get_verifying_key().to_ascii(encoding='base64').decode()
    data = json.dumps(data).encode()
    sig = sk.sign(data, encoding='base64')
    url ='%s/%s' % (base, id)
    headers = {
        'User-Agent': settings.USER_AGENT,
        'X-Ed25519-Signature': sig
    }
    try:
        #r = requests.put(url, data, headers=headers, timeout=2)
        opener = tor_request.get_opener()
        opener.addheaders = list(zip(headers.keys(), headers.values()))
        r = opener.open(url, data)
    except:
        logger.info('put failed: %s', data, exc_info=1)
        return False
    return r.status == 200
