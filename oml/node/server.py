# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from datetime import datetime
from socketserver import ThreadingMixIn
from threading import Thread
import base64
import gzip
import hashlib
import http.server
import io
import json
import os
import socket
import socketserver

from Crypto.PublicKey import RSA
from Crypto.Util.asn1 import DerSequence
from OpenSSL.crypto import dump_privatekey, FILETYPE_ASN1
from OpenSSL.SSL import (
    Context, Connection, TLSv1_2_METHOD,
    VERIFY_PEER, VERIFY_FAIL_IF_NO_PEER_CERT, VERIFY_CLIENT_ONCE
)

import db
import settings
import state
import user

from . import nodeapi
from .sslsocket import fileobject

import logging
logger = logging.getLogger(__name__)


def get_service_id(key):
    '''
    service_id is the first half of the sha1 of the rsa public key encoded in base32
    '''
    # compute sha1 of public key and encode first half in base32
    pub_der = DerSequence()
    pub_der.decode(dump_privatekey(FILETYPE_ASN1, key))
    public_key = RSA.construct((pub_der._seq[1], pub_der._seq[2])).exportKey('DER')[22:]
    service_id = base64.b32encode(hashlib.sha1(public_key).digest()[:10]).lower().decode()
    return service_id

class TLSTCPServer(socketserver.TCPServer):

    def _accept(self, connection, x509, errnum, errdepth, ok):
        # client_id is validated in request
        return True

    def __init__(self, server_address, HandlerClass, bind_and_activate=True):
        socketserver.TCPServer.__init__(self, server_address, HandlerClass)
        ctx = Context(TLSv1_2_METHOD)
        ctx.use_privatekey_file (settings.ssl_key_path)
        ctx.use_certificate_file(settings.ssl_cert_path)
        # only allow clients with cert:
        ctx.set_verify(VERIFY_PEER | VERIFY_CLIENT_ONCE | VERIFY_FAIL_IF_NO_PEER_CERT, self._accept)
        #ctx.set_verify(VERIFY_PEER | VERIFY_CLIENT_ONCE, self._accept)
        self.socket = Connection(ctx, socket.socket(self.address_family, self.socket_type))
        if bind_and_activate:
            self.server_bind()
            self.server_activate()

    def shutdown_request(self,request):
        try:
            request.shutdown()
        except:
            pass

class NodeServer(ThreadingMixIn, TLSTCPServer):
    allow_reuse_address = True


def api_call(action, user_id, args):
    with db.session():
        u = user.models.User.get(user_id)
        if action in (
            'requestPeering', 'acceptPeering', 'rejectPeering', 'removePeering'
        ) or (u and u.peered):
            content = getattr(nodeapi, 'api_' + action)(user_id, *args)
        else:
            if u and u.pending:
                logger.debug('ignore request from pending peer[%s] %s (%s)',
                    user_id, action, args)
                content = {}
            else:
                content = None
    return content

