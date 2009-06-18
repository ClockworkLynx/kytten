# kytten/input.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet
from widgets import Control

class Input(Control):
    """A text input field."""
    def __init__(self, id=None, text="", length=20, padding=0,
                 on_input=None):
        Control.__init__(self, id=id)
        self.text = text
        self.length = length
        self.padding = padding
        self.on_input = on_input
        self.document = pyglet.text.document.UnformattedDocument(text)
        self.text_layout = None
        self.caret = None
        self.field = None
        self.highlight = None

    def delete(self):
        Control.delete(self)
        if self.text_layout is not None:
            self.text_layout.delete()
            self.text_layout = None
        if self.caret is not None:
            self.caret.delete()
            self.caret = None
        if self.field is not None:
            self.field.delete()
            self.field = None
        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

    def get_text(self):
        return self.document.text

    def get_value(self):
        return self.get_text()

    def is_focusable(self):
        return True

    def is_input(self):
        return True

    def layout(self, x, y):
        self.x, self.y = x, y
        self.field.update(x, y, self.width, self.height)
        if self.highlight is not None:
            self.highlight.update(x, y, self.width, self.height)

        # Adjust the text for font's descent
        x, y, width, height = self.field.get_content_region()
        self.text_layout.x = x + self.padding
        self.text_layout.y = y + self.padding

    def on_gain_highlight(self):
        Control.on_gain_highlight(self)
        self.set_highlight()

    def on_gain_focus(self):
        Control.on_gain_focus(self)
        self.set_highlight()
        if self.caret is not None:
            self.caret.visible = True
            self.caret.mark = 0
            self.caret.position = len(self.document.text)

    def on_lose_focus(self):
        Control.on_lose_focus(self)
        self.remove_highlight()
        if self.caret is not None:
            self.caret.visible = False
            self.caret.mark = self.caret.position = 0
        if self.on_input is not None:
            if self.id is not None:
                self.on_input(self.id, self.get_text())
            else:
                self.on_input(self.get_text())

    def on_lose_highlight(self):
        Control.on_lose_highlight(self)
        self.remove_highlight()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        return self.caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        return self.caret.on_mouse_press(x, y, button, modifiers)

    def on_text(self, text):
        self.caret.on_text(text)

    def on_text_motion(self, motion):
        return self.caret.on_text_motion(motion)

    def on_text_motion_select(self, motion):
        return self.caret.on_text_motion_select(motion)

    def set_text(self, text):
        self.document.text = text
        self.caret.mark = self.caret.position = len(self.document.text)

    def remove_highlight(self):
        if not self.is_highlight and not self.is_focus:
            if self.highlight is not None:
                self.highlight.delete()
                self.highlight = None

    def set_highlight(self):
        if self.highlight is None:
            self.highlight = self.saved_dialog.theme['input']\
                ['image-highlight'].generate(
                    color=self.saved_dialog.theme['highlight_color'],
                    batch=self.saved_dialog.batch,
                    group=self.saved_dialog.highlight_group)
            self.highlight.update(self.x, self.y, self.width, self.height)

    def size(self, dialog):
        if dialog is None:
            return
        Control.size(self, dialog)
        self.document.set_style(0, len(self.document.text),
                    dict(color=dialog.theme['text_color'],
                         font_name=dialog.theme['font'],
                         font_size=dialog.theme['font_size']))

        # Calculate the needed size based on the font size
        font = self.document.get_font(0)
        height = font.ascent - font.descent
        glyphs = font.get_glyphs('A_')
        width = max([x.width for x in glyphs])
        needed_width = self.length * width + 2 * self.padding
        needed_height = height + 2 * self.padding

        if self.text_layout is None:
            self.text_layout = pyglet.text.layout.IncrementalTextLayout(
                self.document, needed_width, needed_height,
                multiline=False,
                batch=dialog.batch, group=dialog.fg_group)
        if self.caret is None:
            self.caret = pyglet.text.caret.Caret(
                self.text_layout, color=dialog.theme['gui_color'][0:3])
            self.caret.visible = False
        if self.field is None:
            self.field = dialog.theme['input']['image'].generate(
                color=dialog.theme['gui_color'],
                batch=dialog.batch,
                group=dialog.bg_group)
        if self.highlight is None and self.is_highlight:
            self.set_highlight()

        self.width, self.height = self.field.get_needed_size(
            needed_width, needed_height)

    def teardown(self):
        self.on_input = False
        Control.teardown(self)