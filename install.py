#!/usr/bin/env python
from __future__ import with_statement

from contextlib import closing
import json
import os
import sys
import tarfile
import urllib2


release_url = "http://downloads.openmedialibrary.com/release.json"
release_url = "http://c.local/oml/release.json"

def get_release():
    with closing(urllib2.urlopen(release_url)) as u:
        data = json.load(u)
    return data

def download(url, filename):
    dirname = os.path.dirname(filename)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
    print url, filename
    with open(filename, 'w') as f:
        with closing(urllib2.urlopen(url)) as u:
            data = u.read(4096)
            while data:
                f.write(data)
                data = u.read(4096)

def install_launchd(base):
    plist = os.path.expanduser('~/Library/LaunchAgents/com.openmedialibrary.loginscript.plist')
    with open(plist, 'w') as f:
        f.write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.openmedialibrary.loginscript</string>
        <key>ProgramArguments</key>
        <array>
            <string>%s/ctl</string>
            <string>start</string>
        </array>
        <key>RunAtLoad</key>
        <true/>
    </dict>
</plist>''' % base)

    os.system('launchctl load "%s"' % plist)
    os.system('launchctl start com.openmedialibrary.loginscript')

if __name__ == '__main__':
    if len(sys.argv) == 1:
        target = os.path.join(os.curdir, 'openmedialibrary')
    elif len(sys.argv) != 2:
        print "usage: %s target" % sys.argv[0]
        sys.exit(1)
    else:
        target = sys.argv[1]
    target = os.path.normpath(os.path.join(os.path.abspath(target)))
    if not os.path.exists(target):
        os.makedirs(target)
    os.chdir(target)
    release = get_release()
    packages = ['contrib', 'openmedialibrary']
    if sys.platform == 'darwin':
        packages.append('platform')
    for package in packages:
        package_tar = '%s.tar.bz2' % package
        download(release[package]['url'], package_tar)
        tar = tarfile.open(package_tar)
        tar.extractall()
        tar.close()
        os.unlink(package_tar)
    os.symlink('openmedialibrary/ctl', 'ctl')
    with open('release.json', 'w') as fd:
        json.dump(release, fd, indent=2)

    if sys.platform == 'darwin':
        cmd = 'Open OpenMediaLibrary.command'
        with open(cmd, 'w') as fd:
            fd.write('''#!/bin/sh
cd `dirname "$0"`
./ctl start
./ctl open
''')
        os.chmod(cmd, 0755)
        install_launchd(target)
    elif sys.platform == 'linux2':
        #fixme, do only if on debian/ubuntu
        os.sysrem('sudo apt-get install python-imaging python-setproctitle python-simplejson')
