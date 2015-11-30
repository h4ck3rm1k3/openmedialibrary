# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


import os
import sys
from PIL import Image
from io import StringIO, BytesIO
import re
import stdnum.isbn
import socket
import io
import gzip
import time
import hashlib
from datetime import datetime
import subprocess
import base64

import ox
import ed25519
from OpenSSL.crypto import (
    load_privatekey, load_certificate,
    dump_privatekey, dump_certificate,
    FILETYPE_ASN1, FILETYPE_PEM, PKey, TYPE_RSA,
    X509, X509Extension
)
from Crypto.PublicKey import RSA
from Crypto.Util.asn1 import DerSequence


from meta.utils import normalize_isbn, find_isbns

import logging
logger = logging.getLogger(__name__)

ENCODING='base64'

def cleanup_id(key, value):
    if key == 'isbn':
        value = normalize_isbn(value)
    if key in ('lccn', 'olid', 'oclc'):
        value = ''.join([v for v in value if v!='-'])
    return value

def valid_olid(id):
    return id.startswith('OL') and id.endswith('M')

def get_positions(ids, pos):
    '''
    >>> get_positions([1,2,3,4], [2,4])
    {2: 1, 4: 3}
    '''
    positions = {}
    for i in pos:
        try:
            positions[i] = ids.index(i)
        except:
            pass
    return positions

def get_by_key(objects, key, value):
    obj = [o for o in objects if o.get(key) == value]
    return obj and obj[0] or None

def get_by_id(objects, id):
    return get_by_key(objects, 'id', id)

def resize_image(data, width=None, size=None):
    if isinstance(data, bytes):
        data = BytesIO(data)
    else:
        data = StringIO(data)
    source = Image.open(data)
    if source.mode not in ('1', 'CMYK', 'L', 'RGB', 'RGBA', 'RGBX', 'YCbCr'):
        source = source.convert('RGB')
    source_width = source.size[0]
    source_height = source.size[1]
    if size:
        if source_width > source_height:
            width = size
            height = int(width / (float(source_width) / source_height))
            height = height - height % 2
        else:
            height = size
            width = int(height * (float(source_width) / source_height))
            width = width - width % 2

    else:
        height = int(width / (float(source_width) / source_height))
        height = height - height % 2

    width = max(width, 1)
    height = max(height, 1)

    if width < source_width:
        resize_method = Image.ANTIALIAS
    else:
        resize_method = Image.BICUBIC
    output = source.resize((width, height), resize_method)
    o = BytesIO()
    output.save(o, format='jpeg')
    data = o.getvalue()
    o.close()
    return data

def sort_title(title):

    title = title.replace('Æ', 'Ae')
    if isinstance(title, str):
        title = str(title)
    title = ox.sort_string(title)

    #title
    title = re.sub('[\'!¿¡,\.;\-"\:\*\[\]]', '', title)
    return title.strip()

def get_position_by_id(list, key):
    for i in range(0, len(list)):
        if list[i]['id'] == key:
            return i
    return -1

def valid(key, value, sig):
    '''
    validate that value was signed by key
    '''
    if isinstance(sig, str):
        sig = sig.encode()
    if isinstance(value, str):
        value = value.encode()
    if isinstance(key, str):
        key = key.encode()
    vk = ed25519.VerifyingKey(key, encoding=ENCODING)
    try:
        vk.verify(sig, value, encoding=ENCODING)
    #except ed25519.BadSignatureError:
    except:
        return False
    return True

def get_user_id(private_key, cert_path):
    if os.path.exists(private_key):
        with open(private_key) as fd:
            key = load_privatekey(FILETYPE_PEM, fd.read())
        if key.bits() != 1024:
            os.unlink(private_key)
        else:
            user_id = get_service_id(private_key)
    if not os.path.exists(private_key):
        if os.path.exists(cert_path):
            os.unlink(cert_path)
        folder = os.path.dirname(private_key)
        if not os.path.exists(folder):
            os.makedirs(folder)
            os.chmod(folder, 0o700)
        key = PKey()
        key.generate_key(TYPE_RSA, 1024)
        with open(private_key, 'wb') as fd:
            os.chmod(private_key, 0o600)
            fd.write(dump_privatekey(FILETYPE_PEM, key))
            os.chmod(private_key, 0o400)
        user_id = get_service_id(private_key)
    if not os.path.exists(cert_path):
        ca = X509()
        ca.set_version(2)
        ca.set_serial_number(1)
        ca.get_subject().CN = user_id
        ca.gmtime_adj_notBefore(0)
        ca.gmtime_adj_notAfter(24 * 60 * 60)
        ca.set_issuer(ca.get_subject())
        ca.set_pubkey(key)
        ca.add_extensions([
          X509Extension(b"basicConstraints", True, b"CA:TRUE, pathlen:0"),
          X509Extension(b"nsCertType", True, b"sslCA"),
          X509Extension(b"extendedKeyUsage", True,
            b"serverAuth,clientAuth,emailProtection,timeStamping,msCodeInd,msCodeCom,msCTLSign,msSGC,msEFS,nsSGC"),
          X509Extension(b"keyUsage", False, b"keyCertSign, cRLSign"),
          X509Extension(b"subjectKeyIdentifier", False, b"hash", subject=ca),
        ])
        ca.sign(key, "sha256")
        with open(cert_path, 'wb') as fd:
            fd.write(dump_certificate(FILETYPE_PEM, ca))
    return user_id

