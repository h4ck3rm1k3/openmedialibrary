# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import socket
import thread
import json
import struct
from threading import Thread

from settings import preferences, server, USER_ID
from node.utils import get_public_ipv6

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

class LocalNodes(Thread):
    _active = True
    _nodes = {}

    _BROADCAST = "ff02::1"
    _PORT = 9851 
    TTL = 2

    def __init__(self, app):
        self._app = app
        Thread.__init__(self)
        self.daemon = True
        self.start()
        self.host = get_public_ipv6()
        self.send()

    def send(self):
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

        ttl = struct.pack('@i', self.TTL)
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl)
        message = json.dumps({
            'id': USER_ID,
            'username': preferences.get('username', 'anonymous'),
            'host': self.host,
            'port': server['node_port'],
        })
        s.sendto(message + '\0', (self._BROADCAST, self._PORT))

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
            data = self.validate(data)
            if data:
                if data['id'] not in self._nodes:
                    thread.start_new_thread(self.new_node, (data, ))
                else:
                    print 'UPDATE NODE', data
                self._nodes[data['id']] = data

    def validate(self, data):
        try:
            data = json.loads(data)
        except:
            return None
        for key in ['id', 'username', 'host', 'port']:
            if key not in data:
                return None
        return data

    def get(self, user_id):
        if user_id in self._nodes:
            if can_connect(self._nodes[user_id]):
                return self._nodes[user_id]

    def new_node(self, data):
        print 'NEW NODE', data
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
        self.receive()

    def join(self):
        self._active = False
        return Thread.join(self)
