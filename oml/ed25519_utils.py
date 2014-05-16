# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import ed25519
ENCODING='base64'

def valid(key, value, sig):
    '''
    validate that value was signed by key
    '''
    vk = ed25519.VerifyingKey(str(key), encoding=ENCODING)
    try:
        vk.verify(str(sig), str(value), encoding=ENCODING)
    #except ed25519.BadSignatureError:
    except:
        return False
    return True