def get_service_id(private_key_file=None, cert=None):
    '''
    service_id is the first half of the sha1 of the rsa public key encoded in base32
    '''
    if private_key_file:
        with open(private_key_file, 'rb') as fd:
            private_key = fd.read()
        public_key = RSA.importKey(private_key).publickey().exportKey('DER')[22:]
        # compute sha1 of public key and encode first half in base32
        service_id = base64.b32encode(hashlib.sha1(public_key).digest()[:10]).lower().decode()
        '''
        # compute public key from priate key and export in DER format
        # ignoring the SPKI header(22 bytes)
        key = load_privatekey(FILETYPE_PEM, private_key)
        cert = X509()
        cert.set_pubkey(key)
        public_key = dump_privatekey(FILETYPE_ASN1, cert.get_pubkey())[22:]
        # compute sha1 of public key and encode first half in base32
        service_id = base64.b32encode(hashlib.sha1(public_key).digest()[:10]).lower().decode()
        '''
    elif cert:
        # compute sha1 of public key and encode first half in base32
        key = load_certificate(FILETYPE_ASN1, cert).get_pubkey()
        pub_der = DerSequence()
        pub_der.decode(dump_privatekey(FILETYPE_ASN1, key))
        public_key = RSA.construct((pub_der._seq[1], pub_der._seq[2])).exportKey('DER')[22:]
        service_id = base64.b32encode(hashlib.sha1(public_key).digest()[:10]).lower().decode()
    return service_id

def get_public_ipv6():
    try:
        host = ('2a01:4f8:120:3201::3', 25519)
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(host)
        ip = s.getsockname()[0]
        s.close()
    except:
        ip = None
    return ip

def get_interface():
    interface = ''
    if sys.platform == 'darwin' or sys.platform.startswith('freebsd'):
        #cmd = ['/usr/sbin/netstat', '-rn']
        cmd = ['/sbin/route', '-n', 'get', 'default']
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, close_fds=True)
        stdout, stderr = p.communicate()
        stdout = stdout.decode('utf-8')
        interface = [[p.strip() for p in s.split(':', 1)]
            for s in stdout.strip().split('\n') if 'interface' in s]
        if interface:
            interface = '%%%s' % interface[0][1]
        else:
            interface = ''
    return interface

def get_local_ipv4():
    ip = None
    if sys.platform == 'darwin' or sys.platform.startswith('freebsd'):
        cmd = ['/sbin/route', '-n', 'get', 'default']
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, close_fds=True)
        stdout, stderr = p.communicate()
        stdout = stdout.decode('utf-8')
        interface = [[p.strip() for p in s.split(':', 1)]
                for s in stdout.strip().split('\n') if 'interface' in s]
        if interface:
            interface = interface[0][1]
            cmd = ['ifconfig', interface]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, close_fds=True)
            stdout, stderr = p.communicate()
            stdout = stdout.decode('utf-8')
            ips = [l for l in stdout.split('\n') if 'inet ' in l]
            if ips:
                ip = ips[0].strip().split(' ')[1]
    else:
        cmd = ['ip', 'route', 'show']
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, close_fds=True)
        stdout, stderr = p.communicate()
        stdout = stdout.decode('utf-8')
        local = [l for l in stdout.split('\n') if 'default' in l]
        if local:
            dev = local[0].split(' ')[4]
            local_ip = [l for l in stdout.split('\n')
                    if dev in l and not 'default' in l and 'src' in l]
            ip = [p for p in local_ip[0].split(' ')[1:] if '.' in p][0]
    return ip

def update_dict(root, data):
    for key in data:
        keys = [part.replace('\0', '\\.') for part in key.replace('\\.', '\0').split('.')]
        value = data[key]
        p = root
        while len(keys)>1:
            key = keys.pop(0)
            if isinstance(p, list):
                p = p[get_position_by_id(p, key)]
            else:
                if key not in p:
                    p[key] = {}
                p = p[key]
        if value == None and keys[0] in p:
            del p[keys[0]]
        else:
            p[keys[0]] = value

def remove_empty_folders(prefix):
    empty = []
    for root, folders, files in os.walk(prefix):
        if not folders and not files:
            empty.append(root)
    for folder in empty:
        remove_empty_tree(folder)

def remove_empty_tree(leaf):
    while leaf:
        if not os.path.exists(leaf):
            leaf = os.path.dirname(leaf)
        elif os.path.isdir(leaf) and not os.listdir(leaf):
            logger.debug('rmdir %s', leaf)
            os.rmdir(leaf)
        else:
            break

utc_0 = int(time.mktime(datetime(1970, 1, 1).timetuple()))

def datetime2ts(dt):
    return int(time.mktime(dt.utctimetuple())) - utc_0

def ts2datetime(ts):
    return datetime.utcfromtimestamp(float(ts))

def run(*cmd):
    p = subprocess.Popen(cmd, close_fds=True)
    p.wait()
    return p.returncode

def get(*cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    stdout, error = p.communicate()
    return stdout.decode()

def makefolder(path):
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def open_folder(folder):
    cmd = 'open'
    if sys.platform.startswith('linux'):
        cmd = 'xdg-open'
    subprocess.Popen([cmd, folder], close_fds=True)
