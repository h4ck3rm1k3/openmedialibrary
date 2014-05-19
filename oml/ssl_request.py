import httplib
import socket
import urllib2
import ssl
import hashlib
import logging
logger = logging.getLogger('oml.ssl_request')

class InvalidCertificateException(httplib.HTTPException, urllib2.URLError):
    def __init__(self, fingerprint, cert, reason):
        httplib.HTTPException.__init__(self)
        self.fingerprint = fingerprint
        self.cert_fingerprint = hashlib.sha1(cert).hexdigest()
        self.reason = reason

    def __str__(self):
        return ('%s (local) != %s (remote) (%s)\n' %
                (self.fingerprint, self.cert_fingerprint, self.reason))

class CertValidatingHTTPSConnection(httplib.HTTPConnection):
    default_port = httplib.HTTPS_PORT

    def __init__(self, host, port=None, fingerprint=None, strict=None, **kwargs):
        httplib.HTTPConnection.__init__(self, host, port, strict, **kwargs)
        self.fingerprint = fingerprint
        if self.fingerprint:
            self.cert_reqs = ssl.CERT_REQUIRED
        else:
            self.cert_reqs = ssl.CERT_NONE
        self.cert_reqs = ssl.CERT_NONE

    def _ValidateCertificateFingerprint(self, cert):
        fingerprint = hashlib.sha1(cert).hexdigest()
        return fingerprint == self.fingerprint

    def connect(self):
        sock = socket.create_connection((self.host, self.port))
        self.sock = ssl.wrap_socket(sock, cert_reqs=self.cert_reqs)
        #if self.cert_reqs & ssl.CERT_REQUIRED:
        if self.fingerprint:
            cert = self.sock.getpeercert(binary_form=True)
            if not self._ValidateCertificateFingerprint(cert):
                raise InvalidCertificateException(self.fingerprint, cert,
                                                  'fingerprint mismatch')
        #logger.debug('CIPHER %s VERSION %s', self.sock.cipher(), self.sock.ssl_version)

class VerifiedHTTPSHandler(urllib2.HTTPSHandler):
    def __init__(self, **kwargs):
        urllib2.AbstractHTTPHandler.__init__(self)
        self._connection_args = kwargs

    def https_open(self, req):
        def http_class_wrapper(host, **kwargs):
            full_kwargs = dict(self._connection_args)
            full_kwargs.update(kwargs)
            return CertValidatingHTTPSConnection(host, **full_kwargs)

        try:
            return self.do_open(http_class_wrapper, req)
        except urllib2.URLError, e:
            if type(e.reason) == ssl.SSLError and e.reason.args[0] == 1:
                raise InvalidCertificateException(self.fingerprint, '',
                                                  e.reason.args[1])
            raise

    https_request = urllib2.HTTPSHandler.do_request_

def get_opener(fingerprint):
    handler = VerifiedHTTPSHandler(fingerprint=fingerprint)
    opener = urllib2.build_opener(handler)
    return opener
