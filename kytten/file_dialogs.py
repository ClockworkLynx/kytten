# kytten/file_dialogs.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import glob
import os
import pyglet
from pyglet import gl

from dialog import Dialog
from frame import Frame, SectionHeader
from layout import VerticalLayout
from layout import ANCHOR_CENTER, HALIGN_LEFT
from menu import Menu
from scrollable import Scrollable

class FileLoadDialog(Dialog):
    def __init__(self, path=os.getcwd(), extensions=[], title="Select File",
                 width=600, height=300, window=None, batch=None, group=None,
                 anchor=ANCHOR_CENTER, offset=(0, 0),
                 theme=None, movable=True, on_select=None, on_escape=None):
        self.path = path
        self.extensions = extensions
        self.on_select = on_select
        self.saved_dialog = None
        self.selected_file = None
        self._set_files()

        def on_menu_select(choice):
            self._select_file(self.files_dict[choice])
        self.menu = Menu(options=self.files, on_select=on_menu_select)

        content = Frame(
            Scrollable(
                VerticalLayout([
                    SectionHeader(title),
                    self.menu,
                ], align=HALIGN_LEFT),
                width=width, height=height))
        Dialog.__init__(self, content, window=window, batch=batch, group=group,
                        anchor=anchor, offset=offset, theme=theme,
                        movable=movable, on_escape=on_escape)

    def _select_file(self, filename):
        if os.path.isdir(filename):
            self.path = filename
            self._set_files()
            self.menu.set_options(self.saved_dialog, self.files)
        else:
            self.selected_file = filename
            if self.on_select is not None:
                self.on_select(filename)

    def _set_files(self):
        # Once we have a new path, update our files
        filenames = glob.glob(os.path.join(self.path, '*'))

        # First, a list of directories
        if os.path.split(self.path)[1]:  # do we have a parent dir?
            files = [('(parent dir)', os.path.split(self.path)[0])]
        else:  # Otherwise, don't show a parent dir
            files = []
        files += [("%s (dir)" % os.path.basename(x), x) for x in filenames
                  if os.path.isdir(x)]

        # Now add the files that match the extensions
        if self.extensions:
            for filename in filenames:
                if os.path.isfile(filename):
                    ext = os.path.splitext(filename)[1]
                    if ext in self.extensions:
                        files.append((os.path.basename(filename), filename))
        else:
            files.extend([(os.path.basename(x), x) for x in filenames
                          if os.path.isfile(x)])

        self.selected_file = None
        self.files_dict = dict(files)
        self.files = self.files_dict.keys()

        def dir_sort(x, y):
            if x == '(parent dir)':
                return -1
            elif x.endswith(' (dir)') and y.endswith(' (dir)'):
                return cmp(x, y)
            elif x.endswith(' (dir)') and y != '(parent dir)':
                return -1
            elif y.endswith(' (dir)'):
                return 1
            else:
                return cmp(x, y)
        self.files.sort(dir_sort)

    def get(self):
        return self.selected_file

    def size(self, dialog):
        self.saved_dialog = dialog
        Dialog.size(self, dialog)