# kytten/document.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet

from widgets import Control
from scrollbar import VScrollbar

class Document(Control):
    """
    Allows you to embed a document within the GUI, which includes a
    vertical scrollbar as needed.
    """
    def __init__(self, document, width=1000, height=5000,
                 is_fixed_size=False, always_show_scrollbar=False):
        """
        Creates a new Document.
        """
        Control.__init__(self, width, height)
        self.max_height = height
        self.content_width = width
        if isinstance(document, basestring):
            self.document = pyglet.text.document.UnformattedDocument(document)
        else:
            self.document = document
        self.content = None
        self.content_width = width
        self.scrollbar = None
        self.set_document_style = False
        self.is_fixed_size = is_fixed_size
        self.always_show_scrollbar = always_show_scrollbar
        self.needs_layout = False

    def _do_set_document_style(self, attr, value):
        length = len(self.document.text)
        runs = [(start, end, doc_value) for start, end, doc_value in
                self.document.get_style_runs(attr).ranges(0, length)
                if doc_value is not None]
        if not runs:
            terminator = len(self.document.text)
        else:
            terminator = runs[0][0]
        self.document.set_style(0, terminator, {attr: value})

    def _get_controls(self):
        controls = []
        if self.scrollbar:
            controls += self.scrollbar._get_controls()
        controls += Control._get_controls(self)
        return controls

    def delete(self):
        if self.content is not None:
            self.content.delete()
            self.content = None
        if self.scrollbar is not None:
            self.scrollbar.delete()
            self.scrollbar = None

    def do_set_document_style(self, dialog):
        self.set_document_style = True

        # Check the style runs to make sure we don't stamp on anything
        # set by the user
        self._do_set_document_style('color', dialog.theme['text_color'])
        self._do_set_document_style('font_name', dialog.theme['font'])
        self._do_set_document_style('font_size', dialog.theme['font_size'])

    def get_text(self):
        return self.document.text

    def layout(self, x, y):
        self.x, self.y = x, y
        self.content.begin_update()
        self.content.x = x
        self.content.y = y
        self.content.end_update()
        if self.scrollbar is not None:
            self.scrollbar.layout(x + self.content_width, y)

    def on_update(self, dt):
        """
        On updates, we update the scrollbar and then set our view offset
        if it has changed.

        @param dt Time passed since last update event (in seconds)
        """
        if self.scrollbar is not None:
            self.scrollbar.dispatch_event('on_update', dt)
            pos = self.scrollbar.get(self.max_height,
                                     self.content.content_height)
            if pos != -self.content.view_y:
                self.content.view_y = -pos

        if self.needs_layout:
            self.needs_layout = False
            self.saved_dialog.set_needs_layout()

    def size(self, dialog):
        if dialog is None:
            return

        Control.size(self, dialog)
        if not self.set_document_style:
            self.do_set_document_style(dialog)
        if self.content is None:
            self.content = pyglet.text.layout.IncrementalTextLayout(
                self.document,
                self.content_width,
                self.max_height,
                multiline=True, batch=dialog.batch, group=dialog.fg_group)
            if self.is_fixed_size or (self.max_height and
                self.content.content_height > self.max_height):
                self.height = self.max_height
            else:
                self.height = self.content.content_height
            self.content.height = self.height
        if self.always_show_scrollbar or \
           (self.max_height and self.content.content_height > self.max_height):
            if self.scrollbar is None:
                self.scrollbar = VScrollbar(self.max_height)
            self.scrollbar.size(dialog)
            self.scrollbar.set(self.max_height, self.content.content_height)
        if self.scrollbar is not None:
            self.width = self.content_width + self.scrollbar.width
        else:
            self.width = self.content_width

    def set_text(self, text):
        self.document.text = text
        self.needs_layout = True