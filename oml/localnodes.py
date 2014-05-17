# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import json
import logging
import socket
import struct
import subprocess
import sys
import thread
from threading import Thread

from settings import preferences, server, USER_ID, sk
from node.utils import get_public_ipv6
from ed25519_utils import valid

logger = logging.getLogger('oml.localnodes')

def can_connect(data):
    try:
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect((data['host'], data['port']))
        s.close()
        return True
    except:
        pass
    return False

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

class LocalNodes(Thread):
    _active = True
    _nodes = {}

    _BROADCAST = "ff02::1"
    _PORT = 9851 
    TTL = 1

    def __init__(self, app):
        self._app = app
        Thread.__init__(self)
        if not server['localnode_discovery']:
            return
        self.daemon = True
        self.start()

    def send(self):
        if not server['localnode_discovery']:
            return

        message = json.dumps({
            'username': preferences.get('username', 'anonymous'),
            'host': self.host,
            'port': server['node_port'],
            'cert': server['cert']
        })
        sig = sk.sign(message, encoding='base64')
        packet = json.dumps([sig, USER_ID, message])

        ttl = struct.pack('@i', self.TTL)
        address = self._BROADCAST + get_interface()
        addrs = socket.getaddrinfo(address, self._PORT, socket.AF_INET6,socket.SOCK_DGRAM)
        addr = addrs[0]
        (family, socktype, proto, canonname, sockaddr) = addr
        s = socket.socket(family, socktype, proto)
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl)
        s.sendto(packet + '\0', sockaddr)
        s.close()

    def receive(self):
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', self._PORT))
        group_bin = socket.inet_pton(socket.AF_INET6, self._BROADCAST) + '\0'*4
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, group_bin)

        while self._active:
            data, addr = s.recvfrom(1024)
            while data[-1] == '\0':
                data = data[:-1] # Strip trailing \0's
            data = self.verify(data)
            if data:
                #fixme use local link address
                #print addr
                if data['id'] != USER_ID:
                    if data['id'] not in self._nodes:
                        thread.start_new_thread(self.new_node, (data, ))
                    #else:
                    #    print 'UPDATE NODE', data
                    self._nodes[data['id']] = data

    def verify(self, data):
        try:
            packet = json.loads(data)
        except:
            return None
        if len(packet) == 3:
            sig, user_id, data = packet
            if valid(user_id, data, sig):
                message = json.loads(data)
                message['id'] = user_id
                for key in ['id', 'username', 'host', 'port', 'cert']:
                    if key not in message:
                        return None
                return message

    def get(self, user_id):
        if user_id in self._nodes:
            if can_connect(self._nodes[user_id]):
                return self._nodes[user_id]

    def new_node(self, data):
        logger.debug('NEW NODE %s', data)
        if can_connect(data):
            self._nodes[data['id']] = data
            with self._app.app_context():
                import user.models
                u = user.models.User.get_or_create(data['id'])
                u.info['username'] = data['username']
                u.info['local'] = data
                u.save()
            self.send()

    def run(self):
        self.host = get_public_ipv6()
        self.send()
        self.receive()

    def join(self):
        self._active = False
        return Thread.join(self)