class Handler(http.server.SimpleHTTPRequestHandler):

    def setup(self):
        self.connection = self.request
        self.rfile = fileobject(self.connection, 'rb', self.rbufsize)
        self.wfile = fileobject(self.connection, 'wb', self.wbufsize)

    def version_string(self):
        return settings.USER_AGENT

    def log_message(self, format, *args):
        if settings.DEBUG_HTTP:
            logger.debug("%s - - [%s] %s\n", self.address_string(),
                         self.log_date_time_string(), format%args)

    def do_HEAD(self):
        return self.do_GET()

    def do_GET(self):
        import item.models
        id = self.path.split('/')[-1] if self.path.startswith('/get/') else None
        if id and len(id) == 32 and id.isalnum():
            with db.session():
                i = item.models.Item.get(id)
                if not i:
                    self.send_response(404, 'Not Found')
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'404 - Not Found')
                    return
                path = i.get_path()
                mimetype = {
                    'epub': 'application/epub+zip',
                    'pdf': 'application/pdf',
                    'txt': 'text/plain',
                }.get(path.split('.')[-1], None)
                self.send_response(200, 'OK')
                self.send_header('Content-Type', mimetype)
                self.send_header('X-Node-Protocol', settings.NODE_PROTOCOL)
                self.send_header('Content-Length', str(os.path.getsize(path)))
                self.end_headers()
                ct = datetime.utcnow()
                with open(path, 'rb') as f:
                    size = 0
                    while 1:
                        data = f.read(16384)
                        if not data:
                            break
                        size += len(data)
                        self.wfile.write(data)
                        if state.bandwidth:
                            since_ct = (datetime.utcnow() - ct).total_seconds()
                            state.bandwidth.upload(size/since_ct)
                            size = 0
        else:
            self.send_response(200, 'OK')
            self.send_header('Content-type', 'text/plain')
            self.send_header('X-Node-Protocol', settings.NODE_PROTOCOL)
            self.end_headers()
            self.wfile.write('Open Media Library\n'.encode())

    def gzip_data(self, data):
        encoding = self.headers.get('Accept-Encoding')
        if encoding.find('gzip') != -1:
            self.send_header('Content-Encoding', 'gzip')
            bytes_io = io.BytesIO()
            gzip_file = gzip.GzipFile(fileobj=bytes_io, mode='wb')
            gzip_file.write(data)
            gzip_file.close()
            result = bytes_io.getvalue()
            bytes_io.close()
            return result
        else:
            return data

    def gunzip_data(self, data):
        bytes_io = io.BytesIO(data)
        gzip_file = gzip.GzipFile(fileobj=bytes_io, mode='rb')
        result = gzip_file.read()
        gzip_file.close()
        return result

    def do_POST(self):
        '''
            API
            pullChanges     [userid] from [to]
            pushChanges     [index, change]
            requestPeering  username message
            acceptPeering   username message
            rejectPeering   message
            removePeering   message

            ping            responds public ip
        '''
        x509 = self.connection.get_peer_certificate()
        user_id = get_service_id(x509.get_pubkey()) if x509 else None

        content = {}
        try:
            content_len = int(self.headers.get('content-length', 0))
            data = self.rfile.read(content_len)
            if self.headers.get('Content-Encoding') == 'gzip':
                data = self.gunzip_data(data)
        except:
            logger.debug('invalid request', exc_info=1)
            response_status = (500, 'invalid request')
            self.write_response(response_status, content)
            return

        response_status = (200, 'OK')
        if self.headers.get('X-Node-Protocol', '') > settings.NODE_PROTOCOL:
            state.update_required = True
        if self.headers.get('X-Node-Protocol', '') != settings.NODE_PROTOCOL:
            logger.debug('protocol missmatch %s vs %s',
                self.headers.get('X-Node-Protocol', ''), settings.NODE_PROTOCOL)
            logger.debug('headers %s', self.headers)
            content = settings.release
        else:
            try:
                action, args = json.loads(data.decode('utf-8'))
            except:
                logger.debug('invalid data: %s', data, exc_info=1)
                response_status = (500, 'invalid request')
                content = {
                    'status': 'invalid request'
                }
                self.write_response(response_status, content)
                return
            logger.debug('NODE action %s %s (%s)', action, args, user_id)
            if action == 'ping':
                content = {
                    'status': 'ok'
                }
            else:
                content = api_call(action, user_id, args)
                if content is None:
                    content = {'status': 'not peered'}
                    logger.debug('PEER %s IS UNKNOWN SEND 403', user_id)
                    response_status = (403, 'UNKNOWN USER')
                    content = {}
                #else:
                #    logger.debug('RESPONSE %s: %s', action, content)
        self.write_response(response_status, content)

    def write_response(self, response_status, content):
        self.send_response(*response_status)
        self.send_header('X-Node-Protocol', settings.NODE_PROTOCOL)
        self.send_header('Content-Type', 'application/json')
        content = json.dumps(content, ensure_ascii=False).encode('utf-8')
        content = self.gzip_data(content)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

class Server(Thread):
    http_server = None

    def __init__(self):
        Thread.__init__(self)
        address = (settings.server['node_address'], settings.server['node_port'])
        self.http_server = NodeServer(address, Handler)
        self.daemon = True
        self.start()

    def run(self):
        self.http_server.serve_forever()

    def stop(self):
        if self.http_server:
            self.http_server.shutdown()
            self.http_server.socket.close()
        return Thread.join(self)

def start():
    return Server()

