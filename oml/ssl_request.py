# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import http.client
import urllib.request, urllib.error, urllib.parse
import hashlib
import logging
logger = logging.getLogger('oml.ssl_request')

class InvalidCertificateException(http.client.HTTPException, urllib.error.URLError):
    def __init__(self, fingerprint, cert, reason):
        http.client.HTTPException.__init__(self)
        self._fingerprint = fingerprint
        self._cert_fingerprint = hashlib.sha1(cert).hexdigest()
        self.reason = reason

    def __str__(self):
        return ('%s (local) != %s (remote) (%s)\n' %
                (self._fingerprint, self._cert_fingerprint, self.reason))

class FingerprintHTTPSConnection(http.client.HTTPSConnection):

    def __init__(self, host, port=None, fingerprint=None, check_hostname=None, **kwargs):
        self._fingerprint = fingerprint
        if self._fingerprint:
            check_hostname = None
        http.client.HTTPSConnection.__init__(self, host, port,
                check_hostname=check_hostname, **kwargs)

    def _check_fingerprint(self, cert):
        if len(self._fingerprint) == 40:
            fingerprint = hashlib.sha1(cert).hexdigest()
        elif len(self._fingerprint) == 64:
            fingerprint = hashlib.sha256(cert).hexdigest()
        elif len(self._fingerprint) == 128:
            fingerprint = hashlib.sha512(cert).hexdigest()
        else:
            logging.error('unkown _fingerprint length %s (%s)',
                self._fingerprint, len(self._fingerprint))
            return False
        return fingerprint == self._fingerprint

    def connect(self):
        http.client.HTTPSConnection.connect(self)
        if self._fingerprint:
            cert = self.sock.getpeercert(binary_form=True)
            if not self._check_fingerprint(cert):
                raise InvalidCertificateException(self._fingerprint, cert,
                                                  'fingerprint mismatch')
        #logger.debug('CIPHER %s VERSION %s', self.sock.cipher(), self.sock.ssl_version)

class FingerprintHTTPSHandler(urllib.request.HTTPSHandler):

    def __init__(self, debuglevel=0, context=None, check_hostname=None, fingerprint=None):
        urllib.request.AbstractHTTPHandler.__init__(self, debuglevel)
        self._context = context
        self._check_hostname = check_hostname
        self._fingerprint = fingerprint

    def https_open(self, req):
        return self.do_open(FingerprintHTTPSConnection, req,
            context=self._context, check_hostname=self._check_hostname,
            fingerprint=self._fingerprint)

def get_opener(fingerprint):
    handler = FingerprintHTTPSHandler(fingerprint=fingerprint)
    opener = urllib.request.build_opener(handler)
    return opener
