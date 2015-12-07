#!/usr/bin/env python3
import os
from os.path import dirname, abspath
import subprocess
import time
import webbrowser

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

base = dirname(dirname(dirname(abspath(__file__))))
icon = os.path.join(base, 'openmedialibrary/static/png/oml.png')
title = "Open Media Library"
ctl = base + '/ctl'

class OMLIcon:
    menu = None

    def __init__(self):
        self.icon = Gtk.StatusIcon()
        self.icon.set_from_file(icon)
        self.icon.set_title(title)
        self.icon.connect("activate", self._click)
        p = subprocess.Popen([ctl, 'start'])
        GLib.timeout_add_seconds(1, self._open, None)

    def _click(self, icon):
        if self.menu:
            self.menu.destroy()
            self.menu = None
        else:
            button = 1
            time = Gtk.get_current_event_time()
            menu = Gtk.Menu()
            about = Gtk.MenuItem(label="Open")
            about.connect("activate", self._open)
            menu.append(about)
            quit = Gtk.MenuItem(label="Quit")
            quit.connect("activate", self._quit)
            menu.append(quit)
            menu.show_all()
            menu.popup(None, None, self.icon.position_menu, icon, button, time)
            self.menu = menu

    def _quit(self, q):
        Gtk.main_quit()
        p = subprocess.Popen([ctl, 'stop'])
        self.menu = None

    def _open(self, *args):
        url = 'file://' + base + '/openmedialibrary/static/html/load.html'
        webbrowser.open_new_tab(url)
        self.menu = None

OMLIcon()
Gtk.main()
