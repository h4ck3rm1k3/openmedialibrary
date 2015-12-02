import os
import subprocess
from threading import Thread
import distutils

import stem
from stem.control import Controller
import settings

import state
import utils

import logging
logger = logging.getLogger(__name__)

class TorDaemon(Thread):
    def __init__(self):
        self._status = []
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def create_torrc(self):
        defaults = os.path.join(settings.config_path, 'torrc-defaults')
        torrc = os.path.join(settings.config_path, 'torrc')
        if not os.path.exists(defaults):
            with open(defaults, 'w') as fd:
                fd.write('''
AvoidDiskWrites 1
# Where to send logging messages.  Format is minSeverity[-maxSeverity]
# (stderr|stdout|syslog|file FILENAME).
Log notice stdout
SocksPort 9830
ControlPort 9831
CookieAuthentication 1
                '''.strip())
        if not os.path.exists(torrc):
            with open(torrc, 'w') as fd:
                fd.write('''
DataDirectory {base}/TorData
DirReqStatistics 0
                '''.strip().format(base=settings.config_path))
        return defaults, torrc

    def get_tor(self):
        def cmd_exists(cmd):
            return subprocess.call("type " + cmd, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0
        for path in (
            '/Applications/TorBrowser.app/TorBrowser/Tor/tor',
        ):
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        start = os.path.expanduser('~/.local/share/applications/start-tor-browser.desktop')
        if os.path.exists(start):
            with open(start) as fd:
                e = [line for line in fd.read().split('\n') if line.startswith('Exec')]
                if e:
                    try:
                        base = os.path.dirname(e[0].split('"')[1])
                        path = os.path.join(base, 'TorBrowser', 'Tor', 'tor')
                        if os.path.isfile(path) and os.access(path, os.X_OK):
                            return path
                    except:
                        pass
        return distutils.spawn.find_executable('tor')

    def run(self):
        defaults, torrc = self.create_torrc()
        tor = self.get_tor()
        if not tor:
            self._status.append('No tor binary found. Please install TorBrowser or tor')
        else:
            cmd = [tor, '--defaults-torrc', defaults, '-f', torrc]
            self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True)
            for line in self.p.stdout:
                self._status.append(line)
                logger.debug(line)
            self.p = None

    def shutdown(self):
        if self.p:
            self.p.kill()

    def status(self, max_lines=50):
        return ''.join(self._status[-max_lines:])

class Tor(object):
    _shutdown = False
    connected = False
    controller = None
    daemon = None
    socks_port = 9150

    def __init__(self):
        if not self.connect():
            self.reconnect()

    def connect(self):
        self.connected = False
        self.dir = os.path.join(settings.config_path, 'tor')
        connected = False
        for port in (9831, 9151):
            try:
                self.controller = Controller.from_port('127.0.0.1', port)
                connected = True
                break
            except stem.SocketError:
                pass
        if not connected:
            if not self.daemon:
                logger.debug("start own tor process")
                self.daemon = TorDaemon()
                logger.debug("daemon %s", self.daemon)
                return self.connect()
            logger.debug("Failed to connect to system or own tor process.")
            return False
        try:
            self.controller.authenticate()
        except stem.connection.MissingPassword:
            logger.debug("TOR requires a password")
            return False
        except stem.connection.PasswordAuthFailed:
            logger.debug("invalid tor password")
            return False
        self.controller.add_event_listener(self.event_listener)
        self.controller.add_status_listener(self.status_listener)
        self.connected = True
        self.socks_port = int(self.controller.get_conf('SocksPort').split(' ')[0])
        self.publish()
        state.online = self.is_online()
        return True

    def reconnect(self):
        if not self.connect():
            if state.main:
                state.main.call_later(1, self.reconnect)

    def status_listener(self, controller, status, timestamp):
        if status == 'Closed':
            if not self._shutdown:
                self.connected = False
                state.online = False
                self.reconnect()
        else:
            logger.debug('unknonw change %s', status)

    def event_listener(self, event):
        print('EVENT', event)

    def shutdown(self):
        self._shutdown = True
        try:
            self.unpublish()
            if self.controller:
                #self.controller.remove_event_listener(self.connection_change)
                self.controller.close()
            if self.daemon:
                self.daemon.shutdown()
        except:
            logger.debug('shutdown exception', exc_info=1)
            pass
        self.connected = False

    def publish(self):
        logger.debug("publish tor node")
        if not self.connected:
            return False
        controller = self.controller
        logger.debug("FIXME: dont remove/add service if already defined")
        controller.remove_hidden_service(self.dir)
        result = controller.create_hidden_service(
            self.dir,
            settings.server_defaults['node_port'],
            target_port=settings.server['node_port']
        )
        logger.debug('published node as https://%s:%s', result.hostname, settings.server_defaults['node_port'])
        '''
        with open(settings.ssl_key_path) as fd:
            key_content = fd.read()
        ports = {9851: settings.server['node_port']}
        response = controller.create_ephemeral_hidden_service(ports,
                key_type='RSA1024', key_content=key_content,
                detached=True, await_publication = True)
        logger.debug('published node as https://%s.onion:%s',
                     settings.USER_ID, settings.server_defaults['node_port'])
        '''

    def unpublish(self):
        if not self.connected:
            return False
        if self.controller:
            self.controller.remove_hidden_service(self.dir)
        state.online = False

    def is_online(self):
        return self.connected and self.controller.is_alive() and utils.can_connect_dns()
