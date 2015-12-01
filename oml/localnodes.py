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
from tor_request import get_opener
import settings

import logging
logger = logging.getLogger(__name__)

def can_connect(data):
    try:
        opener = get_opener(data['id'])
        headers = {
            'User-Agent': settings.USER_AGENT,
            'X-Node-Protocol': settings.NODE_PROTOCOL,
            'Accept-Encoding': 'gzip',
        }
        if ':' in data['host']:
            url = 'https://[{host}]:{port}'.format(**data)
        else:
            url = 'https://{host}:{port}'.format(**data)
        opener.addheaders = list(zip(headers.keys(), headers.values()))
        opener.timeout = 1
        r = opener.open(url)
        version = r.headers.get('X-Node-Protocol', None)
        if version != settings.NODE_PROTOCOL:
            logger.debug('version does not match local: %s remote %s', settings.NODE_PROTOCOL, version)
            return False
        c = r.read()
        return True
    except:
        pass
        #logger.debug('failed to connect to local node %s', data, exc_info=1)
    return False

class LocalNodesBase(Thread):

    _PORT = 9851 
    _TTL = 1
    _TIMEOUT = 30

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
                'id': USER_ID,
                'username': preferences.get('username', 'anonymous'),
                'host': self.host,
                'port': server['node_port']
            })
            packet = message.encode()
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
                s.settimeout(self._TIMEOUT)
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
                pass
            except:
                if self._active:
                    logger.debug('receive failed. restart later', exc_info=1)
                    time.sleep(10)
            finally:
                if self._active:
                    now = time.mktime(time.localtime())
                    if now - last > 60:
                        last = now
                        _thread.start_new_thread(self.send, ())

    def verify(self, data):
        try:
            message = json.loads(data.decode())
        except:
            return None
        for key in ['id', 'username', 'host', 'port']:
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
                u = user.models.User.get(data['id'])
                if u:
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
            #logger.debug('send4 %s', packet)
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
            #logger.debug('send6 %s', packet)
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
        #self._nodes6 = LocalNodes6(self._nodes)

    def cleanup(self):
        if self._active:
            for id in list(self._nodes.keys()):
                if not can_connect(self._nodes[id]):
                    with db.session():
                        u = user.models.User.get(id)
                        if u and 'local' in u.info:
                            del u.info['local']
                            u.save()
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
