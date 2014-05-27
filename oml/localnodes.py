# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import json
import logging
import socket
import struct
import thread
from threading import Thread
import time

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

class LocalNodesBase(Thread):

    _PORT = 9851 
    _TTL = 1

    def __init__(self, app, nodes):
        self._active = True
        self._nodes = nodes
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

    def get_socket(self):
        pass

    def send(self):
        pass

    def receive(self):
        while self._active:
            try:
                s = self.get_socket()
                s.bind(('', self._PORT))
                while self._active:
                    data, addr = s.recvfrom(1024)
                    while data[-1] == '\0':
                        data = data[:-1] # Strip trailing \0's
                    data = self.verify(data)
                    if data:
                        self.update_node(data)
            except:
                logger.debug('receive failed. restart later', exc_info=1)
                time.sleep(10)


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
            elif can_connect(data):
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
                u.update_name()
                u.save()
                state.nodes.queue('add', u.id)
            self.send()

    def get_ip(self):
        pass

    def run(self):
        self.host = self.get_ip()
        self.send()
        self.receive()

    def join(self):
        self._active = False
        return Thread.join(self)

class LocalNodes4(LocalNodesBase):

    _BROADCAST = "239.255.255.250"
    _TTL = 1

    def send(self):
        packet = self.get_packet()
        sockaddr = (self._BROADCAST, self._PORT)
        s = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt (socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self._TTL)
        try:
            s.sendto(packet + '\0', sockaddr)
        except:
            logger.debug('LocalNodes4.send failed', exc_info=1)
        s.close()

    def get_socket(self):
        s = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mreq = struct.pack("=4sl", socket.inet_aton(self._BROADCAST), socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        return s

    def get_ip(self):
        return get_local_ipv4()

class LocalNodes6(LocalNodesBase):

    _BROADCAST = "ff02::1"

    def send(self):
        logger.debug('send6')
        packet = self.get_packet()
        ttl = struct.pack('@i', self._TTL)
        address = self._BROADCAST + get_interface()
        addrs = socket.getaddrinfo(address, self._PORT, socket.AF_INET6, socket.SOCK_DGRAM)
        addr = addrs[0]
        (family, socktype, proto, canonname, sockaddr) = addr
        s = socket.socket(family, socktype, proto)
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl)
        try:
            s.sendto(packet + '\0', sockaddr)
        except:
            logger.debug('LocalNodes6.send failed', exc_info=1)
        s.close()

    def get_socket(self):
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        group_bin = socket.inet_pton(socket.AF_INET6, self._BROADCAST) + '\0'*4
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, group_bin)
        return s

    def get_ip(self):
        return get_public_ipv6()

class LocalNodes(object):

    _nodes4 = None
    _nodes6 = None

    def __init__(self, app):
        self._nodes = {}
        self._app = app
        if not server['localnode_discovery']:
            return
        self._nodes4 = LocalNodes4(app, self._nodes)
        self._nodes6 = LocalNodes6(app, self._nodes)

    def get(self, user_id):
        if user_id in self._nodes:
            if can_connect(self._nodes[user_id]):
                return self._nodes[user_id]

    def join(self):
        if self._nodes4:
            self._nodes4.join()
        if self._nodes6:
            self._nodes6.join()
