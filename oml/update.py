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

import requests
import ed25519
import ox

import settings

ENCODING='base64'
RELEASE_URL = "http://downloads.openmedialibrary.com/release.json"

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

def download(self, url, filename):
    dirname = os.path.dirname(filename)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(filename, 'w') as f:
        with closing(urllib2.urlopen(url)) as u:
            data = u.read(4096)
            while data:
                f.write(data)
                data = u.read(4096)

def new_version():
    if settings.release:
        r = requests.get(RELEASE_URL)
        release_data = r.content
        release = json.loads(release_data)
        old = settings.release['modules']['openmedialibrary']['version']
        new = release['modules']['openmedialibrary']['version']
        return verify(release) and old < new

def update():
    r = requests.get(RELEASE_URL)
    release_data = r.content
    release = json.loads(release_data)
    old = settings.release['modules']['openmedialibrary']['version']
    new = release['modules']['openmedialibrary']['version']
    if verify(release) and old < new:
        with open(os.path.join(settings.updates_path, 'release.json'), 'w') as fd:
            fd.write(release_data)
        os.chdir(settings.base_dir)
        for module in release['modules']:
            if release['modules'][module]['version'] > settings.release['modules'][module]['version']:
                package_tar = os.path.join(settings.updates_path, release['modules'][module]['name'])
                url = RELEASE_URL.replace('release.json', package_tar)
                download(url, package_tar)
                if ox.sha1sum(package_tar) == release['modules'][module]['sha1']:
                    shutil.move(module, '%s_old' % module)
                    tar = tarfile.open(package_tar)
                    tar.extractall()
                    tar.close()
                    shutil.rmtree('%s_old' % module)
                else:
                    return False
                os.unlink(package_tar)
        with open(os.path.join(settings.config_dir, 'release.json'), 'w') as fd:
            fd.write(release_data)
        cmd = ['./ctl', 'stop']
        subprocess.call(cmd)
        cmd = ['./ctl', 'setup']
        subprocess.call(cmd)
        cmd = ['./ctl', 'postupdate', '-o', old, '-n', new]
        subprocess.call(cmd)
        cmd = ['./ctl', 'start']
        return True
    return True
