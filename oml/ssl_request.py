# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import ssl
import http.client
import urllib.request, urllib.error, urllib.parse
import hashlib
import logging
import base64
from OpenSSL import crypto

logger = logging.getLogger('oml.ssl_request')

def get_service_id(cert):
    # compute sha1 of public key and encode first half in base32
    key = crypto.load_certificate(crypto.FILETYPE_ASN1, cert).get_pubkey()
    public_key = crypto.dump_privatekey(crypto.FILETYPE_ASN1, key)[22:]
    service_id = base64.b32encode(hashlib.sha1(public_key).digest()[:10]).lower()
    return service_id

class InvalidCertificateException(http.client.HTTPException, urllib.error.URLError):
    def __init__(self, service_id, cert, reason):
        http.client.HTTPException.__init__(self)
        self._service_id = service_id
        self._cert_service_id = get_service_id(cert)
        self.reason = reason

    def __str__(self):
        return ('%s (local) != %s (remote) (%s)\n' %
                (self._service_id, self._cert_service_id, self.reason))

class ServiceIdHTTPSConnection(http.client.HTTPSConnection):

    def __init__(self, host, port=None, service_id=None, check_hostname=None, context=None, **kwargs):
        self._service_id = service_id
        if self._service_id:
            check_hostname = False
            # dont fial for older verions of python
            # without ssl._create_default_https_context
            # that also don't check by default
            try:
                context = ssl._create_default_https_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            except:
                pass
        http.client.HTTPSConnection.__init__(self, host, port,
                check_hostname=check_hostname, context=context, **kwargs)

    def _check_service_id(self, cert):
        service_id = get_service_id(cert)
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

class ServiceIdHTTPSHandler(urllib.request.HTTPSHandler):

    def __init__(self, debuglevel=0, context=None, check_hostname=None, service_id=None):
        urllib.request.AbstractHTTPHandler.__init__(self, debuglevel)
        self._context = context
        self._check_hostname = check_hostname
        self._service_id = service_id

    def https_open(self, req):
        return self.do_open(ServiceIdHTTPSConnection, req,
            context=self._context, check_hostname=self._check_hostname,
            service_id=self._service_id)

def get_opener(service_id):
    handler = ServiceIdHTTPSHandler(service_id=service_id)
    opener = urllib.request.build_opener(handler)
    return opener
