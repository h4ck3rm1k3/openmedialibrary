#!/usr/bin/python3
import os
from os.path import dirname, abspath
import subprocess
import webbrowser

import gi
try:
    gi.require_version('WebKit2', '4.0')
except:
    gi.require_version('WebKit2', '3.0')
from gi.repository import WebKit2, Gtk, Gdk


base = dirname(dirname(dirname(abspath(__file__))))
icon = os.path.join(base, 'openmedialibrary/static/png/oml.png')
title = "Open Media Library"

def on_key_press_event(widget, event):
    if event.state & Gdk.ModifierType.CONTROL_MASK and event.keyval == 113:
        Gtk.main_quit()

def on_decide_policy(view, decision, dtype):
    uri = decision.get_request().get_uri()
    if uri.startswith("http") and not '127.0.0.1' in uri:
        decision.ignore()
        webbrowser.open_new(uri)
        return True
    return False

wnd = Gtk.Window()

wnd.set_icon_from_file(icon)
wnd.set_wmclass(title, title)
wnd.set_title(title)
wnd.set_default_size(1366, 768)

ctx = WebKit2.WebContext.get_default()
web = WebKit2.WebView.new_with_context(ctx)
wnd.connect("destroy", Gtk.main_quit)
wnd.connect('key_press_event', on_key_press_event)
wnd.add(web)
wnd.show_all()

web.connect("decide-policy", on_decide_policy)

url = 'file://' + base + '/openmedialibrary/static/html/load.html'
web.load_uri(url)

ctl = base + '/ctl'
p = subprocess.Popen([ctl, 'start'])
Gtk.main()
p = subprocess.Popen([ctl, 'stop'])
