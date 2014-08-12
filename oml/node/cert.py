# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import hashlib
import os

import OpenSSL

import settings


def get_fingerprint():
    with open(settings.ssl_cert_path) as fd:
        data = fd.read()
    cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, data)
    return hashlib.sha1(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert)).hexdigest()

def generate_ssl():
    key = OpenSSL.crypto.PKey()
    key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
    with open(settings.ssl_key_path, 'wb') as fd:
        os.chmod(settings.ssl_key_path, 0600)
        fd.write(OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key))
        os.chmod(settings.ssl_key_path, 0400)

    ca = OpenSSL.crypto.X509()
    ca.set_version(2)
    ca.set_serial_number(1)
    ca.get_subject().CN = settings.USER_ID
    ca.gmtime_adj_notBefore(0)
    ca.gmtime_adj_notAfter(24 * 60 * 60)
    ca.set_issuer(ca.get_subject())
    ca.set_pubkey(key)
    ca.add_extensions([
      OpenSSL.crypto.X509Extension("basicConstraints", True, "CA:TRUE, pathlen:0"),
      OpenSSL.crypto.X509Extension("nsCertType", True, "sslCA"),
      OpenSSL.crypto.X509Extension("extendedKeyUsage", True,
        "serverAuth,clientAuth,emailProtection,timeStamping,msCodeInd,msCodeCom,msCTLSign,msSGC,msEFS,nsSGC"),
      OpenSSL.crypto.X509Extension("keyUsage", False, "keyCertSign, cRLSign"),
      OpenSSL.crypto.X509Extension("subjectKeyIdentifier", False, "hash", subject=ca),
    ])
    ca.sign(key, "sha1")
    with open(settings.ssl_cert_path, 'wb') as fd:
        fd.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, ca))
    return get_fingerprint()
