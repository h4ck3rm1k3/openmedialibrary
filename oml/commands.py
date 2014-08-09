# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import subprocess
from os.path import join, exists, dirname
import os
import sys

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
    if os.path.exists(join(root_dir, module, '.git')):
        os.chdir(join(root_dir, module))
        version = get('git', 'log', '-1', '--format=%cd', '--date=iso').split(' ')[0].replace('-', '')
        version += '-' + get('git', 'rev-list', 'HEAD', '--count').strip()
        version += '-' + get('git', 'describe', '--always').strip()
        os.chdir(root_dir)
    else:
        version = settings.release['modules'][module]['version']
    return version

def command_version(*args):
    """
        Print current version
    """
    print version('openmedialibrary')

def command_debug(*args):
    """
        Start in debug mode
    """
    pass

def command_start(*args):
    """
        Start Open Media Libary
    """
    pass

def command_stop(*args):
    """
        Stop Open Media Libary
    """
    pass

def command_install_update(*args):
    """
        Install available updates
    """
    import update
    if not update.install():
        print "UPDATE FAILED"
        sys.exit(1)

def command_update(*args):
    """
        Update to latest development version
    """
    import update
    if not (update.download() and update.install()):
        print "UPDATE FAILED"

def command_postupdate(*args):
    """
        Called after update with -o old -n new
    """
    def run(*args):
        o, old, n, new = args
        if o != '-o' or n != '-n':
            print 'usage: -o oldversion -n newversion'
            sys.exit(1)
        if old <= '20140521-65-e14c686' and new > '20140521-65-e14c686':
            if not os.path.exists(settings.db_path):
                r('./ctl', 'setup')
        if old <= '20140525-92-eac91e7' and new > '20140525-92-eac91e7':
            import user.models
            for u in user.models.User.query:
                u.update_name()
                u.save()
            import item.models
            for f in item.models.File.query:
                changed = False
                for key in ('mediastate', 'coverRatio', 'previewRatio'):
                    if key in f.info:
                        del f.info[key]
                        changed = True
                if changed:
                    f.save()
        if old <= '20140526-118-d451eb3' and new > '20140526-118-d451eb3':
            import item.models
            item.models.Find.query.filter_by(key='list').delete()

def command_setup(*args):
    """
        Setup new node
    """
    import setup
    setup.create_db()
    setup.create_default_lists()

def command_update_static(*args):
    """
        Update static files
    """
    oxjs = os.path.join(settings.static_path, 'oxjs')
    if not os.path.exists(oxjs):
        r('git', 'clone', 'https://git.0x2620.org/oxjs.git', oxjs)
    elif os.path.exists(os.path.join(oxjs, '.git')):
        os.system('cd "%s" && git pull' % oxjs)
    r('python2', os.path.join(oxjs, 'tools', 'build', 'build.py'))
    r('python2', os.path.join(settings.static_path, 'py', 'build.py'))

def command_release(*args):
    """
        Release new version
    """
    print 'checking...'
    import os
    import json
    import hashlib
    import ed25519

    os.chdir(root_dir)

    with open(os.path.expanduser('~/.openmedialibrary_release.key')) as fd:
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

def command_shell(*args):
    '''
        Runs a Python shell inside the application context.
    '''
    context = None
    banner = 'Open Media Library'

    import db
    with db.session():
        # Try BPython
        try:
            from bpython import embed
            embed(banner=banner, locals_=context)
            return
        except ImportError:
            pass

        # Try IPython
        try:
            try:
                # 0.10.x
                from IPython.Shell import IPShellEmbed
                ipshell = IPShellEmbed(banner=banner)
                ipshell(global_ns=dict(), local_ns=context)
            except ImportError:
                # 0.12+
                from IPython import embed
                embed(banner1=banner, user_ns=context)
            return
        except ImportError:
            pass

        import code
        # Use basic python shell
        code.interact(banner, local=context)
