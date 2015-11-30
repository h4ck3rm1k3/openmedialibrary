# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


from contextlib import closing
import json
import os
import tarfile
import urllib.request, urllib.error, urllib.parse
import shutil
import subprocess
import sys

import ed25519
import ox
from oxtornado import actions

import settings

import logging

logger = logging.getLogger(__name__)


ENCODING='base64'

def verify(release):
    vk = ed25519.VerifyingKey(settings.OML_UPDATE_KEY, encoding=ENCODING)
    value = []
    for module in sorted(release['modules']):
        value += [str('%s/%s' % (release['modules'][module]['version'], release['modules'][module]['sha1']))]
    value = '\n'.join(value)
    value = value.encode()
    sig = release['signature'].encode()
    try:
        vk.verify(sig, value, encoding=ENCODING)
    except ed25519.BadSignatureError:
        return False
    return True

def get(url, filename=None):
    request = urllib.request.Request(url, headers={
        'User-Agent': settings.USER_AGENT
    })
    with closing(urllib.request.urlopen(request)) as u:
        if not filename:
            data = u.read()
            return data
        else:
            dirname = os.path.dirname(filename)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(filename, 'wb') as fd:
                data = u.read(4096)
                while data:
                    fd.write(data)
                    data = u.read(4096)

def check():
    if settings.release:
        release_data = get(settings.server.get('release_url',
            'http://downloads.openmedialibrary.com/release.json'))
        release = json.loads(release_data.decode('utf-8'))
        old = current_version('openmedialibrary')
        new = release['modules']['openmedialibrary']['version']
        return verify(release) and old < new
    return False

def current_version(module):
    if 'modules' in settings.release \
        and module in settings.release['modules'] \
        and 'version' in settings.release['modules'][module]:
        version = settings.release['modules'][module]['version']
    else:
        version = ''
    return version

def download():
    if not os.path.exists(os.path.join(settings.config_path, 'release.json')):
        return True
    release_data = get(settings.server.get('release_url'))
    release = json.loads(release_data.decode('utf-8'))
    if verify(release):
        ox.makedirs(settings.updates_path)
        os.chdir(os.path.dirname(settings.base_dir))
        current_files = {'release.json'}
        for module in release['modules']:
            if release['modules'][module]['version'] > current_version(module):
                module_tar = os.path.join(settings.updates_path, release['modules'][module]['name'])
                base_url = settings.server.get('release_url').rsplit('/', 1)[0]
                url = '/'.join([base_url, release['modules'][module]['name']])
                if not os.path.exists(module_tar):
                    print('downloading', os.path.basename(module_tar))
                    get(url, module_tar)
                    if ox.sha1sum(module_tar) != release['modules'][module]['sha1']:
                        os.unlink(module_tar)
                        return False
                current_files.add(os.path.basename(module_tar))
        with open(os.path.join(settings.updates_path, 'release.json'), 'wb') as fd:
            fd.write(release_data)
        for f in set(next(os.walk(settings.updates_path))[2])-current_files:
            os.unlink(os.path.join(settings.updates_path, f))
        return True
    return True

def install():
    if not os.path.exists(os.path.join(settings.updates_path, 'release.json')):
        return True
    if not os.path.exists(os.path.join(settings.config_path, 'release.json')):
        return True
    with open(os.path.join(settings.updates_path, 'release.json')) as fd:
        release = json.load(fd)
    old_version = current_version('openmedialibrary')
    new_version = release['modules']['openmedialibrary']['version']
    if verify(release) and old_version < new_version:
        os.chdir(os.path.dirname(settings.base_dir))
        for module in release['modules']:
            if release['modules'][module]['version'] > current_version(module):
                module_tar = os.path.join(settings.updates_path, release['modules'][module]['name'])
                if os.path.exists(module_tar) and ox.sha1sum(module_tar) == release['modules'][module]['sha1']:
                    #tar fails if old platform is moved before extract
                    new = '%s_new' % module
                    ox.makedirs(new)
                    os.chdir(new)
                    tar = tarfile.open(module_tar)
                    tar.extractall()
                    tar.close()
                    os.chdir(os.path.dirname(settings.base_dir))
                    module_old = '%s_old' % module
                    if os.path.exists(module):
                        shutil.move(module, module_old)
                    shutil.move(os.path.join(new, module), module)
                    if os.path.exists(module_old):
                        shutil.rmtree(module_old)
                    shutil.rmtree(new)
                else:
                    os.unlink(module_tar)
                    return False
        shutil.copy(os.path.join(settings.updates_path, 'release.json'), os.path.join(settings.config_path, 'release.json'))
        for cmd in [
                ['./ctl', 'stop'],
                ['./ctl', 'setup'],
                ['./ctl', 'postupdate', '-o', old_version, '-n', new_version]
            ]:
            subprocess.call(cmd)
        upgrade_app()
        return True
    return True

def get_app_version(app):
    plist = app + '/Contents/Info.plist'
    if os.path.exists(plist):
        cmd = ['defaults', 'read', plist, 'CFBundleShortVersionString']
        return subprocess.check_output(cmd).strip()

def upgrade_app():
    if sys.platform == 'darwin':
        base = os.path.dirname(settings.base_dir)
        bundled_app = base + 'platform/Darwin/Applications/Open Media Library.app'
        app = '/Applications/Open Media Library.app'
        version = get_app_version(app)
        current_version = get_app_version(bundled_app)
        if version and current_version and version != current_version:
            try:
                shutil.rmtree(app)
                shutil.copytree(bundled_app, app)
            except:
                logger.debug('Failed to update Application', exc_info=1)

def getVersion(data):
    '''
        check if new version is available
    '''
    response = {
        'current': settings.MINOR_VERSION,
        'upgrade': False,
    }
    if settings.MINOR_VERSION == 'git':
        cmd = ['git', 'rev-parse', '@']
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, close_fds=True)
        stdout, stderr = p.communicate()
        current = stdout.strip()
        cmd = ['git', 'ls-remote', 'origin', '-h', 'refs/heads/master']
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, close_fds=True)
        stdout, stderr = p.communicate()
        new = stdout.strip()[:40]
        response['update'] = current != new
    else:
        if not os.path.exists(os.path.join(settings.updates_path, 'release.json')):
            return response
        if not os.path.exists(os.path.join(settings.config_path, 'release.json')):
            return response
        with open(os.path.join(settings.updates_path, 'release.json')) as fd:
            release = json.load(fd)
        current = current_version('openmedialibrary')
        response['current'] = current
        new = release['modules']['openmedialibrary']['version']
        response['new'] = new
        response['update'] = current < new
    return response
actions.register(getVersion, cache=False)

def restart(data):
    '''
        restart (and upgrade if upgrades are available)
    '''
    subprocess.Popen([os.path.join(settings.base_dir, 'ctl'), 'restart'], close_fds=True)
    return {}
actions.register(restart, cache=False)
