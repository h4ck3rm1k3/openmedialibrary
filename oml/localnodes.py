# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import json
import logging
import socket
import struct
import thread
from threading import Thread

from utils import valid, get_public_ipv6, get_local_ipv4, get_interface
from settings import preferences, server, USER_ID, sk
import state

logger = logging.getLogger('oml.localnodes')

def can_connect(data):
    try:
        if ':' in data['host']:
            s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect((data['host'], data['port']))
        s.close()
        return True
    except:
        pass
    logger.debug('can_connect failed')
    return False

class LocalNodes(Thread):
    _active = True
    _nodes = {}

    _MODE = 6
    _BROADCAST = "ff02::1"
    _BROADCAST4 = "239.255.255.250"
    _PORT = 9851 
    TTL = 1

    def __init__(self, app):
        self._app = app
        Thread.__init__(self)
        if not server['localnode_discovery']:
            return
        self.daemon = True
        self.start()

    def get_packet(self):
        message = json.dumps({
            'username': preferences.get('username', 'anonymous'),
            'host': self.host,
            'port': server['node_port'],
            'cert': server['cert']
        })
        sig = sk.sign(message, encoding='base64')
        packet = json.dumps([sig, USER_ID, message])
        return packet

    def send(self):
        if not server['localnode_discovery']:
            return
        if self._MODE == 4:
            return self.send4()
        packet = self.get_packet()
        ttl = struct.pack('@i', self.TTL)
        address = self._BROADCAST + get_interface()
        addrs = socket.getaddrinfo(address, self._PORT, socket.AF_INET6, socket.SOCK_DGRAM)
        addr = addrs[0]
        (family, socktype, proto, canonname, sockaddr) = addr
        s = socket.socket(family, socktype, proto)
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl)
        s.sendto(packet + '\0', sockaddr)
        s.close()

    def send4(self):
        logger.debug('send4')
        packet = self.get_packet()
        sockaddr = (self._BROADCAST4, self._PORT)
        s = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt (socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        s.sendto(packet + '\0', sockaddr)
        s.close()
        logger.debug('sent4')
        '''
        try:
            s.sendto(packet + '\0', sockaddr)
            s.close()
        except:
            logger.debug('send failed %s', )
            return
        '''

    def receive(self):
        if self._MODE == 4:
            return self.receive4()
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
                self.update_node(data)

    def receive4(self):
        logger.debug('receive4')
        s = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mreq = struct.pack("=4sl", socket.inet_aton(self._BROADCAST4), socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        s.bind(('', self._PORT))
        while self._active:
            data, addr = s.recvfrom(1024)
            logger.debug('receive4')
            while data[-1] == '\0':
                data = data[:-1] # Strip trailing \0's
            logger.debug('receive4 %s', data)
            data = self.verify(data)
            if data:
                self.update_node(data)

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

    def update_node(self, data):
        #fixme use local link address
        #print addr
        if data['id'] != USER_ID:
            if data['id'] not in self._nodes:
                thread.start_new_thread(self.new_node, (data, ))
            #else:
            #    print 'UPDATE NODE', data
            self._nodes[data['id']] = data

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
                state.nodes.queue('add', u.id)
            self.send()

    def run(self):
        self.host = get_public_ipv6()
        if not self.host:
            logger.debug('no ipv6 detected, fall back to local ipv4 sharing')
            self.host = get_local_ipv4()
            self._MODE = 4
        self.send()
        self.receive()

    def join(self):
        self._active = False
        return Thread.join(self)
