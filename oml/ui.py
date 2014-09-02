# encoding: utf-8
# vi:si:et:sw=4:sts=4:ts=4
DEBUG=False
try:
    from gi.repository import Gtk, GObject
    GObject.threads_init()
    use_Gtk = True
except:
    from tkinter import Tk
    import tkinter.filedialog
    use_Gtk = False

class GtkUI:
    def selectFolder(self, data):
        dialog = Gtk.FileChooserDialog(data.get("title", "Select Folder"),
                               None,
                               Gtk.FileChooserAction.SELECT_FOLDER,
                               (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_default_response(Gtk.ResponseType.OK)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            if DEBUG:
                print(filename, 'selected')
        elif response == Gtk.ResponseType.CANCEL:
            if DEBUG:
                print('Closed, no files selected')
            filename = None
        dialog.destroy()
        while Gtk.events_pending():
                Gtk.main_iteration()
        if DEBUG:
            print("done")
        return filename

    def selectFile(self, data):
        dialog = Gtk.FileChooserDialog(data.get("title", "Select File"),
                               None,
                               Gtk.FileChooserAction.OPEN,
                               (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_default_response(Gtk.ResponseType.OK)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            if DEBUG:
                print(filename, 'selected')
        elif response == Gtk.ResponseType.CANCEL:
            if DEBUG:
                print('Closed, no files selected')
            filename = None
        dialog.destroy()
        while Gtk.events_pending():
                Gtk.main_iteration()
        if DEBUG:
            print("done")
        return filename

class TkUI:
    def __init__(self):
        self.root = Tk()
        self.root.withdraw() #hiding tkinter window
    def selectFolder(self, data):
        return tkinter.filedialog.askdirectory(title=data.get("title", "Select Folder"))

    def selectFile(self, data):
        return tkinter.filedialog.askopenfilename(title=data.get("title", "Select File"))

if use_Gtk:
    ui = GtkUI()
else:
    ui = TkUI()

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2 and sys.argv[1] == 'folder':
        print(ui.selectFolder({}))
    else:
        print(ui.selectFile({}))
