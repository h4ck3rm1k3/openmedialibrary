# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import os
import sys
import Image
from StringIO import StringIO
import re
import stdnum.isbn
import socket
import cStringIO
import gzip
import time
from datetime import datetime
import subprocess

import ox
import ed25519

from meta.utils import normalize_isbn, find_isbns

import logging
logger = logging.getLogger('oml.utils')

ENCODING='base64'

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
    obj = filter(lambda o: o.get(key) == value, objects)
    return obj and obj[0] or None

def get_by_id(objects, id):
    return get_by_key(objects, 'id', id)

def resize_image(data, width=None, size=None):
    source = Image.open(StringIO(data))
    if source.mode == 'P':
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
    o = StringIO()
    output.save(o, format='jpeg')
    data = o.getvalue()
    o.close()
    return data

def sort_title(title):

    title = title.replace(u'Æ', 'Ae')
    if isinstance(title, str):
        title = unicode(title)
    title = ox.sort_string(title)

    #title
    title = re.sub(u'[\'!¿¡,\.;\-"\:\*\[\]]', '', title)
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
    vk = ed25519.VerifyingKey(str(key), encoding=ENCODING)
    try:
        vk.verify(str(sig), str(value), encoding=ENCODING)
    #except ed25519.BadSignatureError:
    except:
        return False
    return True

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
    if sys.platform == 'darwin':
        #cmd = ['/usr/sbin/netstat', '-rn']
        cmd = ['/sbin/route', '-n', 'get', 'default']
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        interface = [[p.strip() for p in s.split(':', 1)] for s in stdout.strip().split('\n') if 'interface' in s]
        if interface:
            interface = '%%%s' % interface[0][1]
        else:
            interface = ''
    return interface

def get_local_ipv4():
    ip = socket.gethostbyaddr(socket.getfqdn())[-1][0]
    if ip == '127.0.0.1':
        if sys.platform == 'linux2':
            cmd = ['ip', 'route', 'show']
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            stdout, stderr = p.communicate()
            local = [l for l in stdout.split('\n') if 'default' in l]
            if local:
                dev = local[0].split(' ')[4]
                local_ip = [l for l in stdout.split('\n') if dev in l and not 'default' in l]
                return [p for p in local_ip[0].split(' ')[1:] if '.' in p][0]
        else:
            cmd = ['/sbin/route', '-n', 'get', 'default']
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            stdout, stderr = p.communicate()
            interface = [[p.strip() for p in s.split(':', 1)] for s in stdout.strip().split('\n') if 'interface' in s]
            if interface:
                interface = interface[0][1]
                cmd = ['ifconfig', interface]
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
                stdout, stderr = p.communicate()
                ips = [l for l in stdout.split('\n') if 'inet ' in l]
                if ips:
                    ip = ips[0].strip().split(' ')[1]
    return ip

def update_dict(root, data):
    for key in data:
        keys = map(lambda part: part.replace('\0', '\\.'), key.replace('\\.', '\0').split('.'))
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

utc_0 = int(time.mktime(datetime(1970, 01, 01).timetuple()))

def datetime2ts(dt):
    return int(time.mktime(dt.utctimetuple())) - utc_0

def ts2datetime(ts):
    return datetime.utcfromtimestamp(float(ts))
