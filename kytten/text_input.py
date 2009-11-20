# kytten/input.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet
from widgets import Control
from override import KyttenInputLabel

class Input(Control):
    """A text input field."""
    def __init__(self, id=None, text="", length=20, max_length=None, padding=0,
                 on_input=None, disabled=False):
        Control.__init__(self, id=id, disabled=disabled)
        self.text = text
        self.length = length
        self.max_length = max_length
        self.padding = padding
        self.on_input = on_input
        self.document = pyglet.text.document.UnformattedDocument(text)
        self.document_style_set = False
        self.text_layout = None
        self.label = None
        self.caret = None
        self.field = None
        self.highlight = None

    def delete(self):
        Control.delete(self)
        if self.caret is not None:
            self.caret.delete()
            self.caret = None
        if self.text_layout is not None:
            self.document.remove_handlers(self.text_layout)
            self.text_layout.delete()
            self.text_layout = None
        if self.label is not None:
            self.label.delete()
            self.label = None
        if self.field is not None:
            self.field.delete()
            self.field = None
        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

    def disable(self):
        Control.disable(self)
        self.document_style_set = False

    def enable(self):
        Control.enable(self)
        self.document_style_set = False

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

        x, y, width, height = self.field.get_content_region()
        if self.is_focus():
            self.text_layout.begin_update()
            self.text_layout.x = x + self.padding
            self.text_layout.y = y + self.padding
            self.text_layout.end_update()
        else:
            # Adjust the text for font's descent
            descent = self.document.get_font().descent
            self.label.begin_update()
            self.label.x = x + self.padding
            self.label.y = y + self.padding - descent
            self.label.width = width - self.padding * 2
            self.label.end_update()

    def on_gain_highlight(self):
        Control.on_gain_highlight(self)
        self.set_highlight()

    def on_gain_focus(self):
        Control.on_gain_focus(self)
        self.delete()
        if self.saved_dialog is not None:
            self.size(self.saved_dialog)
            self.layout(self.x, self.y)

    def on_key_press(self, symbol, modifiers):
        return pyglet.event.EVENT_HANDLED

    def on_lose_focus(self):
        Control.on_lose_focus(self)
        self.delete()
        if self.saved_dialog is not None:
            self.size(self.saved_dialog)
            self.layout(self.x, self.y)
        if self.on_input is not None:
            if self.id is not None:
                self.on_input(self.id, self.get_text())
            else:
                self.on_input(self.get_text())

    def on_lose_highlight(self):
        Control.on_lose_highlight(self)
        self.remove_highlight()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if not self.is_disabled() and self.caret:
            return self.caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        if not self.is_disabled():
            return self.caret.on_mouse_press(x, y, button, modifiers)

    def on_text(self, text):
        if not self.is_disabled() and self.caret:
            self.caret.on_text(text)
            if self.max_length and len(self.document.text) > self.max_length:
                self.document.text = self.document.text[:self.max_length]
                self.caret.mark = self.caret.position = self.max_length
            return pyglet.event.EVENT_HANDLED

    def on_text_motion(self, motion):
        if not self.is_disabled() and self.caret:
            return self.caret.on_text_motion(motion)

    def on_text_motion_select(self, motion):
        if not self.is_disabled() and self.caret:
            return self.caret.on_text_motion_select(motion)

    def remove_highlight(self):
        if not self.is_highlight() and not self.is_focus():
            if self.highlight is not None:
                self.highlight.delete()
                self.highlight = None

    def set_highlight(self):
        path = ['input', 'highlight']
        if self.highlight is None:
            self.highlight = self.saved_dialog.theme[path]['image'].generate(
                color=self.saved_dialog.theme[path]['highlight_color'],
                batch=self.saved_dialog.batch,
                group=self.saved_dialog.highlight_group)
            self.highlight.update(self.x, self.y, self.width, self.height)

    def set_text(self, text):
        self.document.text = text
        if self.caret:
            self.caret.mark = self.caret.position = len(self.document.text)
        elif self.label:
            self.label.text = text

    def size(self, dialog):
        if dialog is None:
            return
        Control.size(self, dialog)

        if self.is_disabled():
            color = dialog.theme['input']['disabled_color']
        else:
            color = dialog.theme['input']['text_color']

        # We set the style once.  We shouldn't have to do so again because
        # it's an UnformattedDocument.
        if not self.document_style_set:
            self.document.set_style(0, len(self.document.text),
                                    dict(color=color,
                                         font_name=dialog.theme['font'],
                                         font_size=dialog.theme['font_size']))
            self.document_style_set = True

        # Calculate the needed size based on the font size
        font = self.document.get_font(0)
        height = font.ascent - font.descent
        glyphs = font.get_glyphs('A_')
        width = max([x.width for x in glyphs])
        needed_width = self.length * width + 2 * self.padding
        needed_height = height + 2 * self.padding

        if self.is_focus():
            if self.text_layout is None:
                self.text_layout = pyglet.text.layout.IncrementalTextLayout(
                    self.document, needed_width, needed_height,
                    multiline=False,
                    batch=dialog.batch, group=dialog.fg_group)
                assert self.caret is None
            assert self.label is None
            if self.caret is None:
                self.caret = pyglet.text.caret.Caret(
                    self.text_layout,
                    color=dialog.theme['input']['gui_color'][0:3])
                self.caret.visible = True
                self.caret.mark = 0
                self.caret.position = len(self.document.text)
        else:
            if self.label is None:
                self.label = KyttenInputLabel(self.document.text,
                                              multiline=False,
                                              width=self.width-self.padding*2,
                                              color=color,
                                              batch=dialog.batch,
                                              group=dialog.fg_group)
            assert self.text_layout is None and self.caret is None
        if self.field is None:
            if self.is_disabled():
                color = dialog.theme['input']['disabled_color']
            else:
                color = dialog.theme['input']['gui_color']
            self.field = dialog.theme['input']['image'].generate(
                color=color,
                batch=dialog.batch,
                group=dialog.bg_group)
        if self.highlight is None and self.is_highlight():
            self.set_highlight()

        self.width, self.height = self.field.get_needed_size(
            needed_width, needed_height)

    def teardown(self):
        self.on_input = False
        Control.teardown(self)