import os
import sys
import settings

from utils import run, makefolder

root_dir = os.path.dirname(settings.base_dir)

def install_launcher():
    if sys.platform == 'darwin':
        install_launchd()
    elif sys.platform.startswith('linux'):
        install_xdg()
    else:
        print('no launcher integration supported for %s' % sys.platform)

def uninstall_launcher():
    if sys.platform == 'darwin':
        name = 'com.openmedialibrary.loginscript'
        plist = os.path.expanduser('~/Library/LaunchAgents/%s.plist'%name)
        if os.path.exists(plist):
            run('launchctl', 'stop', name)
            run('launchctl', 'unload', plist)
            os.unlink(plist)
    elif sys.platform.startswith('linux'):
        for f in map(os.path.expanduser, [
            '~/.local/share/applications/openmedialibrary.desktop',
            '~/.config/autostart/openmedialibrary.desktop'
        ]):
            if os.path.exists(f):
                os.unlink(f)

def install_launchd():
    name = 'com.openmedialibrary.loginscript'
    plist = os.path.expanduser('~/Library/LaunchAgents/%s.plist'%name)
    if os.path.exists(plist):
        run('launchctl', 'stop', name)
        run('launchctl', 'unload', plist)
    with open(plist, 'w') as f:
        f.write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>%s</string>
    <key>ProgramArguments</key>
    <array>
        <string>%s/ctl</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>''' % (name, root_dir))
    run('launchctl', 'load', plist)
    run('launchctl', 'start', name)

def install_xdg():
    app = os.path.expanduser('~/.local/share/applications/openmedialibrary.desktop')
    with open(app, 'w') as fd:
        fd.write('''[Desktop Entry]
Type=Application
Name=Open Media Library
Comment=Open Media Library
Exec=%(base)s/ctl open
Icon=%(base)s/openmedialibrary/static/png/oml.png
Terminal=false
Categories=Network;FileTransfer;P2P;
''' % {'base': root_dir})

    start = os.path.expanduser('~/.config/autostart/openmedialibrary.desktop')
    makefolder(start)
    with open(start, 'w') as fd:
            fd.write('''[Desktop Entry]
Type=Application
Name=Start Open Media Library
Exec=%(base)s/ctl start
Icon=%(base)s/openmedialibrary/static/png/oml.png
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
''' % {'base': root_dir})
