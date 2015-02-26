# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


import json
import socket
import struct
import _thread
from threading import Thread
import time

from utils import valid, get_public_ipv6, get_local_ipv4, get_interface
from settings import preferences, server, USER_ID, sk
import state
import db
import user.models

import logging
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

    def __init__(self, nodes):
        self._socket = None
        self._active = True
        self._nodes = nodes
        Thread.__init__(self)
        if not server['localnode_discovery']:
            return
        self.daemon = True
        self.start()

    def get_packet(self):
        self.host = self.get_ip()
        if self.host:
            message = json.dumps({
                'username': preferences.get('username', 'anonymous'),
                'host': self.host,
                'port': server['node_port'],
                'cert': server['cert']
            })
            sig = sk.sign(message.encode(), encoding='base64').decode()
            packet = json.dumps([sig, USER_ID, message]).encode()
        else:
            packet = None
        return packet

    def get_socket(self):
        pass

    def send(self):
        pass

    def receive(self):
        last = time.mktime(time.localtime())
        while self._active:
            try:
                s = self.get_socket()
                s.bind(('', self._PORT))
                while self._active:
                    data, addr = s.recvfrom(1024)
                    if self._active:
                        while data[-1] == 0:
                            data = data[:-1] # Strip trailing \0's
                        data = self.verify(data)
                        if data:
                            self.update_node(data)
            except socket.timeout:
                if self._active:
                    now = time.mktime(time.localtime())
                    if now - last > 60:
                        last = now
                        _thread.start_new_thread(self.send, ())
            except:
                if self._active:
                    logger.debug('receive failed. restart later', exc_info=1)
                    time.sleep(10)

    def verify(self, data):
        try:
            packet = json.loads(data.decode())
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
                _thread.start_new_thread(self.new_node, (data, ))
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
            with db.session():
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
        self.send()
        self.receive()

    def join(self):
        self._active = False
        if self._socket:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._socket.close()
        return Thread.join(self)

class LocalNodes4(LocalNodesBase):

    _BROADCAST = "239.255.255.250"
    _TTL = 1

    def send(self):
        packet = self.get_packet()
        if packet:
            logger.debug('send4 %s', packet)
            sockaddr = (self._BROADCAST, self._PORT)
            s = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt (socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self._TTL)
            try:
                s.sendto(packet + b'\0', sockaddr)
            except:
                logger.debug('LocalNodes4.send failed', exc_info=1)
            s.close()

    def get_socket(self):
        s = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        mreq = struct.pack("=4sl", socket.inet_aton(self._BROADCAST), socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self._socket = s
        return s

    def get_ip(self):
        return get_local_ipv4()

class LocalNodes6(LocalNodesBase):

    _BROADCAST = "ff02::1"

    def send(self):
        packet = self.get_packet()
        if packet:
            logger.debug('send6 %s', packet)
            ttl = struct.pack('@i', self._TTL)
            address = self._BROADCAST + get_interface()
            addrs = socket.getaddrinfo(address, self._PORT, socket.AF_INET6, socket.SOCK_DGRAM)
            addr = addrs[0]
            (family, socktype, proto, canonname, sockaddr) = addr
            s = socket.socket(family, socktype, proto)
            s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl)
            try:
                s.sendto(packet + b'\0', sockaddr)
            except:
                logger.debug('LocalNodes6.send failed', exc_info=1)
            s.close()

    def get_socket(self):
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        group_bin = socket.inet_pton(socket.AF_INET6, self._BROADCAST) + b'\0'*4
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, group_bin)
        self._socket = s
        return s

    def get_ip(self):
        return get_public_ipv6()

class LocalNodes(object):

    _active = True
    _nodes4 = None
    _nodes6 = None

    def __init__(self):
        self._nodes = {}
        if not server['localnode_discovery']:
            return
        self._nodes4 = LocalNodes4(self._nodes)
        self._nodes6 = LocalNodes6(self._nodes)

    def cleanup(self):
        if self._active:
            for id in list(self._nodes.keys()):
                if not can_connect(self._nodes[id]):
                    del self._nodes[id]
                if not self._active:
                    break

    def get(self, user_id):
        if user_id in self._nodes:
            if can_connect(self._nodes[user_id]):
                return self._nodes[user_id]

    def join(self):
        self._active = False
        if self._nodes4:
            self._nodes4.join()
        if self._nodes6:
            self._nodes6.join()
