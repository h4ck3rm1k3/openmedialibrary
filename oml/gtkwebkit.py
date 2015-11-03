#!/usr/bin/python3
import gi
gi.require_version('WebKit2', '4.0')
from gi.repository import WebKit2, Gtk
import os
import subprocess

icon = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../static/png/oml.png')
title = "Open Media Library"
base = os.path.expanduser('~/.local/share/openmedialibrary')


wnd = Gtk.Window()
wnd.set_icon_from_file(icon)

ctx = WebKit2.WebContext.get_default()
web = WebKit2.WebView.new_with_context(ctx)

wnd.connect("destroy", Gtk.main_quit)
wnd.add(web)
wnd.set_wmclass(title, title)
wnd.set_title(title)
wnd.set_default_size(1366, 768)
wnd.show_all()

url = 'file://' + base + '/openmedialibrary/static/html/load.html'
web.load_uri(url)

ctl = base + '/ctl'
p = subprocess.Popen([ctl, 'start'])
Gtk.main()
p = subprocess.Popen([ctl, 'stop'])
