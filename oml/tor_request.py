# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import ssl
import http.client
import urllib.request, urllib.error, urllib.parse
import logging

import socks
import socket

import settings
import state
from utils import get_service_id, get_local_ipv4

logger = logging.getLogger(__name__)

class InvalidCertificateException(http.client.HTTPException, urllib.error.URLError):
    def __init__(self, service_id, cert, reason):
        http.client.HTTPException.__init__(self)
        self._service_id = service_id
        self._cert_service_id = get_service_id(cert=cert)
        self.reason = reason

    def __str__(self):
        return ('%s (local) != %s (remote) (%s)\n' %
                (self._service_id, self._cert_service_id, self.reason))

def is_local(host):
    local_net = get_local_ipv4()[:-2]
    return host.startswith('127.0.0.1') or host.startswith(local_net)

def getaddrinfo(*args):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (args[0], args[1]))]

def create_tor_connection(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                      source_address=None):
    host, port = address
    err = None
    af = socket.AF_INET
    socktype = socket.SOCK_STREAM
    proto = 6
    sa = address
    sock = None
    try:
        sock = socks.socksocket(af, socktype, proto)
        if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
            sock.settimeout(timeout)
        socks_port = state.tor.socks_port if state.tor else 9150
        sock.set_proxy(socks.SOCKS5, "localhost", socks_port, True)
        if source_address:
            sock.bind(source_address)
        sock.connect(sa)
        return sock

    except socket.error as _:
        err = _
        if sock is not None:
            sock.close()

    if err is not None:
        raise err
    else:
        raise sock.error("getaddrinfo returns an empty list")

class TorHTTPSConnection(http.client.HTTPSConnection):

    def __init__(self, host, port=None, service_id=None, check_hostname=None, context=None, **kwargs):
        self._service_id = service_id
        if self._service_id:
            context = ssl._create_default_https_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            context.load_cert_chain(settings.ssl_cert_path, settings.ssl_key_path)
            context.load_default_certs()
        http.client.HTTPSConnection.__init__(self, host, port,
            check_hostname=check_hostname, context=context, **kwargs)

        if not is_local(host):
            self._create_connection = create_tor_connection

    def _check_service_id(self, cert):
        service_id = get_service_id(cert=cert)
        logger.debug('ssl service_id: %s (match: %s)', service_id, service_id == self._service_id)
        if service_id != self._service_id:
            logger.debug('expected service_id: %s', self._service_id)
        return service_id == self._service_id

    def connect(self):
        http.client.HTTPSConnection.connect(self)
        if self._service_id:
            cert = self.sock.getpeercert(binary_form=True)
            if not self._check_service_id(cert):
                raise InvalidCertificateException(self._service_id, cert,
                                                  'service_id mismatch')
        #logger.debug('CIPHER %s VERSION %s', self.sock.cipher(), self.sock.ssl_version)

class TorHTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(self, debuglevel=0, context=None, check_hostname=None, service_id=None):
        urllib.request.AbstractHTTPHandler.__init__(self, debuglevel)
        self._context = context
        self._check_hostname = check_hostname
        self._service_id = service_id

    def https_open(self, req):
        return self.do_open(TorHTTPSConnection, req,
            context=self._context, check_hostname=self._check_hostname,
            service_id=self._service_id)

class TorHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host, port=None, **kwargs):
        http.client.HTTPConnection.__init__(self, host, port, **kwargs)
        if not is_local(host):
            self._create_connection = create_tor_connection

class TorHTTPHandler(urllib.request.HTTPHandler):
    def http_open(self, req):
        return self.do_open(TorHTTPConnection, req)

def get_opener(service_id=None):
    handler = TorHTTPSHandler(service_id=service_id)
    opener = urllib.request.build_opener(handler, TorHTTPHandler())
    return opener
