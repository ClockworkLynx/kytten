# kytten/checkbox.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet
from widgets import Control
from layout import HALIGN_LEFT, HALIGN_RIGHT

class Checkbox(Control):
    """
    A two-state checkbox.
    """
    def __init__(self, text="", id=None, on_click=None, padding=4,
                 align=HALIGN_RIGHT):
        """
        Creates a new checkbox.  The provided text will be used to caption the
        checkbox.

        @param text Label for the checkbox
        @param on_click Callback for the checkbox
        @param padding Space between checkbox and label
        @param align HALIGN_RIGHT if label should be right of checkbox,
                     HALIGN_LEFT if label should be left of checkbox
        """
        assert align in [HALIGN_LEFT, HALIGN_RIGHT]
        Control.__init__(self, id=id)
        self.text = text
        self.on_click = on_click
        self.padding = padding
        self.align = align
        self.label = None
        self.checkbox = None
        self.highlight = None
        self.is_checked = False

    def delete(self):
        """
        Clean up our graphic elements
        """
        Control.delete(self)
        if self.checkbox is not None:
            self.checkbox.delete()
            self.checkbox = None
        if self.label is not None:
            self.label.delete()
            self.label = None
        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

    def get_value(self):
        return self.is_checked

    def is_input(self):
        return True

    def layout(self, x, y):
        """
        Places the Checkbox.

        @param x X coordinate of lower left corner
        @param y Y coordinate of lower left corner
        """
        Control.layout(self, x, y)
        if self.align == HALIGN_RIGHT:  # label goes on right
            self.checkbox.update(x, y + self.height/2 - self.checkbox.height/2,
                                 self.checkbox.width, self.checkbox.height)
            self.label.x = x + self.checkbox.width + self.padding
        else: # label goes on left
            self.label.x = x
            self.checkbox.update(x + self.label.content_width + self.padding,
                                 y + self.height/2 - self.checkbox.height/2,
                                 self.checkbox.width, self.checkbox.height)

        if self.highlight is not None:
            self.highlight.update(self.x, self.y, self.width, self.height)

        font = self.label.document.get_font()
        height = font.ascent - font.descent
        self.label.y = y + self.height/2 - height/2 - font.descent

    def on_gain_highlight(self, dialog):
        Control.on_gain_highlight(self, dialog)
        self.size(dialog)
        self.highlight.update(self.x, self.y, self.width, self.height)

    def on_lose_highlight(self, dialog):
        Control.on_lose_highlight(self, dialog)
        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

    def on_mouse_press(self, dialog, x, y, button, modifiers):
        self.is_checked = not self.is_checked
        if self.on_click is not None:
            if self.id is not None:
                self.on_click(self.id, self.is_checked)
            else:
                self.on_click(self.is_checked)

        # Delete the button to force it to be redrawn
        self.delete()
        dialog.set_needs_layout()

    def size(self, dialog):
        """
        Sizes the Checkbox.  If necessary, creates the graphic elements.

        @param dialog Dialog which contains the Checkbox
        """
        if self.checkbox is None:
            if self.is_checked:
                self.checkbox = dialog.theme['checkbox']['image-checked']\
                    .generate(dialog.theme['checkbox']['gui_color'],
                              dialog.batch, dialog.bg_group)
            else:
                self.checkbox = dialog.theme['checkbox']['image'].generate(
                    dialog.theme['checkbox']['gui_color'],
                    dialog.batch, dialog.bg_group)
        if self.highlight is None and self.is_highlight:
            self.highlight = dialog.theme['checkbox']['image-highlight']\
                .generate(dialog.theme['checkbox']['highlight_color'],
                         dialog.batch,
                         dialog.bg_group)
        if self.label is None:
            self.label = pyglet.text.Label(self.text,
                font_name=dialog.theme['checkbox']['font'],
                font_size=dialog.theme['checkbox']['font_size'],
                color=dialog.theme['checkbox']['gui_color'],
                batch=dialog.batch, group=dialog.fg_group)

        # Treat the height of the label as ascent + descent
        font = self.label.document.get_font()
        height = font.ascent - font.descent # descent is negative
        self.width = self.checkbox.width + self.padding + \
            self.label.content_width
        self.height = max(self.checkbox.height, height)

