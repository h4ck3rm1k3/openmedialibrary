import OpenSSL

key = OpenSSL.crypto.PKey()
key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)

ca = OpenSSL.crypto.X509()
ca.set_version(2)
ca.set_serial_number(1)
ca.get_subject().CN = "put_ed25519_key_here"
ca.gmtime_adj_notBefore(0)
ca.gmtime_adj_notAfter(24 * 60 * 60)
ca.set_issuer(ca.get_subject())
ca.set_pubkey(key)
ca.add_extensions([
  OpenSSL.crypto.X509Extension("basicConstraints", True,
                               "CA:TRUE, pathlen:0"),
  OpenSSL.crypto.X509Extension("keyUsage", True,
                               "keyCertSign, cRLSign"),
  OpenSSL.crypto.X509Extension("subjectKeyIdentifier", False, "hash",
                               subject=ca),
  OpenSSL.crypto.X509Extension("authorityKeyIdentifier", False, "keyid:always",issuer=ca)
  ])
ca.sign(key, "sha1")
open("MyCertificate.crt.bin", "wb").write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_ASN1, ca))

