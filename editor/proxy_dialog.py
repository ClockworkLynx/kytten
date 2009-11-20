# proxy_dialog.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet
import kytten

class ProxyDialog(kytten.Wrapper):
    """
    Allows us to insert the theme being worked on into our own dialog.
    """
    def __init__(self, content, theme):
	kytten.Wrapper.__init__(self, content)
	self.content = content
	self.theme = theme
	self.batch = None
        self.root_group = None
        self.panel_group = None
        self.bg_group = None
        self.fg_group = None
        self.highlight_group = None

    def delete(self):
	kytten.Wrapper.delete(self)
	self.root_group = None
        self.panel_group = None
        self.bg_group = None
        self.fg_group = None
        self.highlight_group = None

    def get_root(self):
        if self.saved_dialog:
            return self.saved_dialog.get_root()
        else:
            return self

    def set_needs_layout(self):
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def size(self, dialog):
        if dialog is None:
            return
        kytten.Widget.size(self, dialog)
        if self.root_group is None: # do we need to re-clone dialog groups?
            self.batch = dialog.batch
            self.root_group = dialog.fg_group
            self.panel_group = pyglet.graphics.OrderedGroup(
                0, self.root_group)
            self.bg_group = pyglet.graphics.OrderedGroup(
                1, self.root_group)
            self.fg_group = pyglet.graphics.OrderedGroup(
                2, self.root_group)
            self.highlight_group = pyglet.graphics.OrderedGroup(
                3, self.root_group)
            kytten.Wrapper.delete(self)  # rebuild children
        kytten.Wrapper.size(self, self)  # all children are to use our groups
