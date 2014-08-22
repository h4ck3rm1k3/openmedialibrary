# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division, with_statement

from contextlib import closing
import json
import os
import tarfile
import urllib2
import shutil
import subprocess

import ed25519
import ox

import settings

ENCODING='base64'
RELEASE_URL = 'http://downloads.openmedialibrary.com/release.json'

def verify(release):
    vk = ed25519.VerifyingKey(settings.OML_UPDATE_KEY, encoding=ENCODING)
    value = []
    for module in sorted(release['modules']):
        value += [str('%s/%s' % (release['modules'][module]['version'], release['modules'][module]['sha1']))]
    value = '\n'.join(value)
    sig = str(release['signature'])
    try:
        vk.verify(sig, value, encoding=ENCODING)
    except ed25519.BadSignatureError:
        return False
    return True

def get(url, filename=None):
    request = urllib2.Request(url, headers={
        'User-Agent': settings.USER_AGENT
    })
    with closing(urllib2.urlopen(request)) as u:
        if not filename:
            data = u.read()
            return data
        else:
            dirname = os.path.dirname(filename)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(filename, 'w') as fd:
                data = u.read(4096)
                while data:
                    fd.write(data)
                    data = u.read(4096)

def check():
    if settings.release:
        release_data = get(RELEASE_URL)
        release = json.loads(release_data)
        old = settings.release['modules']['openmedialibrary']['version']
        new = release['modules']['openmedialibrary']['version']
        return verify(release) and old < new
    return False

def download():
    if not os.path.exists(os.path.join(settings.config_path, 'release.json')):
        return True
    release_data = get(RELEASE_URL)
    release = json.loads(release_data)
    old = settings.release['modules']['openmedialibrary']['version']
    new = release['modules']['openmedialibrary']['version']
    if verify(release) and old < new:
        ox.makedirs(settings.updates_path)
        os.chdir(os.path.dirname(settings.base_dir))
        current_files = {'release.json'}
        for module in release['modules']:
            if release['modules'][module]['version'] > settings.release['modules'][module]['version']:
                module_tar = os.path.join(settings.updates_path, release['modules'][module]['name'])
                url = RELEASE_URL.replace('release.json', release['modules'][module]['name'])
                if not os.path.exists(module_tar):
                    print 'download', os.path.basename(module_tar)
                    get(url, module_tar)
                    if ox.sha1sum(module_tar) != release['modules'][module]['sha1']:
                        os.unlink(module_tar)
                        return False
                current_files.add(os.path.basename(module_tar))
        with open(os.path.join(settings.updates_path, 'release.json'), 'w') as fd:
            fd.write(release_data)
        for f in set(os.walk(settings.updates_path).next()[2])-current_files:
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
    old = settings.release['modules']['openmedialibrary']['version']
    new = release['modules']['openmedialibrary']['version']
    if verify(release) and old < new:
        os.chdir(os.path.dirname(settings.base_dir))
        for module in release['modules']:
            if release['modules'][module]['version'] > settings.release['modules'][module]['version']:
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
                    shutil.move(module, '%s_old' % module)
                    shutil.move(os.path.join(new, module), module)
                    shutil.rmtree('%s_old' % module)
                    shutil.rmtree(new)
                else:
                    return False
        shutil.copy(os.path.join(settings.updates_path, 'release.json'), os.path.join(settings.config_path, 'release.json'))
        for cmd in [
                ['./ctl', 'stop'],
                ['./ctl', 'setup'],
                ['./ctl', 'postupdate', '-o', old, '-n', new]
            ]:
            subprocess.call(cmd)
        return True
    return True
