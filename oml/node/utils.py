import socket
import requests
from urlparse import urlparse

def get_public_ipv6():
    host = ('2a01:4f8:120:3201::3', 25519)
    s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    s.connect(host)
    ip = s.getsockname()[0]
    s.close()
    return ip

def get_public_ipv4():
    host = ('10.0.3.1', 25519)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(host)
    ip = s.getsockname()[0]
    s.close()
    return ip
