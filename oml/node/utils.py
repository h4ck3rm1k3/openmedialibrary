# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import socket

def get_public_ipv6():
    host = ('2a01:4f8:120:3201::3', 25519)
    s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    s.connect(host)
    ip = s.getsockname()[0]
    s.close()
    return ip

