# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import subprocess
from os.path import join, exists, dirname
import os

from flask.ext.script import Command, Option

import settings

root_dir = dirname(settings.base_dir)

def run(*cmd):
    p = subprocess.Popen(cmd)
    p.wait()
    return p.returncode

def get(*cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, error = p.communicate()
    return stdout

def r(*cmd):
    print ' '.join(cmd)
    return subprocess.call(cmd)

def version(module):
    os.chdir(join(root_dir, module))
    version = get('git', 'log', '-1', '--format=%cd', '--date=iso').split(' ')[0].replace('-', '')
    version += '-' + get('git', 'rev-list', 'HEAD', '--count').strip()
    version += '-' + get('git', 'describe', '--always').strip()
    os.chdir(root_dir)
    return version


class Version(Command):
        """
            Print current version
        """
        def run(self):
            print version('openmedialibrary')

class Debug(Command):
        """
            Start in debug mode
        """
        def run(self):
            pass

class Start(Command):
        """
            Start Open Media Libary
        """
        def run(self):
            pass

class Stop(Command):
        """
            Stop Open Media Libary
        """
        def run(self):
            pass

class Update(Command):
        """
            Update to latest development version
        """
        def run(self):
            pass

class PostUpdate(Command):
        """
            Called by update to fix stuff
        """
        def get_options(self):
            return [
                Option('-o', '--old', dest='old'),
                Option('-n', '--new', dest='new'),
            ]

        def run(selfi, old, new):
            if old <= '20140506-2-796c77b' and new > '20140506-2-796c77b':
                print 'migrate database content'
                import item.models
                for i in item.models.Item.query:
                    if 'mainid' in i.meta:
                        mainid = i.meta.pop('mainid')
                        pid = {'isbn10': 'isbn', 'isbn13': 'isbn'}.get(mainid, mainid)
                        i.meta['primaryid'] = [pid, i.meta[mainid]]
                    isbns = i.meta.get('isbn', [])
                    for key in ('isbn10', 'isbn13'):
                        if key in i.meta:
                             isbns.append(i.meta.pop(key))
                    if isbns:
                        i.meta['isbn'] = isbns
                    for key in ('asin', 'lccn', 'olid', 'oclc'):
                        if key in i.meta and isinstance(i.meta[key], basestring):
                            i.meta[key] = [i.meta[key]]
                    i.update()

class Setup(Command):
        """
            Setup new node
        """
        def run(self):
            r('./ctl', 'db', 'upgrade')
            import setup
            setup.create_default_lists()
            settings.db.session.connection().execute("PRAGMA journal_mode=WAL")
            settings.db.session.commit()

class UpdateStatic(Command):
        """
            Update static files
        """
        def run(self):
            oxjs = os.path.join(settings.static_path, 'oxjs')
            if not os.path.exists(oxjs):
                r('git', 'clone', 'https://git.0x2620.org/oxjs.git', oxjs)
            elif os.path.exists(os.path.join(oxjs, '.git')):
                os.system('cd "%s" && git pull' % oxjs)
            r('python2', os.path.join(oxjs, 'tools', 'build', 'build.py'))
            r('python2', os.path.join(settings.static_path, 'py', 'build.py'))

class Release(Command):
        """
            Release new version
        """
        def run(self):
            print 'checking...'
            import os
            import json
            import hashlib
            import ed25519

            os.chdir(root_dir)

            with open(os.path.expanduser('~/Private/openmedialibrary_release.key')) as fd:
                SIG_KEY=ed25519.SigningKey(fd.read())
            SIG_ENCODING='base64'

            def sign(release):
                value = []
                for module in sorted(release['modules']):
                    value += ['%s/%s' % (release['modules'][module]['version'], release['modules'][module]['sha1'])]
                value = '\n'.join(value)
                sig = SIG_KEY.sign(value, encoding=SIG_ENCODING)
                release['signature'] = sig

            def sha1sum(path):
                h = hashlib.sha1()
                with open(path) as fd:
                    for chunk in iter(lambda: fd.read(128*h.block_size), ''):
                        h.update(chunk)
                return h.hexdigest()

            MODULES = ['platform', 'openmedialibrary']
            VERSIONS = {module:version(module) for module in MODULES}

            EXCLUDE=[
                '--exclude', '.git', '--exclude', '.bzr',
                '--exclude', '.*.swp', '--exclude', '._*', '--exclude', '.DS_Store'
            ]

            #run('./ctl', 'update_static')
            for module in MODULES:
                tar = join('updates', '%s-%s.tar.bz2' % (module, VERSIONS[module]))
                if not exists(tar):
                    cmd = ['tar', 'cvjf', tar, '%s/' % module] + EXCLUDE
                    if module in ('openmedialibrary', ):
                        cmd += ['--exclude', '*.pyc']
                    if module == 'openmedialibrary':
                        cmd += ['--exclude', 'oxjs/examples', '--exclude', 'gunicorn.pid']
                    run(*cmd)
            release = {}
            release['modules'] = {module: {
                'name': '%s-%s.tar.bz2' % (module, VERSIONS[module]),
                'version': VERSIONS[module],
                'sha1': sha1sum(join('updates', '%s-%s.tar.bz2' % (module, VERSIONS[module])))
            } for module in MODULES}
            sign(release)
            with open('updates/release.json', 'w') as fd:
                json.dump(release, fd, indent=2)
            print 'signed latest release in updates/release.json'
