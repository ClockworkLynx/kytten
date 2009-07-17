# kytten/checkbox.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong

import pyglet
from widgets import Control
from layout import HALIGN_LEFT, HALIGN_RIGHT
from override import KyttenLabel

class Checkbox(Control):
    """
    A two-state checkbox.
    """
    def __init__(self, text="", is_checked=False, id=None,
                 align=HALIGN_RIGHT, padding=4, on_click=None,
                 disabled=False):
        """
        Creates a new checkbox.  The provided text will be used to caption the
        checkbox.

        @param text Label for the checkbox
        @param is_checked True if we should start checked
        @param id ID for value
        @param align HALIGN_RIGHT if label should be right of checkbox,
                     HALIGN_LEFT if label should be left of checkbox
        @param padding Space between checkbox and label
        @param on_click Callback for the checkbox
        @param disabled True if the checkbox should be disabled
        """
        assert align in [HALIGN_LEFT, HALIGN_RIGHT]
        Control.__init__(self, id=id, disabled=disabled)
        self.text = text
        self.is_checked = is_checked
        self.align = align
        self.padding = padding
        self.on_click = on_click
        self.label = None
        self.checkbox = None
        self.highlight = None

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

    def on_gain_highlight(self):
        Control.on_gain_highlight(self)
        self.size(self.saved_dialog)
        self.highlight.update(self.x, self.y, self.width, self.height)

    def on_lose_highlight(self):
        Control.on_lose_highlight(self)
        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

    def on_mouse_press(self, x, y, button, modifiers):
        if not self.is_disabled():
            self.is_checked = not self.is_checked
            if self.on_click is not None:
                if self.id is not None:
                    self.on_click(self.id, self.is_checked)
                else:
                    self.on_click(self.is_checked)

            # Delete the button to force it to be redrawn
            self.delete()
            self.saved_dialog.set_needs_layout()

    def size(self, dialog):
        """
        Sizes the Checkbox.  If necessary, creates the graphic elements.

        @param dialog Dialog which contains the Checkbox
        """
        if dialog is None:
            return
        Control.size(self, dialog)
        if self.is_checked:
            path = ['checkbox', 'checked']
        else:
            path = ['checkbox', 'unchecked']
        if self.is_disabled():
            color = dialog.theme[path]['disabled_color']
        else:
            color = dialog.theme[path]['gui_color']
        if self.checkbox is None:
            self.checkbox = dialog.theme[path]['image'].generate(
                color,
                dialog.batch, dialog.bg_group)
        if self.highlight is None and self.is_highlight():
            self.highlight = dialog.theme[path]['highlight']['image'].generate(
                    dialog.theme[path]['highlight_color'],
                    dialog.batch,
                    dialog.bg_group)
        if self.label is None:
            self.label = KyttenLabel(self.text,
                font_name=dialog.theme[path]['font'],
                font_size=dialog.theme[path]['font_size'],
                color=color,
                batch=dialog.batch, group=dialog.fg_group)

        # Treat the height of the label as ascent + descent
        font = self.label.document.get_font()
        height = font.ascent - font.descent  # descent is negative
        self.width = self.checkbox.width + self.padding + \
            self.label.content_width
        self.height = max(self.checkbox.height, height)

    def teardown(self):
        self.on_click = None
        Control.teardown(self)